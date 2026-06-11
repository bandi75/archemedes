from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Protocol

from pydantic import Field

from archimedes.agents.pattern_detector import PatternDetector
from archimedes.agents.evidence_auditor import EvidenceAuditor
from archimedes.models.base import ArchimedesModel, new_id
from archimedes.models.change import ChangeEvent
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import (
    ChangeType,
    ClaimType,
    EvidenceRetrievalMethod,
    QualityGateStatus,
    SourceFreshness,
    StageName,
    TrustLevel,
)
from archimedes.models.evidence import EvidenceSource
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.session import ArchitectureSession
from archimedes.orchestrator.dependency_engine import (
    compute_change_impact,
    detect_requirement_changes,
)
from archimedes.state.state_manager import ArchitectureStateManager


PIPELINE_ORDER: list[StageName] = [
    StageName.INTAKE,
    StageName.REQUIREMENTS_EXTRACTION,
    StageName.PATTERN_DETECTION,
    StageName.OPTIONS_GENERATION,
    StageName.SOCRATIC_REVIEW,
    StageName.EVIDENCE_AUDIT_CHECKPOINT,
    StageName.ADR_GENERATION,
    StageName.HLD_GENERATION,
    StageName.MINI_WAF_REVIEW,
    StageName.FINAL_EVIDENCE_AUDIT,
]


class SupportsControllerStorage(Protocol):
    def read_session(self, session_id: str) -> ArchitectureSession | None: ...

    def upsert_session(self, session: ArchitectureSession) -> ArchitectureSession: ...

    def append_change_event(self, event: ChangeEvent) -> ChangeEvent: ...


class OrchestratorResponse(ArchimedesModel):
    current_stage: StageName
    stage_status: str
    artifacts_produced: list[str]
    quality_gate_result: QualityGateResult | None = None
    next_prompt_for_user: str | None = None
    requires_user_action: bool
    change_detected: bool = False
    impacted_stages: list[StageName] = Field(default_factory=list)
    stable_stages: list[StageName] = Field(default_factory=list)


@dataclass(slots=True)
class StageController:
    state_manager: ArchitectureStateManager
    storage: SupportsControllerStorage
    pattern_detector: PatternDetector = field(default_factory=PatternDetector)
    evidence_auditor: EvidenceAuditor = field(default_factory=EvidenceAuditor)

    def process_message(
        self,
        session_id: str,
        user_message: str,
        *,
        idempotency_key: str | None = None,
    ) -> OrchestratorResponse:
        session = self.storage.read_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        changes = detect_requirement_changes(user_message)
        if changes:
            event = ChangeEvent(
                session_id=session_id,
                change_type=ChangeType.REQUIREMENT_MODIFIED,
                changed_field=",".join(change.changed_field for change in changes),
                old_value_summary="existing value",
                new_value_summary="; ".join(change.new_value for change in changes),
                user_message=user_message,
            )
            impact = compute_change_impact(
                changes,
                session.dependency_map,
                session_id=session_id,
                change_event_id=event.change_event_id,
            )
            event.impacted_stages = impact.impacted_stages
            event.stable_stages = impact.stable_stages
            self.storage.append_change_event(event)

            artifacts_produced = self.rerun_impacted_stages(
                session_id=session_id,
                user_message=user_message,
                impacted_stages=event.impacted_stages,
                change_event_id=event.change_event_id,
            )
            refreshed = self.storage.read_session(session_id) or session
            return OrchestratorResponse(
                current_stage=refreshed.current_stage,
                stage_status="rereasoned",
                artifacts_produced=artifacts_produced,
                next_prompt_for_user=(
                    "Requirement change detected. Re-ran impacted stages: "
                    f"{', '.join(self._stage_value(stage) for stage in event.impacted_stages)}"
                ),
                requires_user_action=False,
                change_detected=True,
                impacted_stages=event.impacted_stages,
                stable_stages=event.stable_stages,
            )

        stage = self._resolve_active_stage(session)
        apply_result = self._execute_stage(
            session,
            stage,
            user_message,
            idempotency_key=idempotency_key,
        )

        if not apply_result.applied:
            return OrchestratorResponse(
                current_stage=stage,
                stage_status="failed",
                artifacts_produced=[],
                next_prompt_for_user=f"Stage failed: {apply_result.reason}",
                requires_user_action=True,
            )

        produced = [f"{self._stage_value(stage)}:v{apply_result.version}"]
        next_stage = self._next_stage(stage)
        audit_stage = self._audit_stage_after(stage)
        if audit_stage is not None:
            audit_result = self._run_evidence_audit(session, audit_stage)
            if audit_result.applied:
                produced.append(f"{self._stage_value(audit_stage)}:v{audit_result.version}")
                next_stage = self._next_stage(audit_stage)

        session.current_stage = next_stage or audit_stage or stage
        session.last_successful_stage = audit_stage or stage
        self.storage.upsert_session(session)

        gate = session.quality_gates.get(stage)
        return OrchestratorResponse(
            current_stage=stage,
            stage_status="completed",
            artifacts_produced=produced,
            quality_gate_result=gate,
            next_prompt_for_user=(
                "Pipeline complete."
                if next_stage is None
                else f"Proceeding to {self._stage_value(next_stage)} on next user message."
            ),
            requires_user_action=next_stage is None,
        )

    def rerun_impacted_stages(
        self,
        *,
        session_id: str,
        user_message: str,
        impacted_stages: list[StageName],
        change_event_id: str,
    ) -> list[str]:
        artifacts_produced: list[str] = []
        ordered_stages = [
            stage
            for stage in PIPELINE_ORDER
            if self._stage_value(stage)
            in {self._stage_value(impacted_stage) for impacted_stage in impacted_stages}
        ]

        for stage in ordered_stages:
            session = self.storage.read_session(session_id)
            if session is None:
                raise ValueError(f"Session not found: {session_id}")

            if stage in {
                StageName.EVIDENCE_AUDIT_CHECKPOINT,
                StageName.FINAL_EVIDENCE_AUDIT,
            }:
                result = self._run_evidence_audit(session, stage)
            else:
                result = self._execute_stage(
                    session,
                    stage,
                    self._rerun_message(user_message, stage, change_event_id),
                )

            if result.applied:
                artifacts_produced.append(f"{self._stage_value(stage)}:v{result.version}")
            else:
                artifacts_produced.append(f"{self._stage_value(stage)}:failed:{result.reason}")

        session = self.storage.read_session(session_id)
        if session is not None and ordered_stages:
            session.current_stage = ordered_stages[-1]
            session.last_successful_stage = ordered_stages[-1]
            self.storage.upsert_session(session)
        return artifacts_produced

    def _execute_stage(
        self,
        session: ArchitectureSession,
        stage: StageName,
        user_message: str,
        *,
        idempotency_key: str | None = None,
    ):
        base_version = session.latest_artifact_versions.get(stage, 0)
        if stage == StageName.PATTERN_DETECTION:
            patch = self.pattern_detector.detect(
                session_id=session.session_id,
                stage_run_id=new_id("stage_run"),
                base_version=base_version,
                requirements_text=user_message,
            )
        else:
            patch = self._generic_stage_patch(
                session=session,
                stage=stage,
                base_version=base_version,
                user_message=user_message,
            )
        if idempotency_key:
            patch.idempotency_key = idempotency_key
        return self.state_manager.apply_patch(patch)

    def _run_evidence_audit(self, session: ArchitectureSession, stage: StageName):
        base_version = session.latest_artifact_versions.get(stage, 0)
        report = self.evidence_auditor.run(
            session_id=session.session_id,
            storage=self.storage,
            stage=stage,
        )
        patch = self.evidence_auditor.build_stage_patch(
            report,
            stage_run_id=new_id("stage_run"),
            base_version=base_version,
        )
        return self.state_manager.apply_patch(patch)

    def _generic_stage_patch(
        self,
        *,
        session: ArchitectureSession,
        stage: StageName,
        base_version: int,
        user_message: str,
    ) -> StagePatch:
        payload = self._stage_payload(stage, user_message)
        patch_hash = self._compute_hash(payload)
        evidence = EvidenceSource(
            session_id=session.session_id,
            source="User-provided architecture context",
            retrieved_via=EvidenceRetrievalMethod.USER_INPUT,
            excerpt=user_message.strip(),
            source_freshness=SourceFreshness.CURRENT,
            trust_level=TrustLevel.MEDIUM,
            used_in_stages=[self._stage_value(stage)],
        )
        claim = ClaimRecord(
            session_id=session.session_id,
            claim=f"{stage} artifact generated from user context.",
            type=ClaimType.ASSUMPTION,
            confidence=0.65,
            stage=stage,
            evidence_ids=[evidence.evidence_id],
        )
        gate = QualityGateResult(status=QualityGateStatus.PASSED)
        idem = hashlib.sha256(
            f"{session.session_id}:{stage}:{base_version}:{patch_hash}".encode("utf-8")
        ).hexdigest()

        return StagePatch(
            session_id=session.session_id,
            stage=stage,
            stage_run_id=new_id("stage_run"),
            base_version=base_version,
            target_version=base_version + 1,
            idempotency_key=idem,
            patch_hash=patch_hash,
            patch=payload,
            claims=[claim],
            evidence_sources=[evidence],
            quality_gate_result=gate,
        )

    @staticmethod
    def _resolve_active_stage(session: ArchitectureSession) -> StageName:
        return session.current_stage or PIPELINE_ORDER[0]

    @staticmethod
    def _next_stage(stage: StageName) -> StageName | None:
        try:
            idx = PIPELINE_ORDER.index(stage)
        except ValueError:
            return None
        if idx == len(PIPELINE_ORDER) - 1:
            return None
        return PIPELINE_ORDER[idx + 1]

    @staticmethod
    def _audit_stage_after(stage: StageName) -> StageName | None:
        if stage == StageName.SOCRATIC_REVIEW:
            return StageName.EVIDENCE_AUDIT_CHECKPOINT
        if stage == StageName.MINI_WAF_REVIEW:
            return StageName.FINAL_EVIDENCE_AUDIT
        return None

    @staticmethod
    def _compute_hash(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _stage_payload(self, stage: StageName, user_message: str) -> dict:
        stage_value = self._stage_value(stage)
        text = user_message.strip()
        scale = self._scale_target(text)
        multi_region = self._is_multi_region(text)

        if stage == StageName.OPTIONS_GENERATION:
            options = [
                {
                    "option_id": "option_event_streaming",
                    "name": "Event Hubs streaming fraud pipeline",
                    "fit": "recommended",
                    "capacity_target": scale,
                    "topology": "multi-region active-active" if multi_region else "single-region resilient",
                    "core_services": (
                        ["Partitioned Event Hubs", "AKS", "Cosmos DB multi-region", "Front Door"]
                        if multi_region or scale == "100K TPS"
                        else ["Event Hubs", "Stream Analytics", "Azure Functions", "Cosmos DB"]
                    ),
                },
                {
                    "option_id": "option_serverless",
                    "name": "Serverless event scoring",
                    "fit": "conditional",
                    "capacity_target": scale,
                    "topology": "single-region",
                    "core_services": ["Event Hubs", "Azure Functions", "Cosmos DB"],
                },
                {
                    "option_id": "option_microservices",
                    "name": "AKS microservices scoring platform",
                    "fit": "strong at high scale" if scale == "100K TPS" else "higher operational overhead",
                    "capacity_target": scale,
                    "topology": "multi-region active-active" if multi_region else "regional",
                    "core_services": ["AKS", "Event Hubs", "Redis", "Cosmos DB"],
                },
            ]
            return {
                "summary": text,
                "stage": stage_value,
                "status": "generated",
                "options": options,
                "cost_estimate": {
                    "relative_monthly_cost": "high" if scale == "100K TPS" or multi_region else "medium",
                    "main_cost_drivers": ["stream partitions", "compute replicas", "multi-region data writes"],
                },
            }

        if stage == StageName.ADR_GENERATION:
            return {
                "summary": text,
                "stage": stage_value,
                "status": "generated",
                "title": "ADR: Real-time fraud detection architecture",
                "decision": (
                    "Adopt partitioned Event Hubs with active-active regional scoring."
                    if multi_region or scale == "100K TPS"
                    else "Adopt Event Hubs with stream processing and serverless scoring."
                ),
                "context": {
                    "scale_target": scale,
                    "resiliency": "multi-region active-active" if multi_region else "99.95% regional resilience",
                },
                "consequences": (
                    ["higher cost", "more operational complexity", "regional failover capability"]
                    if multi_region or scale == "100K TPS"
                    else ["lower complexity", "regional dependency", "simpler operations"]
                ),
            }

        if stage == StageName.HLD_GENERATION:
            components = [
                {"name": "Event Hubs", "role": "transaction ingestion", "scale_target": scale},
                {"name": "Scoring workers", "role": "real-time fraud inference"},
                {"name": "Cosmos DB", "role": "feature and decision store"},
            ]
            if multi_region or scale == "100K TPS":
                components.extend(
                    [
                        {"name": "Azure Front Door", "role": "global ingress and failover"},
                        {"name": "AKS", "role": "horizontally scaled scoring runtime"},
                        {"name": "Cosmos DB multi-region writes", "role": "active-active persistence"},
                    ]
                )
            return {
                "summary": text,
                "stage": stage_value,
                "status": "generated",
                "title": "Fraud Detection HLD",
                "components": components,
                "data_flows": [
                    {
                        "from": "payment gateway",
                        "to": "stream ingestion",
                        "latency_target": "sub-second",
                    },
                    {
                        "from": "scoring workers",
                        "to": "decision API",
                        "resiliency": "multi-region" if multi_region else "regional",
                    },
                ],
            }

        if stage == StageName.MINI_WAF_REVIEW:
            findings = [
                {
                    "pillar": "Reliability",
                    "severity": "warning" if multi_region or scale == "100K TPS" else "info",
                    "finding": (
                        "Active-active failover requires tested conflict handling."
                        if multi_region
                        else "Regional resiliency must be validated against 99.95% availability."
                    ),
                },
                {
                    "pillar": "Cost Optimization",
                    "severity": "warning" if scale == "100K TPS" else "info",
                    "finding": "High throughput increases partition and compute cost.",
                },
            ]
            return {
                "summary": text,
                "stage": stage_value,
                "status": "generated",
                "findings": findings,
            }

        return {
            "summary": text,
            "stage": stage_value,
            "status": "generated",
        }

    @staticmethod
    def _stage_value(stage: StageName | str) -> str:
        return stage.value if isinstance(stage, StageName) else str(stage)

    @staticmethod
    def _rerun_message(user_message: str, stage: StageName, change_event_id: str) -> str:
        return (
            f"{user_message.strip()} "
            f"[re-reasoning stage={stage.value} change_event_id={change_event_id}]"
        )

    @staticmethod
    def _scale_target(user_message: str) -> str:
        lowered = user_message.lower().replace(" ", "")
        if "100ktps" in lowered or "100,000tps" in lowered:
            return "100K TPS"
        if "10ktps" in lowered or "10,000tps" in lowered:
            return "10K TPS"
        return "current target"

    @staticmethod
    def _is_multi_region(user_message: str) -> bool:
        lowered = user_message.lower()
        return "multi-region" in lowered or "multi region" in lowered or "active-active" in lowered

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Protocol

from pydantic import Field

from archimedes.agents.factory import AgentFactory
from archimedes.agents.pattern_detector import PatternDetector
from archimedes.agents.evidence_auditor import EvidenceAuditor
from archimedes.models.base import ArchimedesModel, new_id
from archimedes.models.change import ChangeEvent
from archimedes.models.enums import (
    ChangeType,
    StageName,
)
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.socrates import SocratesReviewContext
from archimedes.models.session import ArchitectureSession
from archimedes.orchestrator.dependency_engine import (
    compute_change_impact,
    detect_requirement_changes,
)
from archimedes.socrates.workflow import SocratesWorkflow, build_socrates_workflow
from archimedes.state.state_manager import ArchitectureStateManager

logger = logging.getLogger(__name__)

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

# Stages handled by specialist LLM agents
STAGE_AGENT_MAP: dict[StageName, str] = {
    StageName.INTAKE: "IntakeAgent",
    StageName.REQUIREMENTS_EXTRACTION: "RequirementsEngineer",
    StageName.OPTIONS_GENERATION: "OptionsGenerator",
    StageName.ADR_GENERATION: "ADRWriter",
    StageName.HLD_GENERATION: "HLDDesigner",
    StageName.MINI_WAF_REVIEW: "WAFReviewer",
}


class SupportsControllerStorage(Protocol):
    def read_session(self, session_id: str) -> ArchitectureSession | None: ...

    def read_latest_artifact(self, session_id: str, stage: str): ...

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
    socrates_workflow: SocratesWorkflow = field(default_factory=build_socrates_workflow)
    agent_factory: AgentFactory = field(default_factory=AgentFactory.from_env)

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

        logger.info("[controller] process_message session=%s stage=%s", session_id, session.current_stage)

        changes = detect_requirement_changes(user_message)
        if changes:
            logger.info("[controller] requirement change detected fields=%s — re-running impacted stages",
                        [c.changed_field for c in changes])
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
        logger.info("[controller] active_stage=%s", stage)
        requested_stage = self._requested_stage(user_message)
        if requested_stage is not None and requested_stage != stage:
            logger.info("[controller] user requested stage=%s (current=%s)", requested_stage, stage)
            existing = self.storage.read_latest_artifact(
                session_id,
                self._stage_value(requested_stage),
            )
            if existing is not None:
                return OrchestratorResponse(
                    current_stage=requested_stage,
                    stage_status="already_completed",
                    artifacts_produced=[
                        f"{self._stage_value(requested_stage)}:v{existing.version}"
                    ],
                    quality_gate_result=existing.quality_gate,
                    next_prompt_for_user=(
                        f"{self._stage_value(requested_stage)} is already complete. "
                        f"Current pipeline stage remains {self._stage_value(stage)}."
                    ),
                    requires_user_action=False,
                )

        apply_result = self._execute_stage(
            session,
            stage,
            user_message,
            idempotency_key=idempotency_key,
        )

        if apply_result.applied:
            logger.info("[controller] stage=%s completed v%s", stage, apply_result.version)
        if not apply_result.applied:
            return OrchestratorResponse(
                current_stage=stage,
                stage_status="failed",
                artifacts_produced=[],
                next_prompt_for_user=f"Stage failed: {apply_result.reason}",
                requires_user_action=True,
            )

        produced = [f"{self._stage_value(stage)}:v{apply_result.version}"]
        session = self.storage.read_session(session_id) or session
        next_stage = self._next_stage(stage)
        audit_stage = self._audit_stage_after(stage)
        if audit_stage is not None:
            audit_result = self._run_evidence_audit(session, audit_stage)
            if audit_result.applied:
                produced.append(f"{self._stage_value(audit_stage)}:v{audit_result.version}")
                next_stage = self._next_stage(audit_stage)
                session = self.storage.read_session(session_id) or session

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
            logger.info("[controller] executing stage=%s via PatternDetector", stage)
            patch = self.pattern_detector.detect(
                session_id=session.session_id,
                stage_run_id=new_id("stage_run"),
                base_version=base_version,
                requirements_text=user_message,
            )
        elif stage == StageName.SOCRATIC_REVIEW:
            logger.info("[controller] executing stage=%s via SocratesWorkflow depth=%s", stage, self.socrates_workflow.depth)
            patch = self._socratic_stage_patch(
                session=session,
                base_version=base_version,
                user_message=user_message,
            )
        else:
            agent_name = STAGE_AGENT_MAP.get(stage)
            if agent_name is None:
                raise ValueError(f"No agent mapped for stage: {stage}")
            logger.info("[controller] executing stage=%s via agent=%s", stage, agent_name)
            patch = self.agent_factory.run_stage(
                agent_name,
                session_id=session.session_id,
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

    def _socratic_stage_patch(
        self,
        *,
        session: ArchitectureSession,
        base_version: int,
        user_message: str,
    ) -> StagePatch:
        context = SocratesReviewContext(
            session_id=session.session_id,
            stage_run_id=new_id("stage_run"),
            base_version=base_version,
            target_version=base_version + 1,
            business_need={
                "raw_input": session.business_need,
                "latest_user_message": user_message.strip(),
                "title": session.title,
            },
            requirements_summary=self._requirements_summary(session, user_message),
            architecture_options=self._architecture_options(session),
            evaluation_criteria=["reliability", "security", "cost", "delivery"],
        )
        review = self.socrates_workflow.run_sync(context)
        return self.socrates_workflow.build_stage_patch(review, base_version=base_version)

    def _requirements_summary(
        self,
        session: ArchitectureSession,
        user_message: str,
    ) -> dict:
        artifact = self.storage.read_latest_artifact(
            session.session_id,
            self._stage_value(StageName.REQUIREMENTS_EXTRACTION),
        )
        if artifact is not None and artifact.content:
            return artifact.content
        return {
            "summary": user_message.strip() or session.business_need,
            "source": "session_context",
        }

    def _architecture_options(self, session: ArchitectureSession) -> list[dict]:
        artifact = self.storage.read_latest_artifact(
            session.session_id,
            self._stage_value(StageName.OPTIONS_GENERATION),
        )
        if artifact is not None:
            options = artifact.content.get("options")
            if isinstance(options, list) and options:
                return options
        return []

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
    def _requested_stage(user_message: str) -> StageName | None:
        lowered = user_message.lower().replace("-", " ").replace("_", " ")
        stage_markers: list[tuple[StageName, tuple[str, ...]]] = [
            (StageName.SOCRATIC_REVIEW, ("socratic review", "socrates", "socratic")),
            (StageName.EVIDENCE_AUDIT_CHECKPOINT, ("evidence audit checkpoint", "evidence check")),
            (StageName.FINAL_EVIDENCE_AUDIT, ("final evidence audit", "final audit")),
            (StageName.REQUIREMENTS_EXTRACTION, ("requirements", "extract requirements")),
            (StageName.PATTERN_DETECTION, ("pattern detection", "detect pattern", "patterns")),
            (StageName.OPTIONS_GENERATION, ("options generation", "generate options", "options")),
            (StageName.ADR_GENERATION, ("adr generation", "generate adr", "adr")),
            (StageName.HLD_GENERATION, ("hld generation", "generate hld", "hld")),
            (StageName.MINI_WAF_REVIEW, ("mini waf", "waf review", "waf")),
        ]
        for stage, markers in stage_markers:
            if any(marker in lowered for marker in markers):
                return stage
        return None

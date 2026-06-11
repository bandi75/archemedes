from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Protocol

from pydantic import Field

from archimedes.agents.pattern_detector import PatternDetector
from archimedes.models.base import ArchimedesModel, new_id
from archimedes.models.change import ChangeEvent
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ChangeType, ClaimType, QualityGateStatus, StageName
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.session import ArchitectureSession
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

    def process_message(self, session_id: str, user_message: str) -> OrchestratorResponse:
        session = self.storage.read_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        change = self._classify_requirement_change(user_message)
        if change is not None:
            event = ChangeEvent(
                session_id=session_id,
                change_type=ChangeType.REQUIREMENT_MODIFIED,
                changed_field=change["field"],
                old_value_summary="existing value",
                new_value_summary=change["value"],
                impacted_stages=self._impacted_stages(session, change["category"]),
                stable_stages=self._stable_stages(session, change["category"]),
                user_message=user_message,
            )
            self.storage.append_change_event(event)

            return OrchestratorResponse(
                current_stage=session.current_stage,
                stage_status="change_detected",
                artifacts_produced=[],
                next_prompt_for_user=(
                    "Requirement change detected. Confirm re-run for impacted stages: "
                    f"{', '.join(self._stage_value(stage) for stage in event.impacted_stages)}"
                ),
                requires_user_action=True,
                change_detected=True,
                impacted_stages=event.impacted_stages,
                stable_stages=event.stable_stages,
            )

        stage = self._resolve_active_stage(session)
        apply_result = self._execute_stage(session, stage, user_message)

        if not apply_result.applied:
            return OrchestratorResponse(
                current_stage=stage,
                stage_status="failed",
                artifacts_produced=[],
                next_prompt_for_user=f"Stage failed: {apply_result.reason}",
                requires_user_action=True,
            )

        next_stage = self._next_stage(stage)
        session.current_stage = next_stage or stage
        session.last_successful_stage = stage
        self.storage.upsert_session(session)

        gate = session.quality_gates.get(stage)
        return OrchestratorResponse(
            current_stage=stage,
            stage_status="completed",
            artifacts_produced=[f"{self._stage_value(stage)}:v{apply_result.version}"],
            quality_gate_result=gate,
            next_prompt_for_user=(
                "Pipeline complete."
                if next_stage is None
                else f"Proceeding to {self._stage_value(next_stage)} on next user message."
            ),
            requires_user_action=next_stage is None,
        )

    def _execute_stage(self, session: ArchitectureSession, stage: StageName, user_message: str):
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
        return self.state_manager.apply_patch(patch)

    def _generic_stage_patch(
        self,
        *,
        session: ArchitectureSession,
        stage: StageName,
        base_version: int,
        user_message: str,
    ) -> StagePatch:
        payload = {
            "summary": user_message.strip(),
            "stage": self._stage_value(stage),
            "status": "generated",
        }
        patch_hash = self._compute_hash(payload)
        claim = ClaimRecord(
            session_id=session.session_id,
            claim=f"{stage} artifact generated from user context.",
            type=ClaimType.ASSUMPTION,
            confidence=0.65,
            stage=stage,
            evidence_ids=[],
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
            evidence_sources=[],
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
    def _compute_hash(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _stage_value(stage: StageName | str) -> str:
        return stage.value if isinstance(stage, StageName) else str(stage)

    @staticmethod
    def _classify_requirement_change(user_message: str) -> dict[str, str] | None:
        patterns = {
            "scale": re.compile(r"\b(\d+k\s*tps|throughput|scale|qps|rps)\b", re.IGNORECASE),
            "region": re.compile(r"\b(multi-region|active-active|geo|region)\b", re.IGNORECASE),
            "compliance": re.compile(r"\b(hipaa|pci|gdpr|compliance)\b", re.IGNORECASE),
            "budget": re.compile(r"\b(budget|cost|cheaper|price)\b", re.IGNORECASE),
            "availability": re.compile(r"\b(sla|uptime|availability|dr)\b", re.IGNORECASE),
        }
        trigger = re.compile(r"\b(change|make it|add|remove|instead of|actually)\b", re.IGNORECASE)
        if not trigger.search(user_message):
            return None

        for category, regex in patterns.items():
            if regex.search(user_message):
                return {
                    "category": category,
                    "field": category,
                    "value": user_message.strip(),
                }
        return None

    @staticmethod
    def _impacted_stages(session: ArchitectureSession, category: str) -> list[StageName]:
        return session.dependency_map.get(category, [])

    @staticmethod
    def _stable_stages(session: ArchitectureSession, category: str) -> list[StageName]:
        impacted = set(session.dependency_map.get(category, []))
        return [stage for stage in PIPELINE_ORDER if stage not in impacted]

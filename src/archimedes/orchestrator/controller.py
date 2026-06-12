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

# Primary input artifact each stage should receive as context.
_STAGE_CONTEXT_ARTIFACT: dict[StageName, StageName] = {
    StageName.REQUIREMENTS_EXTRACTION: StageName.INTAKE,
    StageName.PATTERN_DETECTION: StageName.REQUIREMENTS_EXTRACTION,
    StageName.OPTIONS_GENERATION: StageName.REQUIREMENTS_EXTRACTION,
    StageName.ADR_GENERATION: StageName.OPTIONS_GENERATION,
    StageName.HLD_GENERATION: StageName.ADR_GENERATION,
    StageName.MINI_WAF_REVIEW: StageName.HLD_GENERATION,
}

# Stages that run automatically (no user confirmation gate after completion).
# All other stages pause and ask the user to review before proceeding.
_NON_GATE_STAGES: frozenset[StageName] = frozenset({
    StageName.PATTERN_DETECTION,
    StageName.SOCRATIC_REVIEW,
    StageName.EVIDENCE_AUDIT_CHECKPOINT,
    StageName.FINAL_EVIDENCE_AUDIT,
})

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

        # --- Requirement change detection ---
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

            # Clear any active gate so re-run takes effect cleanly.
            session.awaiting_stage_confirmation = False
            session.pending_next_stage = None
            self.storage.upsert_session(session)

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
                    f"{', '.join(self._stage_value(s) for s in event.impacted_stages)}"
                ),
                requires_user_action=False,
                change_detected=True,
                impacted_stages=event.impacted_stages,
                stable_stages=event.stable_stages,
            )

        stage = self._resolve_active_stage(session)
        logger.info("[controller] active_stage=%s", stage)

        # --- Stage confirmation gate ---
        if session.awaiting_stage_confirmation and session.pending_next_stage is not None:
            pending = session.pending_next_stage

            if self._is_proceed_signal(user_message):
                logger.info("[controller] proceed confirmed — advancing to stage=%s", pending)
                session.awaiting_stage_confirmation = False
                session.pending_next_stage = None
                session.current_stage = pending
                self.storage.upsert_session(session)
                return self._run_from_stage(session_id, pending, user_message, idempotency_key)
            else:
                # User provided refinement context.
                # Pass the current artifact content so the agent sees its own prior output
                # (e.g. its clarifying questions) alongside the user's new answers.
                logger.info("[controller] refinement for stage=%s", stage)
                stage_key = self._stage_value(stage)
                current_artifact = self.storage.read_latest_artifact(session_id, stage_key)
                if current_artifact and current_artifact.content:
                    current_text = json.dumps(current_artifact.content, indent=2)
                    enriched = (
                        f"Refine the following {stage_key} artifact based on the user's additional input.\n\n"
                        f"Current artifact:\n{current_text}\n\n"
                        f"User input:\n{user_message}"
                    )
                else:
                    enriched = user_message

                apply_result = self._execute_stage(session, stage, enriched, idempotency_key=idempotency_key)
                if not apply_result.applied:
                    return OrchestratorResponse(
                        current_stage=stage,
                        stage_status="failed",
                        artifacts_produced=[],
                        next_prompt_for_user=f"Stage refinement failed: {apply_result.reason}",
                        requires_user_action=True,
                    )

                # Re-read session (state_manager wrote it) and restore gate.
                session = self.storage.read_session(session_id) or session
                session.awaiting_stage_confirmation = True
                session.pending_next_stage = pending
                self.storage.upsert_session(session)

                logger.info("[controller] stage=%s refined v%s", stage, apply_result.version)
                return OrchestratorResponse(
                    current_stage=stage,
                    stage_status="refined",
                    artifacts_produced=[f"{stage_key}:v{apply_result.version}"],
                    next_prompt_for_user=(
                        f"Stage '{stage_key}' updated. Review the artifact above, then reply "
                        f"'proceed' to continue to '{self._stage_value(pending)}', "
                        f"or provide more context to keep refining."
                    ),
                    requires_user_action=True,
                )

        # --- Pipeline already fully complete ---
        # current_stage is set to FINAL_EVIDENCE_AUDIT by _update_session_state after the last audit.
        # Any further message should return a completion notice rather than re-running stages.
        if stage == StageName.FINAL_EVIDENCE_AUDIT and self._next_stage(stage) is None:
            artifact = self.storage.read_latest_artifact(session_id, self._stage_value(stage))
            if artifact is not None:
                return OrchestratorResponse(
                    current_stage=stage,
                    stage_status="completed",
                    artifacts_produced=[f"{self._stage_value(stage)}:v{artifact.version}"],
                    quality_gate_result=artifact.quality_gate,
                    next_prompt_for_user=(
                        "The full pipeline is complete. All ten stages have been executed. "
                        "You can review any artifact above or start a new session."
                    ),
                    requires_user_action=False,
                )

        # --- Requested stage jump (existing behaviour) ---
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
                    artifacts_produced=[f"{self._stage_value(requested_stage)}:v{existing.version}"],
                    quality_gate_result=existing.quality_gate,
                    next_prompt_for_user=(
                        f"'{self._stage_value(requested_stage)}' is already complete. "
                        f"Current pipeline stage remains '{self._stage_value(stage)}'."
                    ),
                    requires_user_action=False,
                )

        # --- First run of the active stage ---
        return self._run_from_stage(session_id, stage, user_message, idempotency_key)

    def _run_from_stage(
        self,
        session_id: str,
        stage: StageName,
        user_message: str,
        idempotency_key: str | None,
    ) -> OrchestratorResponse:
        """Execute stage (and any subsequent auto stages) until reaching a gate stage."""
        produced: list[str] = []

        while True:
            session = self.storage.read_session(session_id)
            if session is None:
                raise ValueError(f"Session not found: {session_id}")

            logger.info("[controller] executing stage=%s", stage)
            msg = self._stage_user_message(session_id, stage, user_message)
            apply_result = self._execute_stage(session, stage, msg, idempotency_key=idempotency_key)
            idempotency_key = None  # only use on the first stage

            if not apply_result.applied:
                return OrchestratorResponse(
                    current_stage=stage,
                    stage_status="failed",
                    artifacts_produced=produced,
                    next_prompt_for_user=f"Stage '{self._stage_value(stage)}' failed: {apply_result.reason}",
                    requires_user_action=True,
                )

            logger.info("[controller] stage=%s completed v%s", stage, apply_result.version)
            produced.append(f"{self._stage_value(stage)}:v{apply_result.version}")

            # Run inline audit if applicable (SOCRATIC_REVIEW → EVIDENCE_AUDIT_CHECKPOINT, etc.)
            session = self.storage.read_session(session_id) or session
            audit_stage = self._audit_stage_after(stage)
            if audit_stage is not None:
                audit_result = self._run_evidence_audit(session, audit_stage)
                if audit_result.applied:
                    produced.append(f"{self._stage_value(audit_stage)}:v{audit_result.version}")
                effective_next = self._next_stage(audit_stage)
            else:
                effective_next = self._next_stage(stage)

            # Update conversation history for this stage.
            session = self.storage.read_session(session_id) or session
            stage_key = self._stage_value(stage)
            history = session.stage_conversation_history.get(stage_key, [])
            history.append({"user": user_message})
            session.stage_conversation_history[stage_key] = history

            if effective_next is None:
                # Pipeline complete — no gate needed.
                session.last_successful_stage = audit_stage or stage
                self.storage.upsert_session(session)
                gate = session.quality_gates.get(stage)
                return OrchestratorResponse(
                    current_stage=stage,
                    stage_status="completed",
                    artifacts_produced=produced,
                    quality_gate_result=gate,
                    next_prompt_for_user="Pipeline complete.",
                    requires_user_action=True,
                )

            if stage not in _NON_GATE_STAGES:
                # Gate stage: pause and ask user to confirm before proceeding.
                session.awaiting_stage_confirmation = True
                session.pending_next_stage = effective_next
                session.last_successful_stage = audit_stage or stage
                self.storage.upsert_session(session)
                gate = session.quality_gates.get(stage)
                return OrchestratorResponse(
                    current_stage=stage,
                    stage_status="completed",
                    artifacts_produced=produced,
                    quality_gate_result=gate,
                    next_prompt_for_user=(
                        f"Stage '{stage_key}' complete. Review the artifact above, then reply "
                        f"'proceed' to continue to '{self._stage_value(effective_next)}', "
                        f"or provide additional context to refine this stage."
                    ),
                    requires_user_action=True,
                )

            # Non-gate stage: loop and run the next stage automatically.
            session.last_successful_stage = audit_stage or stage
            self.storage.upsert_session(session)
            stage = effective_next
            user_message = "continue"

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
        elif stage in {StageName.EVIDENCE_AUDIT_CHECKPOINT, StageName.FINAL_EVIDENCE_AUDIT}:
            logger.info("[controller] executing stage=%s via EvidenceAuditor", stage)
            return self._run_evidence_audit(session, stage)
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
    def _is_proceed_signal(message: str) -> bool:
        normalized = message.strip().lower()
        exact = {"proceed", "yes", "ok", "next", "continue", "go ahead", "confirm",
                 "looks good", "approved", "done", "go", "lgtm", "approve"}
        if normalized in exact:
            return True
        # Short affirmations like "yes, proceed" or "ok looks good"
        if len(normalized) <= 40 and any(normalized.startswith(w) for w in ("yes", "proceed", "ok ", "looks good", "go ahead")):
            return True
        return False

    @staticmethod
    def _build_stage_context(history: list[dict], current_message: str) -> str:
        """Prepend prior turn Q&A so the agent has full within-stage context."""
        if not history:
            return current_message
        parts: list[str] = []
        for turn in history:
            parts.append(f"[User]: {turn['user']}")
            if turn.get("agent"):
                parts.append(f"[Agent]: {turn['agent']}")
        parts.append(f"[User follow-up]: {current_message}")
        return "\n\n".join(parts)

    def _stage_user_message(self, session_id: str, stage: StageName, user_message: str) -> str:
        """Build the context message for a stage by injecting the relevant prior artifact."""
        source_stage = _STAGE_CONTEXT_ARTIFACT.get(stage)
        if source_stage is None:
            return user_message

        artifact = self.storage.read_latest_artifact(session_id, self._stage_value(source_stage))
        if artifact is None or not artifact.content:
            return user_message

        artifact_text = json.dumps(artifact.content, indent=2)
        source_label = self._stage_value(source_stage)

        # When advancing via "proceed"/"continue", the artifact IS the primary input.
        if self._is_proceed_signal(user_message) or user_message == "continue":
            return f"Process the following {source_label} artifact:\n\n{artifact_text}"

        # User also provided additional context — include both.
        return f"{user_message}\n\nContext from {source_label}:\n\n{artifact_text}"

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

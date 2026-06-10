from __future__ import annotations

from datetime import datetime
from typing import TypeAlias

from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id, utc_now
from .enums import StageName, StageStatus
from .quality_gates import QualityGateResult


DependencyMap: TypeAlias = dict[str, list[StageName]]


DEPENDENCY_RULES: DependencyMap = {
    "business_need": [
        StageName.REQUIREMENTS_EXTRACTION,
        StageName.PATTERN_DETECTION,
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "functional_requirement": [
        StageName.REQUIREMENTS_EXTRACTION,
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "scale": [
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "latency": [
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "availability": [
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "compliance": [
        StageName.REQUIREMENTS_EXTRACTION,
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "region": [
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "budget": [
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
    "timeline": [
        StageName.SOCRATIC_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.ADR_GENERATION,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
}


class StageExecution(ArchimedesModel):
    stage: StageName
    stage_run_id: str = Field(default_factory=lambda: new_id("stage_run"))
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = Field(default=0, ge=0)
    failure_reason: str | None = None
    base_version: int | None = Field(default=None, ge=0)
    target_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_timestamps(self):
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot be earlier than started_at.")
        if self.status == StageStatus.FAILED and not self.failure_reason:
            raise ValueError("failure_reason is required when status='failed'.")
        return self


class ArchitectureSession(ArchimedesModel):
    session_id: str = Field(default_factory=lambda: new_id("session"))
    title: str | None = None
    business_need: str
    current_stage: StageName = StageName.INTAKE
    last_successful_stage: StageName | None = None
    active_version: int = Field(default=0, ge=0)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user_id: str | None = None
    project_id: str | None = None

    stage_executions: dict[StageName, StageExecution] = Field(default_factory=dict)
    dependency_map: DependencyMap = Field(default_factory=lambda: DEPENDENCY_RULES.copy())
    quality_gates: dict[StageName, QualityGateResult] = Field(default_factory=dict)
    detected_patterns: list[str] = Field(default_factory=list)

    latest_artifact_versions: dict[StageName, int] = Field(default_factory=dict)
    is_archived: bool = False

    @model_validator(mode="after")
    def ensure_current_stage_execution_exists(self):
        if self.current_stage not in self.stage_executions:
            self.stage_executions[self.current_stage] = StageExecution(stage=self.current_stage)
        return self

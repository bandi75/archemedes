from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id
from .claims import ClaimRecord
from .enums import QualityGateStatus, StageName
from .evidence import EvidenceSource
from .quality_gates import QualityGateResult


class StagePatch(ArchimedesModel):
    patch_id: str = Field(default_factory=lambda: new_id("patch"))
    session_id: str
    stage: StageName
    stage_run_id: str
    base_version: int = Field(ge=0)
    target_version: int = Field(ge=1)
    idempotency_key: str
    patch_hash: str

    patch: dict[str, Any]
    claims: list[ClaimRecord] = Field(default_factory=list)
    evidence_sources: list[EvidenceSource] = Field(default_factory=list)
    quality_gate_result: QualityGateResult
    requires_user_input: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_versions_and_gate(self):
        if self.target_version <= self.base_version:
            raise ValueError("target_version must be greater than base_version.")
        if self.quality_gate_result.status == QualityGateStatus.FAILED:
            if not self.quality_gate_result.blocking_failures:
                raise ValueError("failed quality gate must include blocking_failures.")
        return self


class ApplyPatchResult(ArchimedesModel):
    applied: bool
    session_id: str
    stage: StageName
    version: int | None = None
    reason: str | None = None
    current_version: int | None = None
    patch_base_version: int | None = None
    action: str | None = None
    evidence_count: int = 0

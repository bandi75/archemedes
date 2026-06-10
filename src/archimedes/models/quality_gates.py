from __future__ import annotations

from pydantic import Field, model_validator

from .base import ArchimedesModel
from .enums import QualityGateStatus


class QualityGateCheck(ArchimedesModel):
    check_id: str
    description: str
    passed: bool = False
    severity: str = "warning"  # blocking | warning
    message: str | None = None


class QualityGateResult(ArchimedesModel):
    status: QualityGateStatus
    blocking_failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: list[QualityGateCheck] = Field(default_factory=list)
    user_override_allowed: bool = True

    @model_validator(mode="after")
    def validate_status_consistency(self):
        if self.blocking_failures and self.status != QualityGateStatus.FAILED:
            raise ValueError("Quality gate with blocking failures must have status='failed'.")
        if self.status == QualityGateStatus.FAILED and self.user_override_allowed:
            raise ValueError("Failed quality gate cannot allow user override.")
        return self

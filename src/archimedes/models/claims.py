from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id
from .enums import ClaimType, StageName


class ClaimRecord(ArchimedesModel):
    claim_id: str = Field(default_factory=lambda: new_id("claim"))
    session_id: str
    claim: str
    type: ClaimType
    confidence: float = Field(ge=0.0, le=1.0)
    stage: StageName
    evidence_ids: list[str] = Field(default_factory=list)
    artifact_id: str | None = None
    requires_user_validation: bool = False
    validation_question: str | None = None

    # Human-in-the-loop validation decision
    validated_at: datetime | None = None
    validated_accepted: bool | None = None
    validation_comment: str | None = None

    @model_validator(mode="after")
    def validate_claim_requirements(self):
        if self.type == ClaimType.FACT and not self.evidence_ids:
            raise ValueError("Fact claims must reference at least one evidence source.")
        if self.requires_user_validation and not self.validation_question:
            raise ValueError(
                "validation_question is required when requires_user_validation=True."
            )
        return self

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id, utc_now
from .enums import PersonaName, SocratesDepth
from .quality_gates import QualityGateResult


class SocratesReviewContext(ArchimedesModel):
    session_id: str
    stage_run_id: str = Field(default_factory=lambda: new_id("stage_run"))
    base_version: int = Field(default=0, ge=0)
    target_version: int = Field(default=1, ge=1)
    depth: SocratesDepth = SocratesDepth.STANDARD
    business_need: dict[str, Any] = Field(default_factory=dict)
    requirements_summary: dict[str, Any] = Field(default_factory=dict)
    architecture_options: list[dict[str, Any]] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    change_context: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_versions(self):
        if self.target_version <= self.base_version:
            raise ValueError("target_version must be greater than base_version.")
        return self


class PersonaFinding(ArchimedesModel):
    finding_id: str = Field(default_factory=lambda: new_id("persona_finding"))
    persona: PersonaName
    target_option_id: str | None = None
    finding: str
    severity: str = "medium"
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    finding_type: str = "recommendation"
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    requires_validation: bool = False
    recommended_action: str | None = None


class PersonaAnalysis(ArchimedesModel):
    persona: PersonaName
    summary: str
    findings: list[PersonaFinding] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    failed: bool = False
    error: str | None = None


class SocraticSynthesis(ArchimedesModel):
    recommended_option_id: str | None = None
    ranked_option_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    blind_spots: list[str] = Field(default_factory=list)
    assumptions_to_validate: list[str] = Field(default_factory=list)
    premortem_scenarios: list[str] = Field(default_factory=list)
    hybrid_option_summary: str | None = None
    rationale: str
    recommended_decision: str | None = None  # "keep" | "modify" | "reject"
    claim_classifications: list[dict[str, Any]] = Field(default_factory=list)


class SocraticReview(ArchimedesModel):
    review_id: str = Field(default_factory=lambda: new_id("socratic_review"))
    session_id: str
    stage_run_id: str
    depth: SocratesDepth = SocratesDepth.STANDARD
    persona_analyses: list[PersonaAnalysis] = Field(default_factory=list)
    cross_examination: str | None = None
    synthesis: SocraticSynthesis
    quality_gate: QualityGateResult
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

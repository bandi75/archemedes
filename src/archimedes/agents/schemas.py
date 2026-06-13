"""Pydantic output schemas for each specialist agent.

Passed as `response_format` to `beta.chat.completions.parse()` so the LLM is
forced to emit a schema-valid JSON object as its final (non-tool-call) response.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class _ChecklistBase(BaseModel):
    """Base for quality-checklist models. Accepts a list of passed check names.

    LLMs sometimes return ["field_a", "field_b"] instead of {"field_a": true}.
    This validator normalises both forms to a plain dict before Pydantic
    validates the individual bool fields.
    """

    @model_validator(mode="before")
    @classmethod
    def _coerce_list_to_dict(cls, v: Any) -> Any:
        if isinstance(v, list):
            return {name: True for name in v if isinstance(name, str)}
        return v


# ---------------------------------------------------------------------------
# IntakeAgent
# ---------------------------------------------------------------------------

class IntakeArtifact(BaseModel):
    status: str = "complete"          # "clarifying" | "complete"
    questions: list[str] = Field(default_factory=list)
    refined_business_need: str = ""
    domain: str = ""
    scale_hint: str = ""
    timeline_hint: str = ""
    compliance_flags: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# RequirementsEngineer
# ---------------------------------------------------------------------------

class ClaimItem(BaseModel):
    type: str   # "fact" | "assumption" | "recommendation"
    label: str
    value: str


class RequirementItem(BaseModel):
    id: str = ""
    description: str
    priority: str = "must"  # "must" | "should" | "could"
    source: str = ""


class NonFunctionalRequirementItem(BaseModel):
    category: str
    description: str
    target: str = ""
    priority: str = "must"
    source: str = ""


class ConstraintItem(BaseModel):
    category: str = ""
    description: str
    requires_user_validation: bool = False


class RequirementsQualityChecklist(_ChecklistBase):
    scale_defined: bool = False
    security_defined: bool = False
    latency_defined: bool = False
    availability_defined: bool = False
    compliance_defined: bool = False
    data_residency_defined: bool = False
    integration_context_defined: bool = False
    operational_constraints_defined: bool = False


class RequirementsArtifact(BaseModel):
    functional_requirements: list[RequirementItem] = Field(min_length=1)
    non_functional_requirements: list[NonFunctionalRequirementItem] = Field(min_length=1)
    constraints: list[ConstraintItem] = Field(min_length=0)
    assumptions: list[ConstraintItem] = Field(min_length=0)
    claims: list[ClaimItem] = Field(min_length=1)
    quality_checklist: RequirementsQualityChecklist = Field(
        default_factory=RequirementsQualityChecklist
    )
    open_questions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# OptionsGenerator
# ---------------------------------------------------------------------------

class ComponentItem(BaseModel):
    azure_service: str
    role: str
    sku_tier: str


class TradeOffScores(BaseModel):
    cost: int = 5
    complexity: int = 5
    scalability: int = 5
    time_to_market: int = 5
    ops_burden: int = 5


class ArchitectureOption(BaseModel):
    name: str
    summary: str
    components: list[ComponentItem] = Field(default_factory=list)
    trade_off_scores: TradeOffScores = Field(default_factory=TradeOffScores)
    key_risks: list[str] = Field(default_factory=list)
    rationale: str = ""


class RejectedOption(BaseModel):
    name: str
    rejection_reason: str = ""
    reason: str = ""  # alternate field name LLMs sometimes use

    @property
    def effective_reason(self) -> str:
        return self.rejection_reason or self.reason


class OptionsQualityChecklist(_ChecklistBase):
    min_viable_options: bool = False
    rejected_option: bool = False
    tradeoffs_scored: bool = False
    cost_assumptions_present: bool = False
    risk_summary_present: bool = False
    evidence_links_present: bool = False


class OptionsArtifact(BaseModel):
    options: list[ArchitectureOption] = Field(default_factory=list)
    rejected_options: list[RejectedOption] = Field(default_factory=list)
    quality_checklist: OptionsQualityChecklist = Field(
        default_factory=OptionsQualityChecklist
    )


# ---------------------------------------------------------------------------
# ADRWriter
# ---------------------------------------------------------------------------

class OptionConsidered(BaseModel):
    name: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class ADRConsequences(BaseModel):
    positive: list[str] = Field(default_factory=list)
    negative: list[str] = Field(default_factory=list)
    neutral: list[str] = Field(default_factory=list)


class ADRQualityChecklist(_ChecklistBase):
    decision_captured: bool = False
    selected_option_valid: bool = False
    alternatives_listed: bool = False
    consequences_documented: bool = False
    assumptions_documented: bool = False
    socrates_findings_reflected: bool = False


class ADRArtifact(BaseModel):
    title: str = ""
    status: str = "Proposed"
    context: str = ""
    decision: str = ""
    options_considered: list[OptionConsidered] = Field(default_factory=list)
    consequences: ADRConsequences = Field(default_factory=ADRConsequences)
    blind_spots: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    quality_checklist: ADRQualityChecklist = Field(default_factory=ADRQualityChecklist)


# ---------------------------------------------------------------------------
# HLDDesigner
# ---------------------------------------------------------------------------

class HLDComponent(BaseModel):
    name: str
    type: str = ""
    azure_service: str = ""
    role: str = ""
    sku_tier: str = ""
    description: str = ""


class HLDIntegrationPoint(BaseModel):
    source: str
    target: str
    protocol: str = ""
    description: str = ""


class HLDKeyRisk(BaseModel):
    risk: str
    mitigation: str = ""


class HLDQualityChecklist(_ChecklistBase):
    components_shown: bool = False
    data_flow_shown: bool = False
    trust_boundaries_shown: bool = False
    mermaid_render_check_passed: bool = False
    network_zones_defined: bool = False
    identity_flow_defined: bool = False
    observability_flow_defined: bool = False


class HLDArtifact(BaseModel):
    system_context_diagram: str = ""
    container_diagram: str = ""
    data_flow_diagram: str = ""
    network_topology_diagram: str = ""
    components: list[HLDComponent] = Field(default_factory=list)
    integration_points: list[HLDIntegrationPoint] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    key_risks: list[HLDKeyRisk | str] = Field(default_factory=list)
    quality_checklist: HLDQualityChecklist = Field(default_factory=HLDQualityChecklist)


# ---------------------------------------------------------------------------
# WAFReviewer
# ---------------------------------------------------------------------------

class WAFFinding(BaseModel):
    pillar: str
    severity: str   # "critical" | "high" | "medium" | "low"
    recommendation: str
    evidence_source_id: str = ""


class WAFQualityChecklist(_ChecklistBase):
    reliability_reviewed: bool = False
    security_reviewed: bool = False
    cost_reviewed: bool = False
    ops_reviewed: bool = False
    performance_reviewed: bool = False
    critical_findings_prioritized: bool = False
    mitigations_present: bool = False


class WAFArtifact(BaseModel):
    findings: list[WAFFinding] = Field(default_factory=list)
    quality_checklist: WAFQualityChecklist = Field(default_factory=WAFQualityChecklist)
    summary: str = ""


# ---------------------------------------------------------------------------
# Registry: agent name → output schema class
# ---------------------------------------------------------------------------

AGENT_OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "IntakeAgent": IntakeArtifact,
    "RequirementsEngineer": RequirementsArtifact,
    "OptionsGenerator": OptionsArtifact,
    "ADRWriter": ADRArtifact,
    "HLDDesigner": HLDArtifact,
    "WAFReviewer": WAFArtifact,
}

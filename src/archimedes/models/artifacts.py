from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from .base import ArchimedesModel, FlexibleContentModel, new_id, utc_now
from .enums import StageName
from .quality_gates import QualityGateResult


class RequirementContent(FlexibleContentModel):
    summary: str | None = None
    functional_requirements: list[dict[str, Any]] = Field(default_factory=list)
    non_functional_requirements: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[dict[str, Any]] = Field(default_factory=list)


class OptionsContent(FlexibleContentModel):
    options: list[dict[str, Any]] = Field(default_factory=list)
    rejected_options: list[dict[str, Any]] = Field(default_factory=list)
    cost_estimate: dict[str, Any] | None = None


class MermaidDiagram(FlexibleContentModel):
    diagram_id: str = Field(default_factory=lambda: new_id("diagram"))
    diagram_type: str
    title: str
    mermaid_source: str
    render_checked: bool = False
    render_errors: list[str] = Field(default_factory=list)


class AdrContent(FlexibleContentModel):
    title: str
    status: str = "proposed"
    context: str
    decision: str
    alternatives: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)


class HldContent(FlexibleContentModel):
    title: str
    summary: str
    diagrams: list[MermaidDiagram] = Field(default_factory=list)
    components: list[dict[str, Any]] = Field(default_factory=list)
    data_flows: list[dict[str, Any]] = Field(default_factory=list)
    security_zones: list[dict[str, Any]] = Field(default_factory=list)


class WafFinding(FlexibleContentModel):
    finding_id: str = Field(default_factory=lambda: new_id("waf_finding"))
    pillar: str
    severity: str
    finding: str
    recommendation: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class WafReviewContent(FlexibleContentModel):
    findings: list[WafFinding] = Field(default_factory=list)
    summary_by_pillar: dict[str, str] = Field(default_factory=dict)


class VersionedArtifact(ArchimedesModel):
    artifact_id: str = Field(default_factory=lambda: new_id("artifact"))
    session_id: str
    stage: StageName
    version: int = Field(ge=1)
    stage_run_id: str
    content: dict[str, Any]
    content_type: str = "json"  # json | markdown | mermaid | mixed
    full_content_uri: str | None = None
    quality_gate: QualityGateResult
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    created_by: str | None = "archimedes"
    change_trigger: str | None = None

    @model_validator(mode="after")
    def content_or_uri_required(self):
        if not self.content and not self.full_content_uri:
            raise ValueError("Either content or full_content_uri must be provided.")
        return self

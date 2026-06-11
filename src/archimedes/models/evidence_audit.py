from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .base import ArchimedesModel, new_id, utc_now
from .enums import EvidenceAuditRecommendation, EvidenceQuality, Severity, StageName


class EvidenceAuditFinding(ArchimedesModel):
    finding_id: str = Field(default_factory=lambda: new_id("audit_finding"))
    severity: Severity
    category: str
    description: str
    claim_id: str | None = None
    evidence_id: str | None = None
    recommendation: str | None = None


class EvidenceAuditReport(ArchimedesModel):
    audit_id: str = Field(default_factory=lambda: new_id("evidence_audit"))
    session_id: str
    stage: StageName
    total_claims: int = Field(ge=0)
    facts_cited: int = Field(ge=0)
    recommendations_with_evidence: int = Field(ge=0)
    assumptions_unvalidated: int = Field(ge=0)
    unsupported_claims: int = Field(default=0, ge=0)
    irrelevant_citations: int = Field(default=0, ge=0)
    low_trust_sources: int = Field(default=0, ge=0)
    stale_citations: int = Field(default=0, ge=0)
    contradictions: int = Field(default=0, ge=0)
    findings: list[EvidenceAuditFinding] = Field(default_factory=list)
    requires_user_validation: list[str] = Field(default_factory=list)
    blocking_failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    overall_evidence_quality: EvidenceQuality
    recommendation: EvidenceAuditRecommendation
    created_at: datetime = Field(default_factory=utc_now)

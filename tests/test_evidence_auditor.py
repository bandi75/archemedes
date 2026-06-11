from __future__ import annotations

from archimedes.agents.evidence_auditor import EvidenceAuditor
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import (
    ClaimType,
    EvidenceAuditRecommendation,
    EvidenceQuality,
    EvidenceRetrievalMethod,
    QualityGateStatus,
    SourceFreshness,
    StageName,
    TrustLevel,
)
from archimedes.models.evidence import EvidenceSource


class AuditStorage:
    def __init__(self):
        self.claims = []
        self.evidence = []

    def list_claims(self, session_id: str, **filters):
        return [claim for claim in self.claims if claim.session_id == session_id]

    def list_evidence(self, session_id: str, **filters):
        return [evidence for evidence in self.evidence if evidence.session_id == session_id]


def test_evidence_auditor_blocks_unsupported_fact_claims():
    storage = AuditStorage()
    storage.claims.append(
        ClaimRecord.model_construct(
            claim_id="claim-unsupported",
            session_id="session-1",
            claim="Event Hubs supports this exact throughput target.",
            type=ClaimType.FACT,
            confidence=0.9,
            stage=StageName.OPTIONS_GENERATION,
            evidence_ids=[],
        )
    )

    report = EvidenceAuditor().run(
        session_id="session-1",
        storage=storage,
        stage=StageName.EVIDENCE_AUDIT_CHECKPOINT,
    )

    assert report.overall_evidence_quality == EvidenceQuality.WEAK
    assert report.recommendation == EvidenceAuditRecommendation.PAUSE_AND_VALIDATE
    assert report.unsupported_claims == 1
    assert report.blocking_failures


def test_evidence_auditor_warns_on_low_trust_stale_sources_and_missing_kb_version():
    storage = AuditStorage()
    evidence = EvidenceSource(
        session_id="session-1",
        source="Unverified blog",
        retrieved_via=EvidenceRetrievalMethod.FOUNDRY_IQ,
        source_freshness=SourceFreshness.STALE,
        trust_level=TrustLevel.LOW,
    )
    storage.evidence.append(evidence)
    storage.claims.append(
        ClaimRecord(
            session_id="session-1",
            claim="A recommendation informed by a weak source.",
            type=ClaimType.RECOMMENDATION,
            confidence=0.7,
            stage=StageName.SOCRATIC_REVIEW,
            evidence_ids=[evidence.evidence_id],
        )
    )

    report = EvidenceAuditor().run(
        session_id="session-1",
        storage=storage,
        stage=StageName.EVIDENCE_AUDIT_CHECKPOINT,
    )

    assert report.overall_evidence_quality == EvidenceQuality.ADEQUATE
    assert report.recommendation == EvidenceAuditRecommendation.REVIEW_FLAGGED_ITEMS
    assert report.low_trust_sources == 1
    assert report.stale_citations == 1
    assert any(finding.category == "missing_kb_version" for finding in report.findings)


def test_evidence_auditor_stage_patch_uses_report_quality_gate():
    storage = AuditStorage()
    report = EvidenceAuditor().run(
        session_id="session-1",
        storage=storage,
        stage=StageName.FINAL_EVIDENCE_AUDIT,
    )
    patch = EvidenceAuditor().build_stage_patch(report, base_version=0)

    assert patch.stage == StageName.FINAL_EVIDENCE_AUDIT
    assert patch.patch["evidence_audit"]["overall_evidence_quality"] == EvidenceQuality.STRONG
    assert patch.quality_gate_result.status == QualityGateStatus.PASSED

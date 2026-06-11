from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import (
    ClaimType,
    EvidenceAuditRecommendation,
    EvidenceQuality,
    EvidenceRetrievalMethod,
    QualityGateStatus,
    Severity,
    SourceFreshness,
    StageName,
    TrustLevel,
)
from archimedes.models.evidence import EvidenceSource
from archimedes.models.evidence_audit import EvidenceAuditFinding, EvidenceAuditReport
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.base import new_id


class SupportsEvidenceAuditStorage(Protocol):
    def list_claims(self, session_id: str, **filters) -> list[ClaimRecord]: ...

    def list_evidence(self, session_id: str, **filters) -> list[EvidenceSource]: ...


POST_SOCRATES_STAGES = {
    StageName.REQUIREMENTS_EXTRACTION,
    StageName.PATTERN_DETECTION,
    StageName.OPTIONS_GENERATION,
    StageName.SOCRATIC_REVIEW,
}

FINAL_AUDIT_STAGES = {
    *POST_SOCRATES_STAGES,
    StageName.ADR_GENERATION,
    StageName.HLD_GENERATION,
    StageName.MINI_WAF_REVIEW,
}


@dataclass(slots=True)
class EvidenceAuditor:
    """Deterministic Evidence Auditor routine for MVP checkpoints."""

    def run(
        self,
        *,
        session_id: str,
        storage: SupportsEvidenceAuditStorage,
        stage: StageName = StageName.EVIDENCE_AUDIT_CHECKPOINT,
    ) -> EvidenceAuditReport:
        claims = _safe_list_claims(storage, session_id)
        evidence_sources = _safe_list_evidence(storage, session_id)
        scoped_claims = self._scope_claims(claims, stage)
        evidence_by_id = {evidence.evidence_id: evidence for evidence in evidence_sources}
        findings: list[EvidenceAuditFinding] = []
        requires_user_validation: list[str] = []

        facts_cited = 0
        recommendations_with_evidence = 0
        assumptions_unvalidated = 0

        for claim in scoped_claims:
            linked = [evidence_by_id[eid] for eid in claim.evidence_ids if eid in evidence_by_id]
            if claim.type == ClaimType.FACT:
                if linked:
                    facts_cited += 1
                else:
                    findings.append(
                        EvidenceAuditFinding(
                            severity=Severity.HIGH,
                            category="unsupported_claim",
                            description="Factual claim has no linked evidence.",
                            claim_id=claim.claim_id,
                            recommendation="Retrieve trusted evidence or downgrade the claim classification.",
                        )
                    )
            if claim.type == ClaimType.RECOMMENDATION and linked:
                recommendations_with_evidence += 1
            if claim.type == ClaimType.ASSUMPTION and claim.requires_user_validation:
                assumptions_unvalidated += 1
                requires_user_validation.append(claim.claim_id)
                findings.append(
                    EvidenceAuditFinding(
                        severity=Severity.WARNING,
                        category="missing_user_validation",
                        description="Assumption requires user validation.",
                        claim_id=claim.claim_id,
                        recommendation="Ask the user to validate or reject this assumption.",
                    )
                )

        for evidence in evidence_sources:
            if evidence.session_id != session_id:
                continue
            if evidence.trust_level == TrustLevel.LOW:
                findings.append(
                    EvidenceAuditFinding(
                        severity=Severity.WARNING,
                        category="low_trust_source",
                        description="Evidence source has low trust level.",
                        evidence_id=evidence.evidence_id,
                        recommendation="Replace with Microsoft Learn, Azure Architecture Center, WAF, SLA, or pricing evidence.",
                    )
                )
            if evidence.source_freshness == SourceFreshness.STALE:
                findings.append(
                    EvidenceAuditFinding(
                        severity=Severity.WARNING,
                        category="stale_source",
                        description="Evidence source is marked stale.",
                        evidence_id=evidence.evidence_id,
                        recommendation="Refresh the source or downgrade dependent claims.",
                    )
                )
            if (
                evidence.retrieved_via == EvidenceRetrievalMethod.FOUNDRY_IQ
                and (not evidence.kb_name or not evidence.kb_version)
            ):
                findings.append(
                    EvidenceAuditFinding(
                        severity=Severity.WARNING,
                        category="missing_kb_version",
                        description="Foundry IQ evidence is missing KB version metadata.",
                        evidence_id=evidence.evidence_id,
                        recommendation="Preserve kb_name and kb_version with retrieved evidence.",
                    )
                )

        blocking = [
            finding.description
            for finding in findings
            if finding.severity in {Severity.HIGH, Severity.CRITICAL}
        ]
        warnings = [
            finding.description
            for finding in findings
            if finding.severity == Severity.WARNING
        ]
        low_trust_count = sum(1 for finding in findings if finding.category == "low_trust_source")
        stale_count = sum(1 for finding in findings if finding.category == "stale_source")
        unsupported_count = sum(1 for finding in findings if finding.category == "unsupported_claim")

        quality = EvidenceQuality.STRONG
        recommendation = EvidenceAuditRecommendation.PROCEED
        if blocking:
            quality = EvidenceQuality.WEAK
            recommendation = EvidenceAuditRecommendation.PAUSE_AND_VALIDATE
        elif warnings:
            quality = EvidenceQuality.ADEQUATE
            recommendation = EvidenceAuditRecommendation.REVIEW_FLAGGED_ITEMS

        return EvidenceAuditReport(
            session_id=session_id,
            stage=stage,
            total_claims=len(scoped_claims),
            facts_cited=facts_cited,
            recommendations_with_evidence=recommendations_with_evidence,
            assumptions_unvalidated=assumptions_unvalidated,
            unsupported_claims=unsupported_count,
            low_trust_sources=low_trust_count,
            stale_citations=stale_count,
            findings=findings,
            requires_user_validation=requires_user_validation,
            blocking_failures=blocking,
            warnings=warnings,
            overall_evidence_quality=quality,
            recommendation=recommendation,
        )

    def build_stage_patch(
        self,
        report: EvidenceAuditReport,
        *,
        stage_run_id: str | None = None,
        base_version: int,
    ) -> StagePatch:
        payload = report.model_dump(mode="json")
        patch_payload = {"evidence_audit": payload}
        patch_hash = _compute_hash(patch_payload)
        stage_run = stage_run_id or new_id("stage_run")
        gate = QualityGateResult(
            status=(
                QualityGateStatus.FAILED
                if report.blocking_failures
                else QualityGateStatus.PASSED_WITH_WARNINGS
                if report.warnings
                else QualityGateStatus.PASSED
            ),
            blocking_failures=report.blocking_failures,
            warnings=report.warnings,
            user_override_allowed=False if report.blocking_failures else True,
        )
        return StagePatch(
            session_id=report.session_id,
            stage=report.stage,
            stage_run_id=stage_run,
            base_version=base_version,
            target_version=base_version + 1,
            idempotency_key=_idempotency_key(report.session_id, report.stage, stage_run, patch_hash),
            patch_hash=patch_hash,
            patch=patch_payload,
            claims=[],
            evidence_sources=[],
            quality_gate_result=gate,
        )

    @staticmethod
    def _scope_claims(claims: list[ClaimRecord], audit_stage: StageName) -> list[ClaimRecord]:
        allowed = FINAL_AUDIT_STAGES if audit_stage == StageName.FINAL_EVIDENCE_AUDIT else POST_SOCRATES_STAGES
        return [claim for claim in claims if claim.stage in allowed]


def _safe_list_claims(storage: SupportsEvidenceAuditStorage, session_id: str) -> list[ClaimRecord]:
    list_claims = getattr(storage, "list_claims", None)
    if list_claims is None:
        return []
    return list_claims(session_id)


def _safe_list_evidence(storage: SupportsEvidenceAuditStorage, session_id: str) -> list[EvidenceSource]:
    list_evidence = getattr(storage, "list_evidence", None)
    if list_evidence is None:
        return []
    return list_evidence(session_id)


def _compute_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _idempotency_key(session_id: str, stage: StageName, stage_run_id: str, patch_hash: str) -> str:
    stage_value = stage.value if isinstance(stage, StageName) else str(stage)
    return hashlib.sha256(
        f"{session_id}:{stage_value}:{stage_run_id}:{patch_hash}".encode("utf-8")
    ).hexdigest()

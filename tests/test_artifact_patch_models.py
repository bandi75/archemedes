import pytest

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ClaimType, StageName
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult


def _passed_gate() -> QualityGateResult:
    return QualityGateResult(status="passed")


def test_versioned_artifact_requires_content_or_uri():
    with pytest.raises(ValueError):
        VersionedArtifact(
            session_id="session_123",
            stage=StageName.OPTIONS_GENERATION,
            version=1,
            stage_run_id="stage_run_123",
            content={},
            quality_gate=_passed_gate(),
        )


def test_stage_patch_requires_target_version_gt_base():
    with pytest.raises(ValueError):
        StagePatch(
            session_id="session_123",
            stage=StageName.REQUIREMENTS_EXTRACTION,
            stage_run_id="stage_run_123",
            base_version=1,
            target_version=1,
            idempotency_key="k1",
            patch_hash="h1",
            patch={"field": "value"},
            quality_gate_result=_passed_gate(),
        )


def test_fact_claim_requires_evidence_ids():
    with pytest.raises(ValueError):
        ClaimRecord(
            session_id="session_123",
            claim="Event Hubs supports this throughput",
            type=ClaimType.FACT,
            confidence=0.8,
            stage=StageName.OPTIONS_GENERATION,
            evidence_ids=[],
        )


def test_stage_patch_failed_gate_requires_blocking_failures():
    with pytest.raises(ValueError):
        StagePatch(
            session_id="session_123",
            stage=StageName.ADR_GENERATION,
            stage_run_id="stage_run_123",
            base_version=0,
            target_version=1,
            idempotency_key="k2",
            patch_hash="h2",
            patch={"title": "ADR"},
            quality_gate_result=QualityGateResult(status="failed", user_override_allowed=False),
        )

import pytest

from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ClaimType, StageName
from archimedes.models.evidence import EvidenceSource


def test_claim_requires_validation_question_when_flagged():
    with pytest.raises(ValueError):
        ClaimRecord(
            session_id="session_123",
            claim="Assume team has Kafka expertise",
            type=ClaimType.ASSUMPTION,
            confidence=0.5,
            stage=StageName.REQUIREMENTS_EXTRACTION,
            requires_user_validation=True,
        )


def test_evidence_source_accepts_mock_retrieval_and_fixture_flag():
    evidence = EvidenceSource(
        session_id="session_123",
        source="Mock KB citation",
        retrieved_via="mock",
        kb_name="mock-kb",
        kb_version="fixture-v1",
        is_fixture=True,
    )
    assert evidence.retrieved_via == "mock"
    assert evidence.trust_level == "medium"
    assert evidence.source_freshness == "unknown"

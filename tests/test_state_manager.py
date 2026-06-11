from __future__ import annotations

import hashlib
import json

from archimedes.models.change import ChangeEvent
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ClaimType, StageName
from archimedes.models.evidence import EvidenceSource
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.session import ArchitectureSession
from archimedes.state.state_manager import ArchitectureStateManager


class FakePreconditionError(Exception):
    def __init__(self):
        super().__init__("Precondition Failed")
        self.status_code = 412


class FakeStorage:
    def __init__(self):
        self.session: ArchitectureSession | None = None
        self.latest_artifact = None
        self.idempotency_hit: dict | None = None
        self.written_artifact = None
        self.claims: list[ClaimRecord] = []
        self.evidence: list[EvidenceSource] = []
        self.change_events: list[ChangeEvent] = []
        self.fail_first_artifact_upsert = False
        self.artifact_upsert_calls = 0

    def read_session(self, session_id: str):
        return self.session

    def read_latest_artifact(self, session_id: str, stage: str):
        return self.latest_artifact

    def find_by_idempotency_key(self, session_id: str, key: str):
        return self.idempotency_hit

    def upsert_artifact(self, artifact, *, idempotency_key=None, patch_id=None):
        self.artifact_upsert_calls += 1
        if self.fail_first_artifact_upsert and self.artifact_upsert_calls == 1:
            raise FakePreconditionError()
        self.written_artifact = artifact
        return artifact

    def append_claim(self, claim):
        self.claims.append(claim)
        return claim

    def append_evidence(self, evidence):
        self.evidence.append(evidence)
        return evidence

    def upsert_session(self, session):
        self.session = session
        return session

    def append_change_event(self, event):
        self.change_events.append(event)
        return event


def _patch_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _build_patch(
    *,
    session_id: str,
    base_version: int = 0,
    target_version: int = 1,
    gate: QualityGateResult | None = None,
):
    payload = {"summary": "updated output"}
    evidence = EvidenceSource(
        session_id=session_id,
        source="KB result",
        source_url="https://example.com/doc",
        retrieved_via="foundry_iq",
        kb_name="azure-architecture-kb",
        kb_version="v1",
    )
    claim = ClaimRecord(
        session_id=session_id,
        claim="The architecture is event-driven",
        type=ClaimType.FACT,
        confidence=0.9,
        stage=StageName.OPTIONS_GENERATION,
        evidence_ids=[evidence.evidence_id],
    )
    gate_result = gate or QualityGateResult(status="passed")
    return StagePatch(
        session_id=session_id,
        stage=StageName.OPTIONS_GENERATION,
        stage_run_id="stage_run_1",
        base_version=base_version,
        target_version=target_version,
        idempotency_key="idem-1",
        patch_hash=_patch_hash(payload),
        patch=payload,
        claims=[claim],
        evidence_sources=[evidence],
        quality_gate_result=gate_result,
    )


def test_apply_patch_idempotent_replay_returns_existing_result():
    storage = FakeStorage()
    session = ArchitectureSession(business_need="Design fraud detection")
    storage.session = session
    patch = _build_patch(session_id=session.session_id)

    storage.idempotency_hit = {
        "idempotency_key": patch.idempotency_key,
        "patch_hash": patch.patch_hash,
        "version": 3,
    }

    manager = ArchitectureStateManager(storage=storage)
    result = manager.apply_patch(patch)

    assert result.applied is True
    assert result.action == "idempotent_replay"
    assert result.version == 3
    assert storage.written_artifact is None


def test_apply_patch_rejects_failed_quality_gate_without_writes():
    storage = FakeStorage()
    session = ArchitectureSession(business_need="Design fraud detection")
    storage.session = session
    failed_gate = QualityGateResult(
        status="failed",
        blocking_failures=["missing compliance requirement"],
        user_override_allowed=False,
    )
    patch = _build_patch(session_id=session.session_id, gate=failed_gate)

    manager = ArchitectureStateManager(storage=storage)
    result = manager.apply_patch(patch)

    assert result.applied is False
    assert result.reason == "quality_gate_failed"
    assert storage.written_artifact is None
    assert not storage.claims
    assert not storage.evidence
    assert not storage.change_events


def test_apply_patch_rejects_base_version_conflict():
    storage = FakeStorage()
    session = ArchitectureSession(business_need="Design fraud detection")
    storage.session = session
    patch = _build_patch(session_id=session.session_id, base_version=0, target_version=1)

    class _Artifact:
        version = 2

    storage.latest_artifact = _Artifact()

    manager = ArchitectureStateManager(storage=storage)
    result = manager.apply_patch(patch)

    assert result.applied is False
    assert result.reason == "version_conflict"
    assert result.current_version == 2


def test_apply_patch_passed_with_warnings_writes_and_updates_session():
    storage = FakeStorage()
    session = ArchitectureSession(business_need="Design fraud detection")
    storage.session = session
    warning_gate = QualityGateResult(
        status="passed_with_warnings",
        warnings=["Throughput assumption needs validation"],
    )
    patch = _build_patch(session_id=session.session_id, gate=warning_gate)

    manager = ArchitectureStateManager(storage=storage)
    result = manager.apply_patch(patch)

    assert result.applied is True
    assert result.action == "applied"
    assert storage.written_artifact is not None
    assert session.latest_artifact_versions[StageName.OPTIONS_GENERATION] == 1
    assert session.quality_gates[StageName.OPTIONS_GENERATION].status == "passed_with_warnings"
    assert len(storage.claims) == 1
    assert len(storage.evidence) == 1
    assert len(storage.change_events) == 1


def test_apply_patch_retries_once_on_precondition_failed():
    storage = FakeStorage()
    session = ArchitectureSession(business_need="Design fraud detection")
    storage.session = session
    storage.fail_first_artifact_upsert = True
    patch = _build_patch(session_id=session.session_id)

    manager = ArchitectureStateManager(storage=storage, max_apply_retries=2)
    result = manager.apply_patch(patch)

    assert result.applied is True
    assert storage.artifact_upsert_calls == 2

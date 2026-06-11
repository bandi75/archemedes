from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.change import ChangeEvent
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ChangeType, ClaimType, StageName
from archimedes.models.evidence import EvidenceSource
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.session import ArchitectureSession
from archimedes.storage.cosmos_client import CONTAINER_NAMES, CosmosStorageClient


class FakeCosmosHttpError(Exception):
    def __init__(self, status_code: int, message: str = ""):
        super().__init__(message or f"status={status_code}")
        self.status_code = status_code


@dataclass
class _Entry:
    body: dict[str, Any]
    etag: int


class FakeContainer:
    def __init__(self):
        self._items: dict[tuple[str, str], _Entry] = {}
        self.precondition_failures_remaining = 0

    def read_item(self, item: str, partition_key: str) -> dict[str, Any]:
        key = (partition_key, item)
        if key not in self._items:
            raise FakeCosmosHttpError(404)
        entry = self._items[key]
        return {**entry.body, "_etag": f'"{entry.etag}"'}

    def create_item(self, body: dict[str, Any]) -> dict[str, Any]:
        key = (body["session_id"], body["id"])
        if key in self._items:
            raise FakeCosmosHttpError(409)
        self._items[key] = _Entry(body=body.copy(), etag=1)
        return {**body, "_etag": '"1"'}

    def replace_item(
        self,
        item: str,
        body: dict[str, Any],
        *,
        etag: str | None = None,
        match_condition: Any | None = None,
    ) -> dict[str, Any]:
        key = (body["session_id"], item)
        if key not in self._items:
            raise FakeCosmosHttpError(404)

        if self.precondition_failures_remaining > 0:
            self.precondition_failures_remaining -= 1
            raise FakeCosmosHttpError(412, "Precondition Failed")

        current = self._items[key]
        current_etag = f'"{current.etag}"'
        if match_condition and etag is not None and etag != current_etag:
            raise FakeCosmosHttpError(412, "Precondition Failed")

        new_etag = current.etag + 1
        self._items[key] = _Entry(body=body.copy(), etag=new_etag)
        return {**body, "_etag": f'"{new_etag}"'}

    def query_items(
        self,
        query: str,
        parameters: list[dict[str, Any]],
        *,
        enable_cross_partition_query: bool,
    ) -> list[dict[str, Any]]:
        params = {p["name"]: p["value"] for p in parameters}
        session_id = params.get("@session_id")
        rows = [entry.body.copy() for (pk, _), entry in self._items.items() if pk == session_id]

        if "@stage" in params:
            rows = [r for r in rows if r.get("stage") == params["@stage"]]
            rows.sort(key=lambda r: r.get("version", 0), reverse=True)
            return rows[:1]

        if "@idempotency_key" in params:
            rows = [r for r in rows if r.get("idempotency_key") == params["@idempotency_key"]]
            rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
            return rows[:1]

        return rows


class FakeDatabase:
    def __init__(self):
        self.created_containers: list[str] = []
        self._containers = {name: FakeContainer() for name in CONTAINER_NAMES.values()}

    def get_container_client(self, container: str) -> FakeContainer:
        return self._containers[container]

    def create_container_if_not_exists(self, *, id: str, partition_key: Any) -> dict[str, Any]:
        self.created_containers.append(id)
        return {"id": id, "partition_key": partition_key}


def _passed_gate() -> QualityGateResult:
    return QualityGateResult(status="passed")


def _artifact(session_id: str, version: int, stage_run_id: str = "run_1") -> VersionedArtifact:
    return VersionedArtifact(
        session_id=session_id,
        stage=StageName.OPTIONS_GENERATION,
        version=version,
        stage_run_id=stage_run_id,
        content={"option": f"v{version}"},
        quality_gate=_passed_gate(),
    )


def test_ensure_containers_uses_canonical_names():
    db = FakeDatabase()
    CosmosStorageClient.ensure_containers(db)
    assert db.created_containers == list(CONTAINER_NAMES.values())


def test_upsert_and_read_session_roundtrip():
    db = FakeDatabase()
    client = CosmosStorageClient.from_database(db)

    session = ArchitectureSession(business_need="Design fraud detection architecture")
    saved = client.upsert_session(session)
    loaded = client.read_session(session.session_id)

    assert saved.session_id == session.session_id
    assert loaded is not None
    assert loaded.business_need == session.business_need


def test_upsert_artifact_and_read_latest_artifact():
    db = FakeDatabase()
    client = CosmosStorageClient.from_database(db)
    session_id = "session_123"

    older = client.upsert_artifact(_artifact(session_id=session_id, version=1))
    newer = client.upsert_artifact(_artifact(session_id=session_id, version=2))
    latest = client.read_latest_artifact(session_id=session_id, stage=StageName.OPTIONS_GENERATION)

    assert older.version == 1
    assert newer.version == 2
    assert latest is not None
    assert latest.version == 2


def test_find_by_idempotency_key_returns_matching_artifact_document():
    db = FakeDatabase()
    client = CosmosStorageClient.from_database(db)
    session_id = "session_abc"

    artifact = _artifact(session_id=session_id, version=1)
    payload = artifact.model_dump(mode="json")
    payload["id"] = artifact.artifact_id
    payload["idempotency_key"] = "idem-1"
    payload["created_at"] = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc).isoformat()
    db.get_container_client(CONTAINER_NAMES["artifacts"]).create_item(payload)

    found = client.find_by_idempotency_key(session_id=session_id, key="idem-1")
    missing = client.find_by_idempotency_key(session_id=session_id, key="missing")

    assert found is not None
    assert found["idempotency_key"] == "idem-1"
    assert missing is None


def test_append_claim_evidence_and_change_event():
    db = FakeDatabase()
    client = CosmosStorageClient.from_database(db)
    session_id = "session_xyz"

    evidence = EvidenceSource(
        session_id=session_id,
        source="Event Hubs limits",
        source_url="https://example.com/event-hubs",
        retrieved_via="web_search",
    )
    saved_evidence = client.append_evidence(evidence)

    claim = ClaimRecord(
        session_id=session_id,
        claim="Event Hubs can support required throughput",
        type=ClaimType.FACT,
        confidence=0.8,
        stage=StageName.OPTIONS_GENERATION,
        evidence_ids=[saved_evidence.evidence_id],
    )
    saved_claim = client.append_claim(claim)

    change = ChangeEvent(
        session_id=session_id,
        change_type=ChangeType.REQUIREMENT_MODIFIED,
        changed_field="throughput",
    )
    saved_change = client.append_change_event(change)

    assert saved_claim.evidence_ids == [saved_evidence.evidence_id]
    assert saved_change.changed_field == "throughput"


def test_optimistic_concurrency_retries_on_precondition_failure():
    db = FakeDatabase()
    client = CosmosStorageClient.from_database(db)

    session = ArchitectureSession(business_need="Initial")
    client.upsert_session(session)

    container = db.get_container_client(CONTAINER_NAMES["sessions"])
    container.precondition_failures_remaining = 1

    session.business_need = "Updated need"
    saved = client.upsert_session(session)

    assert saved.business_need == "Updated need"

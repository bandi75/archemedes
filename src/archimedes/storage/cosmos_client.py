from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.change import ChangeEvent
from archimedes.models.claims import ClaimRecord
from archimedes.models.evidence import EvidenceSource
from archimedes.models.session import ArchitectureSession


CONTAINER_NAMES = {
    "sessions": "architecture_sessions",
    "artifacts": "versioned_artifacts",
    "claims_evidence": "claims_evidence",
    "change_events": "change_events",
}


class CosmosContainerProtocol(Protocol):
    def read_item(self, item: str, partition_key: str) -> dict[str, Any]: ...

    def create_item(self, body: dict[str, Any]) -> dict[str, Any]: ...

    def replace_item(
        self,
        item: str,
        body: dict[str, Any],
        *,
        etag: str | None = None,
        match_condition: Any | None = None,
    ) -> dict[str, Any]: ...

    def query_items(
        self,
        query: str,
        parameters: list[dict[str, Any]],
        *,
        enable_cross_partition_query: bool,
    ) -> list[dict[str, Any]]: ...


class CosmosDatabaseProtocol(Protocol):
    def get_container_client(self, container: str) -> CosmosContainerProtocol: ...

    def create_container_if_not_exists(
        self,
        *,
        id: str,
        partition_key: Any,
    ) -> Any: ...


@dataclass(slots=True)
class CosmosStorageClient:
    sessions: CosmosContainerProtocol
    artifacts: CosmosContainerProtocol
    claims_evidence: CosmosContainerProtocol
    change_events: CosmosContainerProtocol
    max_write_retries: int = 3

    @classmethod
    def from_database(cls, database: CosmosDatabaseProtocol) -> "CosmosStorageClient":
        return cls(
            sessions=database.get_container_client(CONTAINER_NAMES["sessions"]),
            artifacts=database.get_container_client(CONTAINER_NAMES["artifacts"]),
            claims_evidence=database.get_container_client(CONTAINER_NAMES["claims_evidence"]),
            change_events=database.get_container_client(CONTAINER_NAMES["change_events"]),
        )

    @staticmethod
    def ensure_containers(database: CosmosDatabaseProtocol) -> None:
        # Keep partitioning consistent across all containers for MVP simplicity.
        for name in CONTAINER_NAMES.values():
            database.create_container_if_not_exists(
                id=name,
                partition_key={"paths": ["/session_id"], "kind": "Hash"},
            )

    def read_session(self, session_id: str) -> ArchitectureSession | None:
        payload = self._read_by_id(self.sessions, item_id=session_id, partition_key=session_id)
        if payload is None:
            return None
        return ArchitectureSession.model_validate(self._clean_payload(payload))

    def upsert_session(self, session: ArchitectureSession) -> ArchitectureSession:
        payload = session.model_dump(mode="json")
        payload["id"] = session.session_id
        stored = self._write_with_optimistic_concurrency(
            container=self.sessions,
            item_id=session.session_id,
            partition_key=session.session_id,
            payload=payload,
        )
        return ArchitectureSession.model_validate(self._clean_payload(stored))

    def read_latest_artifact(self, session_id: str, stage: str) -> VersionedArtifact | None:
        query = (
            "SELECT TOP 1 * FROM c "
            "WHERE c.session_id = @session_id AND c.stage = @stage "
            "ORDER BY c.version DESC"
        )
        items = list(
            self.artifacts.query_items(
                query=query,
                parameters=[
                    {"name": "@session_id", "value": session_id},
                    {"name": "@stage", "value": stage},
                ],
                enable_cross_partition_query=False,
            )
        )
        if not items:
            return None
        return VersionedArtifact.model_validate(self._clean_payload(items[0]))

    def upsert_artifact(
        self,
        artifact: VersionedArtifact,
        *,
        idempotency_key: str | None = None,
        patch_id: str | None = None,
    ) -> VersionedArtifact:
        payload = artifact.model_dump(mode="json")
        payload["id"] = artifact.artifact_id
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        if patch_id:
            payload["patch_id"] = patch_id

        stored = self._write_with_optimistic_concurrency(
            container=self.artifacts,
            item_id=artifact.artifact_id,
            partition_key=artifact.session_id,
            payload=payload,
        )
        return VersionedArtifact.model_validate(self._clean_payload(stored))

    def append_evidence(self, evidence: EvidenceSource) -> EvidenceSource:
        payload = evidence.model_dump(mode="json")
        payload["id"] = evidence.evidence_id
        stored = self._write_with_optimistic_concurrency(
            container=self.claims_evidence,
            item_id=evidence.evidence_id,
            partition_key=evidence.session_id,
            payload=payload,
        )
        return EvidenceSource.model_validate(self._clean_payload(stored))

    def append_claim(self, claim: ClaimRecord) -> ClaimRecord:
        payload = claim.model_dump(mode="json")
        payload["id"] = claim.claim_id
        stored = self._write_with_optimistic_concurrency(
            container=self.claims_evidence,
            item_id=claim.claim_id,
            partition_key=claim.session_id,
            payload=payload,
        )
        return ClaimRecord.model_validate(self._clean_payload(stored))

    def append_change_event(self, event: ChangeEvent) -> ChangeEvent:
        payload = event.model_dump(mode="json")
        payload["id"] = event.change_event_id
        stored = self._write_with_optimistic_concurrency(
            container=self.change_events,
            item_id=event.change_event_id,
            partition_key=event.session_id,
            payload=payload,
        )
        return ChangeEvent.model_validate(self._clean_payload(stored))

    def find_by_idempotency_key(
        self,
        session_id: str,
        key: str,
    ) -> dict[str, Any] | None:
        query = (
            "SELECT TOP 1 * FROM c "
            "WHERE c.session_id = @session_id AND c.idempotency_key = @idempotency_key "
            "ORDER BY c.created_at DESC"
        )
        items = list(
            self.artifacts.query_items(
                query=query,
                parameters=[
                    {"name": "@session_id", "value": session_id},
                    {"name": "@idempotency_key", "value": key},
                ],
                enable_cross_partition_query=False,
            )
        )
        if not items:
            return None
        return items[0]

    def _write_with_optimistic_concurrency(
        self,
        *,
        container: CosmosContainerProtocol,
        item_id: str,
        partition_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        attempts = 0
        last_error: Exception | None = None

        while attempts <= self.max_write_retries:
            attempts += 1
            current = self._read_by_id(container, item_id=item_id, partition_key=partition_key)
            try:
                if current is None:
                    return container.create_item(body=payload)

                etag = current.get("_etag")
                if etag is None:
                    return container.replace_item(item=item_id, body=payload)

                return container.replace_item(
                    item=item_id,
                    body=payload,
                    etag=etag,
                    match_condition="IfNotModified",
                )
            except Exception as exc:  # pragma: no cover - branch exercised by unit fakes
                if self._is_precondition_failed(exc) and attempts <= self.max_write_retries:
                    last_error = exc
                    continue
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Write retry loop exited unexpectedly.")

    @staticmethod
    def _read_by_id(
        container: CosmosContainerProtocol,
        *,
        item_id: str,
        partition_key: str,
    ) -> dict[str, Any] | None:
        try:
            return container.read_item(item=item_id, partition_key=partition_key)
        except Exception as exc:  # pragma: no cover - branch exercised by unit fakes
            if CosmosStorageClient._is_not_found(exc):
                return None
            raise

    @staticmethod
    def _status_code(exc: Exception) -> int | None:
        code = getattr(exc, "status_code", None)
        if code is None:
            code = getattr(exc, "status", None)
        return code if isinstance(code, int) else None

    @staticmethod
    def _is_not_found(exc: Exception) -> bool:
        status_code = CosmosStorageClient._status_code(exc)
        return status_code == 404

    @staticmethod
    def _is_precondition_failed(exc: Exception) -> bool:
        status_code = CosmosStorageClient._status_code(exc)
        if status_code == 412:
            return True
        return "precondition" in str(exc).lower()

    @staticmethod
    def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
        clean = payload.copy()
        clean.pop("id", None)
        clean.pop("_etag", None)
        return clean

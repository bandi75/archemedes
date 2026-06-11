from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.change import ChangeEvent
from archimedes.models.enums import ChangeType, QualityGateStatus, StageStatus
from archimedes.models.patches import ApplyPatchResult, StagePatch
from archimedes.models.session import ArchitectureSession, StageExecution
from archimedes.storage.cosmos_client import CosmosStorageClient


class SupportsStateStorage(Protocol):
    def read_session(self, session_id: str) -> ArchitectureSession | None: ...

    def read_latest_artifact(self, session_id: str, stage: str) -> VersionedArtifact | None: ...

    def find_by_idempotency_key(self, session_id: str, key: str) -> dict | None: ...

    def upsert_artifact(
        self,
        artifact: VersionedArtifact,
        *,
        idempotency_key: str | None = None,
        patch_id: str | None = None,
    ) -> VersionedArtifact: ...

    def append_claim(self, claim): ...

    def append_evidence(self, evidence): ...

    def upsert_session(self, session: ArchitectureSession) -> ArchitectureSession: ...

    def append_change_event(self, event: ChangeEvent) -> ChangeEvent: ...


@dataclass(slots=True)
class ArchitectureStateManager:
    storage: SupportsStateStorage
    max_apply_retries: int = 2

    @classmethod
    def from_cosmos(cls, storage: CosmosStorageClient) -> "ArchitectureStateManager":
        return cls(storage=storage)

    def apply_patch(self, patch: StagePatch) -> ApplyPatchResult:
        # 1) Idempotency check.
        existing = self.storage.find_by_idempotency_key(
            session_id=patch.session_id,
            key=patch.idempotency_key,
        )
        if existing is not None:
            existing_hash = existing.get("patch_hash")
            existing_version = existing.get("version")
            if existing_hash and existing_hash != patch.patch_hash:
                return ApplyPatchResult(
                    applied=False,
                    session_id=patch.session_id,
                    stage=patch.stage,
                    reason="idempotency_conflict",
                    current_version=existing_version,
                    patch_base_version=patch.base_version,
                    action="idempotency_key_conflict",
                )

            return ApplyPatchResult(
                applied=True,
                session_id=patch.session_id,
                stage=patch.stage,
                version=existing_version,
                current_version=existing_version,
                patch_base_version=patch.base_version,
                action="idempotent_replay",
            )

        if self._compute_patch_hash(patch.patch) != patch.patch_hash:
            return ApplyPatchResult(
                applied=False,
                session_id=patch.session_id,
                stage=patch.stage,
                reason="invalid_patch_hash",
                patch_base_version=patch.base_version,
                action="rejected",
            )

        if patch.quality_gate_result.status == QualityGateStatus.FAILED:
            return ApplyPatchResult(
                applied=False,
                session_id=patch.session_id,
                stage=patch.stage,
                reason="quality_gate_failed",
                patch_base_version=patch.base_version,
                action="blocked",
            )

        retries = 0
        while True:
            session = self.storage.read_session(patch.session_id)
            if session is None:
                return ApplyPatchResult(
                    applied=False,
                    session_id=patch.session_id,
                    stage=patch.stage,
                    reason="session_not_found",
                    patch_base_version=patch.base_version,
                    action="rejected",
                )

            latest = self.storage.read_latest_artifact(patch.session_id, patch.stage)
            latest_version = latest.version if latest else 0
            if latest_version != patch.base_version:
                return ApplyPatchResult(
                    applied=False,
                    session_id=patch.session_id,
                    stage=patch.stage,
                    reason="version_conflict",
                    current_version=latest_version,
                    patch_base_version=patch.base_version,
                    action="rejected",
                )

            artifact = VersionedArtifact(
                session_id=patch.session_id,
                stage=patch.stage,
                version=patch.target_version,
                stage_run_id=patch.stage_run_id,
                content=patch.patch,
                quality_gate=patch.quality_gate_result,
                claim_ids=[c.claim_id for c in patch.claims],
                evidence_ids=[e.evidence_id for e in patch.evidence_sources],
            )

            try:
                self.storage.upsert_artifact(
                    artifact,
                    idempotency_key=patch.idempotency_key,
                    patch_id=patch.patch_id,
                )
                for claim in patch.claims:
                    self.storage.append_claim(claim)
                for evidence in patch.evidence_sources:
                    self.storage.append_evidence(evidence)

                self._update_session_state(session, patch)
                self.storage.upsert_session(session)

                change_event = ChangeEvent(
                    session_id=patch.session_id,
                    change_type=ChangeType.REQUIREMENT_UPDATED,
                    changed_field=f"artifact.{patch.stage}",
                    old_value_summary=f"v{patch.base_version}",
                    new_value_summary=f"v{patch.target_version}",
                    impacted_stages=[patch.stage],
                )
                self.storage.append_change_event(change_event)

                return ApplyPatchResult(
                    applied=True,
                    session_id=patch.session_id,
                    stage=patch.stage,
                    version=patch.target_version,
                    current_version=patch.target_version,
                    patch_base_version=patch.base_version,
                    action="applied",
                )
            except Exception as exc:
                if self._is_precondition_failed(exc) and retries < self.max_apply_retries:
                    retries += 1
                    continue
                raise

    @staticmethod
    def _update_session_state(session: ArchitectureSession, patch: StagePatch) -> None:
        session.active_version = max(session.active_version, patch.target_version)
        session.current_stage = patch.stage
        session.last_successful_stage = patch.stage
        session.quality_gates[patch.stage] = patch.quality_gate_result
        session.latest_artifact_versions[patch.stage] = patch.target_version

        execution = session.stage_executions.get(patch.stage)
        if execution is None:
            execution = StageExecution(stage=patch.stage)
            session.stage_executions[patch.stage] = execution

        execution.stage_run_id = patch.stage_run_id
        execution.status = StageStatus.COMPLETED
        execution.base_version = patch.base_version
        execution.target_version = patch.target_version
        execution.failure_reason = None

    @staticmethod
    def _compute_patch_hash(patch_payload: dict) -> str:
        canonical = json.dumps(patch_payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _is_precondition_failed(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        if status_code == 412:
            return True
        return "precondition" in str(exc).lower()

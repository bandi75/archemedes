from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.change import ChangeEvent
from archimedes.models.claims import ClaimRecord
from archimedes.models.diffs import ArtifactDiff
from archimedes.models.evidence import EvidenceSource
from archimedes.models.session import ArchitectureSession


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


@dataclass(slots=True)
class InMemoryArchimedesStorage:
    """Local API storage for the MVP backend until Cosmos wiring is enabled."""

    sessions: dict[str, ArchitectureSession] = field(default_factory=dict)
    artifacts: dict[tuple[str, str, int], VersionedArtifact] = field(default_factory=dict)
    claims: dict[str, ClaimRecord] = field(default_factory=dict)
    evidence: dict[str, EvidenceSource] = field(default_factory=dict)
    change_events: list[ChangeEvent] = field(default_factory=list)
    diffs: dict[str, ArtifactDiff] = field(default_factory=dict)
    idempotency: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    def read_session(self, session_id: str) -> ArchitectureSession | None:
        return self.sessions.get(session_id)

    def upsert_session(self, session: ArchitectureSession) -> ArchitectureSession:
        self.sessions[session.session_id] = session
        return session

    def read_latest_artifact(
        self, session_id: str, stage: str
    ) -> VersionedArtifact | None:
        versions = [
            artifact
            for (artifact_session_id, artifact_stage, _), artifact in self.artifacts.items()
            if artifact_session_id == session_id and artifact_stage == _value(stage)
        ]
        if not versions:
            return None
        return max(versions, key=lambda artifact: artifact.version)

    def read_artifact_version(
        self, session_id: str, stage: str, version: int
    ) -> VersionedArtifact | None:
        return self.artifacts.get((session_id, _value(stage), version))

    def find_by_idempotency_key(
        self,
        session_id: str,
        key: str,
    ) -> dict[str, Any] | None:
        return self.idempotency.get((session_id, key))

    def upsert_artifact(
        self,
        artifact: VersionedArtifact,
        *,
        idempotency_key: str | None = None,
        patch_id: str | None = None,
    ) -> VersionedArtifact:
        stage = _value(artifact.stage)
        self.artifacts[(artifact.session_id, stage, artifact.version)] = artifact
        if idempotency_key:
            self.idempotency[(artifact.session_id, idempotency_key)] = {
                "idempotency_key": idempotency_key,
                "patch_id": patch_id,
                "version": artifact.version,
            }
        return artifact

    def append_claim(self, claim: ClaimRecord) -> ClaimRecord:
        self.claims[claim.claim_id] = claim
        return claim

    def update_claim(self, session_id: str, claim_id: str, **updates) -> ClaimRecord | None:
        claim = self.claims.get(claim_id)
        if claim is None or claim.session_id != session_id:
            return None
        updated = claim.model_copy(update=updates)
        self.claims[claim_id] = updated
        return updated

    def append_evidence(self, evidence: EvidenceSource) -> EvidenceSource:
        self.evidence[evidence.evidence_id] = evidence
        return evidence

    def append_change_event(self, event: ChangeEvent) -> ChangeEvent:
        self.change_events.append(event)
        return event

    def read_change_event(self, session_id: str, change_event_id: str) -> ChangeEvent | None:
        for event in self.change_events:
            if event.session_id == session_id and event.change_event_id == change_event_id:
                return event
        return None

    def list_change_events(self, session_id: str) -> list[ChangeEvent]:
        return [event for event in self.change_events if event.session_id == session_id]

    def upsert_diff(self, diff: ArtifactDiff) -> ArtifactDiff:
        self.diffs[diff.diff_id] = diff
        return diff

    def read_diff(self, session_id: str, diff_id: str) -> ArtifactDiff | None:
        diff = self.diffs.get(diff_id)
        if diff is None or diff.session_id != session_id:
            return None
        return diff

    def list_diffs(
        self,
        session_id: str,
        *,
        stage: str | None = None,
    ) -> list[ArtifactDiff]:
        items = [diff for diff in self.diffs.values() if diff.session_id == session_id]
        if stage is not None:
            items = [diff for diff in items if _value(diff.stage) == _value(stage)]
        return items

    def list_claims(
        self,
        session_id: str,
        *,
        stage: str | None = None,
        claim_type: str | None = None,
        requires_user_validation: bool | None = None,
        min_confidence: float | None = None,
    ) -> list[ClaimRecord]:
        items = [claim for claim in self.claims.values() if claim.session_id == session_id]
        if stage is not None:
            items = [claim for claim in items if _value(claim.stage) == stage]
        if claim_type is not None:
            items = [claim for claim in items if _value(claim.type) == claim_type]
        if requires_user_validation is not None:
            items = [
                claim
                for claim in items
                if claim.requires_user_validation is requires_user_validation
            ]
        if min_confidence is not None:
            items = [claim for claim in items if claim.confidence >= min_confidence]
        return items

    def list_sessions(self) -> list[ArchitectureSession]:
        return sorted(self.sessions.values(), key=lambda s: s.created_at, reverse=True)

    def list_evidence(
        self,
        session_id: str,
        *,
        retrieved_via: str | None = None,
        trust_level: str | None = None,
    ) -> list[EvidenceSource]:
        items = [
            evidence
            for evidence in self.evidence.values()
            if evidence.session_id == session_id
        ]
        if retrieved_via is not None:
            items = [
                evidence
                for evidence in items
                if _value(evidence.retrieved_via) == retrieved_via
            ]
        if trust_level is not None:
            items = [
                evidence
                for evidence in items
                if _value(evidence.trust_level) == trust_level
            ]
        return items

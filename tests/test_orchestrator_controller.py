from __future__ import annotations

from archimedes.models.session import ArchitectureSession
from archimedes.orchestrator.controller import StageController
from archimedes.state.state_manager import ArchitectureStateManager


class FakeStorage:
    def __init__(self, session: ArchitectureSession):
        self.session = session
        self.artifacts = {}
        self.idempotency = {}
        self.change_events = []

    def read_session(self, session_id: str):
        if self.session.session_id == session_id:
            return self.session
        return None

    def read_latest_artifact(self, session_id: str, stage: str):
        return self.artifacts.get((session_id, stage))

    def find_by_idempotency_key(self, session_id: str, key: str):
        return self.idempotency.get((session_id, key))

    def upsert_artifact(self, artifact, *, idempotency_key=None, patch_id=None):
        self.artifacts[(artifact.session_id, artifact.stage)] = artifact
        if idempotency_key:
            self.idempotency[(artifact.session_id, idempotency_key)] = {
                "idempotency_key": idempotency_key,
                "patch_hash": getattr(artifact, "patch_hash", None),
                "version": artifact.version,
            }
        return artifact

    def append_claim(self, claim):
        return claim

    def append_evidence(self, evidence):
        return evidence

    def upsert_session(self, session):
        self.session = session
        return session

    def append_change_event(self, event):
        self.change_events.append(event)
        return event


def test_stage_controller_applies_current_stage_and_advances():
    session = ArchitectureSession(business_need="Build fraud detection assistant")
    storage = FakeStorage(session)
    manager = ArchitectureStateManager(storage=storage)
    controller = StageController(state_manager=manager, storage=storage)

    response = controller.process_message(session.session_id, "Need an architecture for fraud detection")

    assert response.stage_status == "completed"
    assert response.current_stage == "intake"
    assert "intake:v1" in response.artifacts_produced[0]
    assert storage.session.current_stage == "requirements_extraction"


def test_stage_controller_detects_requirement_change():
    session = ArchitectureSession(business_need="Build fraud detection assistant")
    storage = FakeStorage(session)
    manager = ArchitectureStateManager(storage=storage)
    controller = StageController(state_manager=manager, storage=storage)

    response = controller.process_message(session.session_id, "Actually make it 100K TPS and multi-region")

    assert response.change_detected is True
    assert response.requires_user_action is True
    assert len(response.impacted_stages) > 0
    assert len(storage.change_events) == 1

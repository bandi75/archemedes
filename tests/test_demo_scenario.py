from __future__ import annotations

from archimedes.models.session import ArchitectureSession
from archimedes.orchestrator.controller import StageController
from archimedes.state.diff_service import ArtifactDiffService
from archimedes.state.state_manager import ArchitectureStateManager
from archimedes.api.storage import InMemoryArchimedesStorage


DEMO_NEED = (
    "Design a real-time fraud detection platform on Azure for a fintech processing "
    "10K TPS with PCI-DSS constraints and 99.95% availability."
)


def test_phase6_demo_scenario_change_rereasons_impacted_artifacts_and_diffs():
    storage = InMemoryArchimedesStorage()
    session = storage.upsert_session(ArchitectureSession(business_need=DEMO_NEED))
    controller = StageController(
        state_manager=ArchitectureStateManager(storage=storage),
        storage=storage,
    )

    # Each gate stage requires "proceed" to advance; non-gate stages (pattern, socratic, audits) chain automatically.
    for message in [
        DEMO_NEED,   # intake (gate)
        "proceed",   # → requirements_extraction (gate)
        "proceed",   # → options_generation (gate; pattern_detection chains automatically first)
        "proceed",   # → adr_generation (gate; socratic + evidence_audit chain automatically first)
        "proceed",   # → hld_generation (gate)
        "proceed",   # → mini_waf_review (gate)
        "proceed",   # → final_evidence_audit (non-gate, completes pipeline)
    ]:
        response = controller.process_message(session.session_id, message)
        assert response.stage_status == "completed", (
            f"Expected completed but got {response.stage_status!r} "
            f"at stage {response.current_stage} for message {message!r}"
        )

    pattern = storage.read_latest_artifact(session.session_id, "pattern_detection")
    options_v1 = storage.read_latest_artifact(session.session_id, "options_generation")
    hld_v1 = storage.read_latest_artifact(session.session_id, "hld_generation")
    final_audit_v1 = storage.read_latest_artifact(session.session_id, "final_evidence_audit")

    assert pattern is not None
    assert options_v1 is not None
    assert isinstance(options_v1.content.get("options"), list)
    assert hld_v1 is not None
    assert final_audit_v1 is not None

    change_response = controller.process_message(
        session.session_id,
        "Actually, make it 100K TPS and multi-region active-active.",
    )

    assert change_response.stage_status == "rereasoned"
    assert change_response.change_detected is True
    assert "intake" in {str(stage) for stage in change_response.stable_stages}

    options_v2 = storage.read_latest_artifact(session.session_id, "options_generation")
    hld_v2 = storage.read_latest_artifact(session.session_id, "hld_generation")
    assert options_v2 is not None
    assert hld_v2 is not None
    # v2 must be a new version produced by re-reasoning.
    assert options_v2.version >= 2
    assert hld_v2.version >= 2

    change_event = storage.list_change_events(session.session_id)[-1]
    diff_service = ArtifactDiffService(storage)
    options_diff = diff_service.generate_diff(
        session.session_id,
        "options_generation",
        1,
        2,
        change_event_id=change_event.change_event_id,
    )
    hld_diff = diff_service.generate_diff(
        session.session_id,
        "hld_generation",
        1,
        2,
        change_event_id=change_event.change_event_id,
    )

    assert options_diff.field_diffs
    assert hld_diff.field_diffs


def test_phase6_demo_variations_do_not_crash():
    variations = [
        "Skip optional clarifications and continue with marked assumptions.",
        "I disagree with the recommendation; choose the AKS option instead.",
        "Quality gate warning acknowledged; continue with override rationale.",
    ]

    for variation in variations:
        storage = InMemoryArchimedesStorage()
        session = storage.upsert_session(ArchitectureSession(business_need=DEMO_NEED))
        controller = StageController(
            state_manager=ArchitectureStateManager(storage=storage),
            storage=storage,
        )

        first = controller.process_message(session.session_id, DEMO_NEED)
        second = controller.process_message(session.session_id, variation)

        assert first.stage_status == "completed"
        assert second.stage_status in {"completed", "rereasoned", "refined"}
        assert storage.read_session(session.session_id) is not None

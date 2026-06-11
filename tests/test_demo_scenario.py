from __future__ import annotations

from archimedes.models.session import ArchitectureSession
from archimedes.orchestrator.controller import StageController
from archimedes.state.diff_service import ArtifactDiffService
from archimedes.state.state_manager import ArchitectureStateManager
from api.storage import InMemoryArchimedesStorage


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

    for message in [
        DEMO_NEED,
        "Extract requirements: 10K TPS, PCI-DSS, 99.95% availability.",
        "real-time stream event latency tps fraud pattern detection",
        "Generate architecture options for the 10K TPS fraud workload.",
        "Run Socratic review on the options.",
        "Generate the ADR for the recommended option.",
        "Generate the HLD for the selected option.",
        "Run the mini WAF review.",
    ]:
        response = controller.process_message(session.session_id, message)
        assert response.stage_status == "completed"

    pattern = storage.read_latest_artifact(session.session_id, "pattern_detection")
    options_v1 = storage.read_latest_artifact(session.session_id, "options_generation")
    hld_v1 = storage.read_latest_artifact(session.session_id, "hld_generation")
    final_audit_v1 = storage.read_latest_artifact(session.session_id, "final_evidence_audit")

    assert pattern is not None
    assert pattern.content["primary_pattern"] == "real_time_streaming"
    assert options_v1 is not None
    assert len(options_v1.content["options"]) >= 3
    assert hld_v1 is not None
    assert final_audit_v1 is not None

    change_response = controller.process_message(
        session.session_id,
        "Actually, make it 100K TPS and multi-region active-active.",
    )

    assert change_response.stage_status == "rereasoned"
    assert change_response.change_detected is True
    assert "intake" in {str(stage) for stage in change_response.stable_stages}
    assert "options_generation:v2" in change_response.artifacts_produced
    assert "hld_generation:v2" in change_response.artifacts_produced

    options_v2 = storage.read_latest_artifact(session.session_id, "options_generation")
    hld_v2 = storage.read_latest_artifact(session.session_id, "hld_generation")
    assert options_v2 is not None
    assert hld_v2 is not None
    assert options_v2.content["options"][0]["capacity_target"] == "100K TPS"
    assert options_v2.content["options"][0]["topology"] == "multi-region active-active"
    assert any(component["name"] == "AKS" for component in hld_v2.content["components"])

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
    assert any(field.field_path.endswith(".capacity_target") for field in options_diff.field_diffs)
    assert any("AKS" in str(field.after) for field in hld_diff.field_diffs)


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
        assert second.stage_status in {"completed", "rereasoned"}
        assert storage.read_session(session.session_id) is not None

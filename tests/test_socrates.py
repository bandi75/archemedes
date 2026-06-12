from __future__ import annotations

import asyncio

import pytest

from archimedes.models.enums import PersonaName, QualityGateStatus, SocratesDepth, StageName
from archimedes.models.socrates import SocratesReviewContext
from archimedes.socrates.workflow import build_socrates_workflow


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _context(depth: SocratesDepth = SocratesDepth.STANDARD) -> SocratesReviewContext:
    return SocratesReviewContext(
        session_id="session_socrates_test",
        stage_run_id="stage_run_socrates_1",
        base_version=0,
        target_version=1,
        depth=depth,
        business_need={
            "raw_input": (
                "Design a real-time fraud detection platform on Azure for a fintech "
                "processing 10K TPS with PCI-DSS constraints and 99.95% availability."
            ),
            "domain": "fintech",
        },
        requirements_summary={
            "functional": ["Score transactions in near real time"],
            "non_functional": ["10K TPS", "99.95% availability"],
            "constraints": ["PCI-DSS"],
            "assumptions": ["Team can operate streaming services"],
        },
        architecture_options=[
            {
                "option_id": "OPT-A",
                "name": "Event Hubs and Stream Analytics",
                "summary": "Managed streaming ingestion and scoring path.",
            },
            {
                "option_id": "OPT-B",
                "name": "AKS stream processors",
                "summary": "Custom streaming workers on Kubernetes.",
            },
            {
                "option_id": "OPT-C",
                "name": "Serverless event processing",
                "summary": "Function-driven event processing for faster delivery.",
            },
        ],
        evaluation_criteria=["reliability", "security", "cost", "delivery"],
    )


def test_build_standard_workflow_registers_dispatcher_five_personas_and_synthesizer():
    workflow = build_socrates_workflow("standard")

    assert workflow.depth == SocratesDepth.STANDARD
    assert len(workflow.persona_executors) == 5
    assert [executor.persona for executor in workflow.persona_executors] == [
        PersonaName.DEVILS_ADVOCATE,
        PersonaName.SRE_OPS_LEAD,
        PersonaName.SECURITY_ARCHITECT,
        PersonaName.FINOPS_LEAD,
        PersonaName.DELIVERY_LEAD,
    ]
    assert workflow.dispatcher.recipients == [executor.persona.value for executor in workflow.persona_executors]


def test_build_light_and_deep_workflows_use_expected_depth_personas():
    light = build_socrates_workflow("light")
    deep = build_socrates_workflow("deep")

    assert len(light.persona_executors) == 3
    assert len(deep.persona_executors) == 7
    assert deep.include_cross_examiner is True


def test_invalid_depth_raises_validation_error():
    with pytest.raises(ValueError):
        build_socrates_workflow("extreme")


def test_socrates_standard_workflow_produces_review_with_synthesis():
    workflow = build_socrates_workflow("standard")
    review = asyncio.run(workflow.run(_context()))

    assert review.session_id == "session_socrates_test"
    assert review.stage_run_id == "stage_run_socrates_1"
    assert len(review.persona_analyses) == 5
    assert review.synthesis.recommended_option_id == "OPT-A"
    assert review.synthesis.ranked_option_ids == ["OPT-A", "OPT-B", "OPT-C"]
    assert 0 <= review.synthesis.confidence <= 1
    assert review.synthesis.blind_spots
    assert review.synthesis.premortem_scenarios
    assert review.quality_gate.status == QualityGateStatus.PASSED


def test_socrates_review_can_be_wrapped_as_stage_patch():
    workflow = build_socrates_workflow("standard")
    review = workflow.run_sync(_context())
    patch = workflow.build_stage_patch(review, base_version=0)

    assert patch.stage == StageName.SOCRATIC_REVIEW
    assert patch.base_version == 0
    assert patch.target_version == 1
    assert patch.patch["socratic_review"]["synthesis"]["recommended_option_id"] == "OPT-A"
    assert patch.quality_gate_result.status == QualityGateStatus.PASSED


@pytest.mark.anyio
async def test_socrates_run_sync_can_be_called_inside_running_event_loop():
    workflow = build_socrates_workflow("standard")

    review = workflow.run_sync(_context())

    assert review.synthesis.recommended_option_id == "OPT-A"

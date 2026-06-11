from __future__ import annotations

import pytest

from archimedes.models.enums import QualityGateStatus, StageName
from archimedes.state.quality_gates import GATE_DEFINITIONS, evaluate_quality_gate


@pytest.mark.parametrize(
    "stage",
    [
        StageName.REQUIREMENTS_EXTRACTION,
        StageName.PATTERN_DETECTION,
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.EVIDENCE_AUDIT_CHECKPOINT,
        StageName.FINAL_EVIDENCE_AUDIT,
    ],
)
def test_evaluate_quality_gate_passed_for_all_stages(stage: StageName):
    spec = GATE_DEFINITIONS[stage.value]
    inputs = {
        check_id: True
        for check_id, _ in (spec["blocking"] + spec["warning"])
    }

    result = evaluate_quality_gate(stage, inputs)

    assert result.status == QualityGateStatus.PASSED
    assert result.blocking_failures == []
    assert result.warnings == []


def test_evaluate_quality_gate_failed_when_blocking_check_missing():
    result = evaluate_quality_gate("requirements", {"security_defined": True})

    assert result.status == QualityGateStatus.FAILED
    assert result.user_override_allowed is False
    assert any("Scale target" in failure for failure in result.blocking_failures)


def test_evaluate_quality_gate_passed_with_warnings_when_only_warning_checks_missing():
    spec = GATE_DEFINITIONS[StageName.REQUIREMENTS_EXTRACTION.value]
    inputs = {check_id: True for check_id, _ in spec["blocking"]}

    result = evaluate_quality_gate("requirements", inputs)

    assert result.status == QualityGateStatus.PASSED_WITH_WARNINGS
    assert result.blocking_failures == []
    assert result.warnings


def test_evaluate_quality_gate_supports_dict_check_payload_with_message():
    result = evaluate_quality_gate(
        "hld",
        {
            "components_shown": {"passed": True},
            "data_flow_shown": {"passed": True},
            "trust_boundaries_shown": {"passed": False, "message": "Trust zones not labeled"},
            "mermaid_render_check_passed": {"passed": True},
            "network_zones_defined": {"passed": True},
            "identity_flow_defined": {"passed": True},
            "observability_flow_defined": {"passed": True},
        },
    )

    assert result.status == QualityGateStatus.PASSED_WITH_WARNINGS
    assert "Trust zones not labeled" in result.warnings


def test_evaluate_quality_gate_alias_waf_review_maps_to_mini_waf_review():
    result = evaluate_quality_gate(
        "waf_review",
        {
            "reliability_reviewed": True,
            "security_reviewed": True,
            "cost_reviewed": True,
            "ops_reviewed": True,
            "performance_reviewed": True,
            "critical_findings_prioritized": True,
            "mitigations_present": True,
        },
    )

    assert result.status == QualityGateStatus.PASSED


def test_evaluate_quality_gate_unknown_stage_raises():
    with pytest.raises(ValueError):
        evaluate_quality_gate("unknown_stage", {})

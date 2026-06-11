from __future__ import annotations

from archimedes.models.enums import StageName
from archimedes.orchestrator.dependency_engine import (
    compute_change_impact,
    detect_requirement_changes,
)


def test_detect_requirement_changes_handles_multi_field_demo_change():
    changes = detect_requirement_changes(
        "Actually, make it 100K TPS and multi-region active-active."
    )

    assert {change.requirement_type for change in changes} >= {"scale", "region"}


def test_compute_change_impact_returns_impacted_and_stable_stages():
    changes = detect_requirement_changes(
        "Actually, make it 100K TPS and multi-region active-active."
    )
    impact = compute_change_impact(changes, session_id="session_1", change_event_id="change_1")

    assert impact.session_id == "session_1"
    assert StageName.OPTIONS_GENERATION in impact.impacted_stages
    assert StageName.SOCRATIC_REVIEW in impact.impacted_stages
    assert StageName.ADR_GENERATION in impact.impacted_stages
    assert StageName.HLD_GENERATION in impact.impacted_stages
    assert StageName.MINI_WAF_REVIEW in impact.impacted_stages
    assert StageName.FINAL_EVIDENCE_AUDIT in impact.impacted_stages
    assert StageName.INTAKE in impact.stable_stages
    assert StageName.REQUIREMENTS_EXTRACTION in impact.stable_stages
    assert impact.reason_by_stage[StageName.HLD_GENERATION]

from __future__ import annotations

from typing import Any

from archimedes.models.enums import QualityGateStatus, StageName
from archimedes.models.quality_gates import QualityGateCheck, QualityGateResult


GateSpec = dict[str, list[tuple[str, str]]]


GATE_DEFINITIONS: dict[str, GateSpec] = {
    StageName.REQUIREMENTS_EXTRACTION.value: {
        "blocking": [
            ("scale_defined", "Scale target must be defined."),
            ("security_defined", "Security requirements must be identified."),
        ],
        "warning": [
            ("latency_defined", "Latency SLA is not defined."),
            ("availability_defined", "Availability target is not defined."),
            ("compliance_defined", "Compliance frameworks are not specified."),
            ("data_residency_defined", "Data residency is not checked."),
            (
                "integration_context_defined",
                "Upstream/downstream integration context is unclear.",
            ),
            ("operational_constraints_defined", "Operational constraints are missing."),
        ],
    },
    StageName.PATTERN_DETECTION.value: {
        "blocking": [
            (
                "primary_pattern_identified",
                "At least one primary architecture pattern must be identified.",
            )
        ],
        "warning": [
            ("multiple_patterns_detected", "Multiple patterns may broaden options."),
            ("pattern_confidence_low", "Pattern confidence is below threshold."),
            (
                "pattern_specific_nfrs_inferred",
                "Pattern-specific inferred NFRs need user validation.",
            ),
        ],
    },
    StageName.OPTIONS_GENERATION.value: {
        "blocking": [
            ("min_viable_options", "At least two viable options must be generated."),
            (
                "rejected_option",
                "At least one option must be explicitly rejected with reason.",
            ),
        ],
        "warning": [
            ("tradeoffs_scored", "Trade-off scoring is incomplete."),
            ("cost_assumptions_present", "Cost assumptions are missing or weak."),
            ("risk_summary_present", "Risk summary is missing."),
            ("evidence_links_present", "Some option claims lack evidence links."),
        ],
    },
    StageName.SOCRATIC_REVIEW.value: {
        "blocking": [
            ("blind_spots_generated", "Blind spots must be identified."),
            ("premortem_generated", "Pre-mortem scenarios must be generated."),
        ],
        "warning": [
            (
                "min_personas_responded",
                "Fewer than expected Socratic personas responded.",
            ),
            ("confidence_scored", "Confidence score is missing."),
            ("low_confidence", "Confidence score is below threshold."),
            ("assumptions_listed", "Key assumptions are missing."),
            (
                "recommended_option_identified",
                "Synthesizer did not clearly identify a preferred option.",
            ),
        ],
    },
    StageName.ADR_GENERATION.value: {
        "blocking": [
            ("decision_captured", "Decision must be clearly stated."),
            (
                "selected_option_valid",
                "Selected option must reference an existing option.",
            ),
        ],
        "warning": [
            ("alternatives_listed", "Rejected alternatives are incomplete."),
            ("consequences_documented", "Consequences are incomplete."),
            ("assumptions_documented", "Assumptions are not captured."),
            (
                "socrates_findings_reflected",
                "Socrates concerns are not reflected in ADR rationale.",
            ),
        ],
    },
    StageName.HLD_GENERATION.value: {
        "blocking": [
            ("components_shown", "All major components must appear in the HLD."),
            ("data_flow_shown", "Data flow paths must be documented."),
        ],
        "warning": [
            ("trust_boundaries_shown", "Trust boundaries are not marked."),
            (
                "mermaid_render_check_passed",
                "Mermaid render checks failed or returned warnings.",
            ),
            ("network_zones_defined", "Network zones are missing."),
            ("identity_flow_defined", "Identity flow is missing."),
            (
                "observability_flow_defined",
                "Logging/tracing/metrics flow is unclear.",
            ),
        ],
    },
    StageName.MINI_WAF_REVIEW.value: {
        "blocking": [
            ("reliability_reviewed", "Reliability pillar must be reviewed."),
            ("security_reviewed", "Security pillar must be reviewed."),
        ],
        "warning": [
            ("cost_reviewed", "Cost optimization pillar is missing."),
            ("ops_reviewed", "Operational excellence pillar is missing."),
            ("performance_reviewed", "Performance efficiency pillar is missing."),
            (
                "critical_findings_prioritized",
                "Findings are not prioritized by severity.",
            ),
            ("mitigations_present", "Mitigations are missing."),
        ],
    },
}


STAGE_ALIASES = {
    "requirements": StageName.REQUIREMENTS_EXTRACTION.value,
    "pattern_detection": StageName.PATTERN_DETECTION.value,
    "options": StageName.OPTIONS_GENERATION.value,
    "options_generation": StageName.OPTIONS_GENERATION.value,
    "socratic": StageName.SOCRATIC_REVIEW.value,
    "socratic_review": StageName.SOCRATIC_REVIEW.value,
    "adr": StageName.ADR_GENERATION.value,
    "adr_generation": StageName.ADR_GENERATION.value,
    "hld": StageName.HLD_GENERATION.value,
    "hld_generation": StageName.HLD_GENERATION.value,
    "waf_review": StageName.MINI_WAF_REVIEW.value,
    "mini_waf_review": StageName.MINI_WAF_REVIEW.value,
}


def evaluate_quality_gate(stage: StageName | str, checklist_results: dict[str, Any]) -> QualityGateResult:
    normalized_stage = _normalize_stage(stage)
    spec = GATE_DEFINITIONS.get(normalized_stage)
    if spec is None:
        raise ValueError(f"Unsupported stage for quality gate evaluation: {stage}")

    checks: list[QualityGateCheck] = []
    blocking_failures: list[str] = []
    warnings: list[str] = []

    for check_id, description in spec["blocking"]:
        passed, message = _extract_check(checklist_results.get(check_id))
        checks.append(
            QualityGateCheck(
                check_id=check_id,
                description=description,
                passed=passed,
                severity="blocking",
                message=message,
            )
        )
        if not passed:
            blocking_failures.append(message or description)

    for check_id, description in spec["warning"]:
        passed, message = _extract_check(checklist_results.get(check_id))
        checks.append(
            QualityGateCheck(
                check_id=check_id,
                description=description,
                passed=passed,
                severity="warning",
                message=message,
            )
        )
        if not passed:
            warnings.append(message or description)

    if blocking_failures:
        return QualityGateResult(
            status=QualityGateStatus.FAILED,
            blocking_failures=blocking_failures,
            warnings=warnings,
            checks=checks,
            user_override_allowed=False,
        )

    if warnings:
        return QualityGateResult(
            status=QualityGateStatus.PASSED_WITH_WARNINGS,
            warnings=warnings,
            checks=checks,
            user_override_allowed=True,
        )

    return QualityGateResult(
        status=QualityGateStatus.PASSED,
        checks=checks,
        user_override_allowed=True,
    )


def _normalize_stage(stage: StageName | str) -> str:
    stage_value = stage.value if isinstance(stage, StageName) else str(stage)
    return STAGE_ALIASES.get(stage_value, stage_value)


def _extract_check(value: Any) -> tuple[bool, str | None]:
    if isinstance(value, dict):
        passed = bool(value.get("passed", False))
        message = value.get("message")
        return passed, message
    if isinstance(value, bool):
        return value, None
    return False, None

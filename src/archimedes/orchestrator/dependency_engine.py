from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from archimedes.models.change import DependencyImpactResult
from archimedes.models.enums import StageName
from archimedes.models.session import DEPENDENCY_RULES, DependencyMap


PIPELINE_STAGE_ORDER: list[StageName] = [
    StageName.INTAKE,
    StageName.REQUIREMENTS_EXTRACTION,
    StageName.PATTERN_DETECTION,
    StageName.OPTIONS_GENERATION,
    StageName.SOCRATIC_REVIEW,
    StageName.EVIDENCE_AUDIT_CHECKPOINT,
    StageName.ADR_GENERATION,
    StageName.HLD_GENERATION,
    StageName.MINI_WAF_REVIEW,
    StageName.FINAL_EVIDENCE_AUDIT,
]


@dataclass(frozen=True, slots=True)
class ChangeSpec:
    requirement_type: str
    changed_field: str
    new_value: str


_TRIGGER_RE = re.compile(
    r"\b(actually|change|make\s+it|update|increase|decrease|add|remove|switch|instead)\b",
    re.IGNORECASE,
)

_CHANGE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("scale", re.compile(r"\b(\d+\s*k\s*tps|\d+\s*tps|throughput|qps|rps|scale)\b", re.IGNORECASE)),
    ("region", re.compile(r"\b(multi[- ]region|single[- ]region|active[- ]active|geo|region)\b", re.IGNORECASE)),
    ("availability", re.compile(r"\b(availability|uptime|sla|dr|disaster recovery|failover)\b", re.IGNORECASE)),
    ("compliance", re.compile(r"\b(pci[- ]?dss|hipaa|gdpr|sox|compliance)\b", re.IGNORECASE)),
    ("security", re.compile(r"\b(security|zero trust|encryption|threat|private endpoint)\b", re.IGNORECASE)),
    ("budget", re.compile(r"\b(budget|cost|cheaper|price|finops)\b", re.IGNORECASE)),
    ("latency", re.compile(r"\b(latency|p95|p99|response time|real[- ]time)\b", re.IGNORECASE)),
    ("timeline", re.compile(r"\b(timeline|deadline|delivery|mvp|launch)\b", re.IGNORECASE)),
    ("selected_option", re.compile(r"\b(option|recommendation|choose|selected)\b", re.IGNORECASE)),
    ("functional_requirement", re.compile(r"\b(requirement|feature|capability|workflow)\b", re.IGNORECASE)),
)

_REASON_BY_CATEGORY: dict[str, str] = {
    "business_need": "Business need changes invalidate requirement framing and downstream reasoning.",
    "functional_requirement": "Functional requirement changes may alter options and decisions.",
    "scale": "Scale changes alter capacity, topology, resilience, cost, and risk analysis.",
    "latency": "Latency target changes affect option tradeoffs and architecture decisions.",
    "availability": "Availability changes affect resiliency topology, WAF review, and decisions.",
    "security": "Security changes affect requirements, options, WAF review, and evidence.",
    "compliance": "Compliance changes affect requirements, decisions, controls, and evidence.",
    "region": "Region changes affect topology, data flow, resiliency, and cost.",
    "budget": "Budget changes affect options, tradeoffs, ADR, and final audit.",
    "timeline": "Timeline changes affect tradeoff review and decision rationale.",
    "selected_option": "Selected option changes affect decision, design, and downstream reviews.",
}


def detect_requirement_changes(user_message: str) -> list[ChangeSpec]:
    """Detect deterministic MVP requirement changes from a user message."""

    text = user_message.strip()
    if not text or not _TRIGGER_RE.search(text):
        return []

    changes: list[ChangeSpec] = []
    seen: set[str] = set()
    for requirement_type, pattern in _CHANGE_PATTERNS:
        if requirement_type in seen or not pattern.search(text):
            continue
        seen.add(requirement_type)
        changes.append(
            ChangeSpec(
                requirement_type=requirement_type,
                changed_field=requirement_type,
                new_value=text,
            )
        )
    return changes


def compute_change_impact(
    changed_requirement: str | ChangeSpec | Iterable[str | ChangeSpec],
    dependency_map: DependencyMap | None = None,
    *,
    session_id: str = "preview",
    change_event_id: str = "preview",
) -> DependencyImpactResult:
    """Return impacted and stable stages for one or more requirement changes."""

    rules = dependency_map or DEPENDENCY_RULES
    categories = _normalize_changed_requirement(changed_requirement)
    impacted_set: set[StageName] = set()
    reasons: dict[StageName, str] = {}

    for category in categories:
        stages = rules.get(category, rules.get("functional_requirement", []))
        reason = _REASON_BY_CATEGORY.get(category, "Requirement change affects downstream reasoning.")
        for stage in stages:
            normalized_stage = _to_stage(stage)
            impacted_set.add(normalized_stage)
            reasons.setdefault(normalized_stage, reason)

    impacted = [stage for stage in PIPELINE_STAGE_ORDER if stage in impacted_set]
    stable = [stage for stage in PIPELINE_STAGE_ORDER if stage not in impacted_set]
    return DependencyImpactResult(
        session_id=session_id,
        change_event_id=change_event_id,
        impacted_stages=impacted,
        stable_stages=stable,
        reason_by_stage=reasons,
        rerun_required=bool(impacted),
    )


def _normalize_changed_requirement(
    changed_requirement: str | ChangeSpec | Iterable[str | ChangeSpec],
) -> list[str]:
    if isinstance(changed_requirement, str):
        return [changed_requirement]
    if isinstance(changed_requirement, ChangeSpec):
        return [changed_requirement.requirement_type]

    categories: list[str] = []
    for item in changed_requirement:
        if isinstance(item, ChangeSpec):
            categories.append(item.requirement_type)
        else:
            categories.append(str(item))
    return categories


def _to_stage(stage: StageName | str) -> StageName:
    if isinstance(stage, StageName):
        return stage
    return StageName(str(stage))

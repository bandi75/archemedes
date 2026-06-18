from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from archimedes.models.enums import StageName

from api.deps import get_storage
from api.errors import api_error
from api.routers.events import build_session_events
from api.storage import InMemoryArchimedesStorage


router = APIRouter(prefix="/sessions/{session_id}", tags=["frontend-views"])


STAGE_LABELS = {
    "intake": "Intake",
    "requirements_extraction": "Requirements",
    "pattern_detection": "Pattern Detection",
    "options_generation": "Options",
    "socratic_review": "Socratic Review",
    "evidence_audit_checkpoint": "Evidence Checkpoint",
    "adr_generation": "ADR",
    "hld_generation": "HLD",
    "mini_waf_review": "Mini WAF Review",
    "final_evidence_audit": "Final Evidence Audit",
    "rereasoning": "Re-Reasoning",
}


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return str(value)


def _require_session(storage: InMemoryArchimedesStorage, session_id: str):
    session = storage.read_session(session_id)
    if session is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")
    return session


def _artifact_summary(artifact: Any | None) -> dict[str, Any] | None:
    if artifact is None:
        return None
    content = artifact.content or {}
    return {
        "artifact_id": artifact.artifact_id,
        "stage": _value(artifact.stage),
        "version": artifact.version,
        "title": content.get("title") or content.get("summary") or STAGE_LABELS.get(_value(artifact.stage), _value(artifact.stage)),
        "summary": content.get("summary") or content.get("decision") or content.get("status") or "Artifact generated.",
        "content_type": artifact.content_type,
        "quality_gate": artifact.quality_gate.model_dump(mode="json"),
        "claim_count": len(artifact.claim_ids),
        "evidence_count": len(artifact.evidence_ids),
        "created_at": _iso(artifact.created_at),
    }


def _latest_artifacts(storage: InMemoryArchimedesStorage, session_id: str) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for stage in StageName:
        artifact = storage.read_latest_artifact(session_id, stage.value)
        if artifact is not None:
            artifacts[stage.value] = artifact
    return artifacts


def _stage_rows(storage: InMemoryArchimedesStorage, session: Any) -> list[dict[str, Any]]:
    rows = []
    for stage in StageName:
        execution = session.stage_executions.get(stage)
        artifact = storage.read_latest_artifact(session.session_id, stage.value)
        gate = session.quality_gates.get(stage)
        rows.append(
            {
                "stage": stage.value,
                "label": STAGE_LABELS.get(stage.value, stage.value),
                "status": _value(execution.status) if execution else "pending",
                "stage_run_id": execution.stage_run_id if execution else None,
                "quality_gate": gate.model_dump(mode="json") if gate else None,
                "artifact_version": artifact.version if artifact else None,
                "summary": _artifact_summary(artifact)["summary"] if artifact else "Awaiting stage output.",
            }
        )
    return rows


@router.get("/overview")
async def get_session_overview_view(
    session_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    session = _require_session(storage, session_id)
    claims = storage.list_claims(session_id)
    evidence = storage.list_evidence(session_id)
    artifacts = _latest_artifacts(storage, session_id)
    completed = sum(
        1 for execution in session.stage_executions.values() if _value(execution.status) == "completed"
    )
    return {
        "session": {
            "session_id": session.session_id,
            "title": session.title or "Untitled architecture session",
            "business_need": session.business_need,
            "current_stage": _value(session.current_stage),
            "created_at": _iso(session.created_at),
            "updated_at": _iso(session.updated_at),
        },
        "metrics": {
            "completed_stages": completed,
            "total_stages": len(StageName),
            "artifact_count": len(artifacts),
            "claim_count": len(claims),
            "evidence_count": len(evidence),
            "open_assumptions": sum(1 for claim in claims if claim.requires_user_validation and claim.validated_accepted is None),
        },
        "source_artifact_versions": {
            stage: artifact.version for stage, artifact in artifacts.items()
        },
        "warnings": [],
    }


@router.get("/pipeline/view")
async def get_pipeline_view(
    session_id: str,
    include_events: bool = Query(default=True),
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    session = _require_session(storage, session_id)
    stages = _stage_rows(storage, session)
    current_stage = _value(session.current_stage)
    return {
        "session_id": session_id,
        "current_stage": current_stage,
        "stages": stages,
        "selected_stage": next((stage for stage in stages if stage["stage"] == current_stage), stages[0]),
        "recent_events": build_session_events(storage, session_id)[-20:] if include_events else [],
        "last_updated_at": _iso(session.updated_at),
    }


@router.get("/socrates/view")
async def get_socrates_view(
    session_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    _require_session(storage, session_id)
    artifact = storage.read_latest_artifact(session_id, StageName.SOCRATIC_REVIEW.value)
    content = artifact.content if artifact else {}
    personas = content.get("persona_findings") or content.get("personas") or []
    if isinstance(personas, dict):
        personas = list(personas.values())
    return {
        "session_id": session_id,
        "decision_under_review": content.get("decision_under_review")
        or {"title": "Architecture option under review", "summary": content.get("summary", "Awaiting Socrates output.")},
        "synthesis": content.get("synthesis")
        or {
            "recommended_decision": content.get("recommended_decision", "Awaiting synthesizer recommendation."),
            "confidence": content.get("confidence_score", 0),
            "blind_spots": content.get("blind_spots", []),
            "premortem": content.get("premortem", content.get("pre_mortem", [])),
        },
        "personas": personas,
        "artifact": _artifact_summary(artifact),
        "source_refs": [artifact.artifact_id] if artifact else [],
    }


@router.get("/evidence/view")
async def get_evidence_view(
    session_id: str,
    selected_claim_id: str | None = None,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    _require_session(storage, session_id)
    claims = storage.list_claims(session_id)
    evidence = storage.list_evidence(session_id)
    by_trust = Counter(_value(source.trust_level) for source in evidence)
    selected = next((claim for claim in claims if claim.claim_id == selected_claim_id), None)
    if selected is None and claims:
        selected = claims[0]
    return {
        "session_id": session_id,
        "coverage": {
            "total_claims": len(claims),
            "claims_with_evidence": sum(1 for claim in claims if claim.evidence_ids),
            "evidence_sources": len(evidence),
            "trust_breakdown": dict(by_trust),
            "open_assumptions": sum(1 for claim in claims if claim.requires_user_validation and claim.validated_accepted is None),
        },
        "claims": [claim.model_dump(mode="json") for claim in claims],
        "evidence": [source.model_dump(mode="json") for source in evidence],
        "selected_claim": selected.model_dump(mode="json") if selected else None,
    }


@router.get("/artifacts/package-view")
async def get_artifact_package_view(
    session_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    _require_session(storage, session_id)
    package_stages = [
        StageName.REQUIREMENTS_EXTRACTION,
        StageName.OPTIONS_GENERATION,
        StageName.SOCRATIC_REVIEW,
        StageName.ADR_GENERATION,
        StageName.HLD_GENERATION,
        StageName.MINI_WAF_REVIEW,
        StageName.FINAL_EVIDENCE_AUDIT,
    ]
    artifacts = []
    for stage in package_stages:
        artifact = storage.read_latest_artifact(session_id, stage.value)
        summary = _artifact_summary(artifact)
        artifacts.append(
            summary
            or {
                "stage": stage.value,
                "label": STAGE_LABELS[stage.value],
                "version": None,
                "summary": "Awaiting artifact.",
                "render_status": "pending",
                "quality_gate": None,
            }
        )
    return {
        "session_id": session_id,
        "package_status": "ready" if any(item.get("version") for item in artifacts) else "empty",
        "artifacts": artifacts,
        "render_status": {"status": "passed", "warnings": []},
        "warnings": [],
    }


@router.get("/changes/{change_event_id}/impact-view")
async def get_change_impact_view(
    session_id: str,
    change_event_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    _require_session(storage, session_id)
    event = storage.read_change_event(session_id, change_event_id)
    if event is None:
        raise api_error(404, f"Change event not found: {change_event_id}", "change_not_found")
    diffs = storage.list_diffs(session_id)
    related_diffs = [
        diff for diff in diffs if getattr(diff, "change_event_id", None) == change_event_id
    ]
    return {
        "session_id": session_id,
        "change_event": event.model_dump(mode="json"),
        "impact": {
            "impacted_stages": [_value(stage) for stage in event.impacted_stages],
            "stable_stages": [_value(stage) for stage in event.stable_stages],
            "ordered_stages": [_value(stage) for stage in event.impacted_stages],
        },
        "rerun_plan": [
            {
                "stage": _value(stage),
                "label": STAGE_LABELS.get(_value(stage), _value(stage)),
                "status": "ready_to_rerun",
            }
            for stage in event.impacted_stages
        ],
        "diffs": [diff.model_dump(mode="json") for diff in related_diffs],
    }

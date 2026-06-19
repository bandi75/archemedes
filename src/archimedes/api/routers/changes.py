from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from archimedes.models.change import ChangeEvent, DependencyImpactResult
from archimedes.models.enums import ChangeType
from archimedes.orchestrator.controller import StageController
from archimedes.orchestrator.dependency_engine import (
    ChangeSpec,
    compute_change_impact,
    detect_requirement_changes,
)

from archimedes.api.deps import get_stage_controller, get_storage
from archimedes.api.errors import api_error
from archimedes.api.storage import InMemoryArchimedesStorage


router = APIRouter(prefix="/sessions/{session_id}/changes", tags=["changes"])


class PreviewImpactRequest(BaseModel):
    user_message: str | None = Field(default=None, min_length=1)
    changed_field: str | None = Field(default=None, min_length=1)
    new_value_summary: str | None = Field(default=None, min_length=1)


class SubmitChangeRequest(BaseModel):
    change_type: ChangeType = ChangeType.REQUIREMENT_MODIFIED
    changed_field: str = Field(min_length=1)
    old_value_summary: str | None = None
    new_value_summary: str = Field(min_length=1)
    user_message: str | None = None


class RereasonRequest(BaseModel):
    generate_diffs: bool = True


class RereasonResponse(BaseModel):
    change_event: ChangeEvent
    artifacts_produced: list[str]
    diffs: list[Any] = Field(default_factory=list)


@router.post("/preview-impact")
async def preview_impact(
    session_id: str,
    request: PreviewImpactRequest,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> DependencyImpactResult:
    session = storage.read_session(session_id)
    if session is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")

    changes = _changes_from_preview_request(request)
    return compute_change_impact(
        changes,
        session.dependency_map,
        session_id=session_id,
        change_event_id="preview",
    )


@router.post("")
async def submit_change(
    session_id: str,
    request: SubmitChangeRequest,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ChangeEvent:
    session = storage.read_session(session_id)
    if session is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")

    changes = detect_requirement_changes(request.user_message or request.new_value_summary)
    if not changes:
        changes = [
            ChangeSpec(
                requirement_type=request.changed_field,
                changed_field=request.changed_field,
                new_value=request.new_value_summary,
            )
        ]
    event = ChangeEvent(
        session_id=session_id,
        change_type=request.change_type,
        changed_field=request.changed_field,
        old_value_summary=request.old_value_summary,
        new_value_summary=request.new_value_summary,
        user_message=request.user_message,
    )
    impact = compute_change_impact(
        changes,
        session.dependency_map,
        session_id=session_id,
        change_event_id=event.change_event_id,
    )
    event.impacted_stages = impact.impacted_stages
    event.stable_stages = impact.stable_stages
    return storage.append_change_event(event)


@router.get("/{change_event_id}")
async def get_change(
    session_id: str,
    change_event_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ChangeEvent:
    event = storage.read_change_event(session_id, change_event_id)
    if event is None:
        raise api_error(404, f"Change event not found: {change_event_id}", "change_not_found")
    return event


@router.post("/{change_event_id}/rereason")
async def rereason_change(
    session_id: str,
    change_event_id: str,
    request: RereasonRequest,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
    controller: StageController = Depends(get_stage_controller),
) -> RereasonResponse:
    event = storage.read_change_event(session_id, change_event_id)
    if event is None:
        raise api_error(404, f"Change event not found: {change_event_id}", "change_not_found")

    before_versions = _stage_versions(storage, session_id, event.impacted_stages)
    artifacts = controller.rerun_impacted_stages(
        session_id=session_id,
        user_message=event.user_message or event.new_value_summary or event.changed_field,
        impacted_stages=event.impacted_stages,
        change_event_id=event.change_event_id,
    )

    diffs = []
    if request.generate_diffs:
        from archimedes.state.diff_service import ArtifactDiffService

        service = ArtifactDiffService(storage)
        after_versions = _stage_versions(storage, session_id, event.impacted_stages)
        for stage, before_version in before_versions.items():
            after_version = after_versions.get(stage)
            if before_version and after_version and after_version > before_version:
                diffs.append(
                    service.generate_diff(
                        session_id,
                        stage,
                        before_version,
                        after_version,
                        change_event_id=event.change_event_id,
                    )
                )
    return RereasonResponse(change_event=event, artifacts_produced=artifacts, diffs=diffs)


def _changes_from_preview_request(request: PreviewImpactRequest) -> list[ChangeSpec]:
    if request.user_message:
        changes = detect_requirement_changes(request.user_message)
        if changes:
            return changes

    field = request.changed_field or "functional_requirement"
    value = request.new_value_summary or request.user_message or field
    return [
        ChangeSpec(
            requirement_type=field,
            changed_field=field,
            new_value=value,
        )
    ]


def _stage_versions(
    storage: InMemoryArchimedesStorage,
    session_id: str,
    stages: list[Any],
) -> dict[str, int]:
    versions: dict[str, int] = {}
    for stage in stages:
        stage_value = stage.value if hasattr(stage, "value") else str(stage)
        artifact = storage.read_latest_artifact(session_id, stage_value)
        versions[stage_value] = artifact.version if artifact else 0
    return versions

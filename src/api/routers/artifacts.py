from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.enums import DiffType, StageName, StageStatus
from archimedes.models.session import ArchitectureSession
from archimedes.orchestrator.controller import StageController
from archimedes.state.diff_service import ArtifactDiffService

from api.deps import get_stage_controller, get_storage
from api.errors import api_error
from api.storage import InMemoryArchimedesStorage


router = APIRouter(prefix="/sessions/{session_id}", tags=["artifacts"])


def _value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


class PipelineStageStatus(BaseModel):
    stage: str
    status: str
    quality_gate: Any | None = None
    artifact_version: int | None = None


class PipelineStatusResponse(BaseModel):
    stages: list[PipelineStageStatus]


class ArtifactDiffResponse(BaseModel):
    session_id: str
    stage: str
    before_version: int
    after_version: int
    summary: str
    added: dict[str, Any]
    removed: dict[str, Any]
    modified: dict[str, dict[str, Any]]


class PipelineRunRequest(BaseModel):
    mode: str = "standard"
    allow_warning_override: bool = False
    context_overrides: dict[str, Any] = {}
    stop_on_warning: bool = False
    stop_on_user_input_required: bool = True
    max_stages: int = 10


class PausePipelineRequest(BaseModel):
    reason: str | None = None


class ResumePipelineRequest(BaseModel):
    resume_from: str = "last_successful_stage"
    stop_on_warning: bool = False


class RetryStageRequest(BaseModel):
    reason: str | None = None
    use_same_inputs: bool = True


def _require_session(
    storage: InMemoryArchimedesStorage, session_id: str
) -> ArchitectureSession:
    session = storage.read_session(session_id)
    if session is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")
    return session


def _require_artifact(
    storage: InMemoryArchimedesStorage,
    session_id: str,
    stage: str,
    version: int | None = None,
) -> VersionedArtifact:
    artifact = (
        storage.read_latest_artifact(session_id, stage)
        if version is None
        else storage.read_artifact_version(session_id, stage, version)
    )
    if artifact is None:
        suffix = "latest" if version is None else f"v{version}"
        raise api_error(
            404,
            f"Artifact not found: {stage} {suffix}",
            "artifact_not_found",
        )
    return artifact


def _pipeline_status(session: ArchitectureSession) -> PipelineStatusResponse:
    stages: list[PipelineStageStatus] = []
    for stage, execution in session.stage_executions.items():
        stages.append(
            PipelineStageStatus(
                stage=_value(stage),
                status=_value(execution.status),
                quality_gate=session.quality_gates.get(stage),
                artifact_version=session.latest_artifact_versions.get(stage),
            )
        )
    return PipelineStatusResponse(stages=stages)


@router.get("/pipeline/status")
async def get_pipeline_status(
    session_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> PipelineStatusResponse:
    return _pipeline_status(_require_session(storage, session_id))


@router.get("/pipeline")
async def get_pipeline(
    session_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> PipelineStatusResponse:
    return _pipeline_status(_require_session(storage, session_id))


@router.post("/pipeline/run-next")
async def run_next_stage(
    session_id: str,
    request: PipelineRunRequest | None = None,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
    controller: StageController = Depends(get_stage_controller),
) -> dict[str, Any]:
    _require_session(storage, session_id)
    response = controller.process_message(session_id, "proceed")
    session = _require_session(storage, session_id)
    execution = session.stage_executions.get(response.current_stage)
    return {
        "session_id": session_id,
        "stage": _value(response.current_stage),
        "stage_run_id": execution.stage_run_id if execution else None,
        "status": response.stage_status,
        "artifacts_produced": response.artifacts_produced,
        "requires_user_action": response.requires_user_action,
    }


@router.post("/pipeline/run")
async def run_pipeline(
    session_id: str,
    request: PipelineRunRequest | None = None,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
    controller: StageController = Depends(get_stage_controller),
) -> dict[str, Any]:
    _require_session(storage, session_id)
    response = controller.process_message(session_id, "proceed")
    return {
        "session_id": session_id,
        "pipeline_run_id": f"pipe_{session_id}",
        "status": response.stage_status,
        "started_from_stage": _value(response.current_stage),
        "planned_stages": [stage.value for stage in StageName],
        "artifacts_produced": response.artifacts_produced,
        "requires_user_action": response.requires_user_action,
    }


@router.post("/pipeline/pause")
async def pause_pipeline(
    session_id: str,
    request: PausePipelineRequest | None = None,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    session = _require_session(storage, session_id)
    execution = session.stage_executions.get(session.current_stage)
    if execution:
        execution.status = StageStatus.PAUSED
    session.awaiting_stage_confirmation = True
    storage.upsert_session(session)
    return {
        "session_id": session_id,
        "status": "paused",
        "current_stage": _value(session.current_stage),
        "reason": request.reason if request else None,
    }


@router.post("/pipeline/resume")
async def resume_pipeline(
    session_id: str,
    request: ResumePipelineRequest | None = None,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    session = _require_session(storage, session_id)
    execution = session.stage_executions.get(session.current_stage)
    if execution and execution.status == StageStatus.PAUSED:
        execution.status = StageStatus.PENDING
    session.awaiting_stage_confirmation = False
    storage.upsert_session(session)
    return {
        "session_id": session_id,
        "status": "running",
        "resumed_from_stage": _value(session.current_stage),
    }


@router.post("/pipeline/stages/{stage_id}/retry")
async def retry_stage(
    session_id: str,
    stage_id: StageName,
    request: RetryStageRequest | None = None,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    session = _require_session(storage, session_id)
    execution = session.stage_executions.get(stage_id)
    if execution is None:
        raise api_error(404, f"Stage run not found: {stage_id}", "stage_not_found")
    execution.retry_count += 1
    execution.status = StageStatus.RUNNING
    storage.upsert_session(session)
    return {
        "session_id": session_id,
        "stage": stage_id.value,
        "stage_run_id": execution.stage_run_id,
        "retry_count": execution.retry_count,
        "status": "running",
    }


@router.post("/pipeline/stage-runs/{stage_run_id}/cancel")
async def cancel_stage_run(
    session_id: str,
    stage_run_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> dict[str, Any]:
    session = _require_session(storage, session_id)
    for execution in session.stage_executions.values():
        if execution.stage_run_id == stage_run_id:
            execution.status = StageStatus.PAUSED
            storage.upsert_session(session)
            return {
                "session_id": session_id,
                "stage_run_id": stage_run_id,
                "status": "cancel_requested",
            }
    raise api_error(404, f"Stage run not found: {stage_run_id}", "stage_run_not_found")


@router.get("/artifacts/{stage}/latest")
async def get_latest_artifact(
    session_id: str,
    stage: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> VersionedArtifact:
    _require_session(storage, session_id)
    return _require_artifact(storage, session_id, stage)


@router.get("/artifacts/{stage}")
async def get_artifact_by_query_version(
    session_id: str,
    stage: str,
    version: int = Query(ge=1),
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> VersionedArtifact:
    _require_session(storage, session_id)
    return _require_artifact(storage, session_id, stage, version)


@router.get("/artifacts/{stage}/versions/{version}")
async def get_artifact_by_version(
    session_id: str,
    stage: str,
    version: int,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> VersionedArtifact:
    _require_session(storage, session_id)
    return _require_artifact(storage, session_id, stage, version)


@router.get("/artifacts/{stage}/diff")
async def get_artifact_diff(
    session_id: str,
    stage: str,
    v1: int = Query(ge=1),
    v2: int = Query(ge=1),
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ArtifactDiffResponse:
    if v2 <= v1:
        raise api_error(422, "v2 must be greater than v1", "validation_error")

    _require_artifact(storage, session_id, stage, v1)
    _require_artifact(storage, session_id, stage, v2)
    diff = ArtifactDiffService(storage).generate_diff(session_id, stage, v1, v2)
    added = {
        _top_level_path(field.field_path): field.after
        for field in diff.field_diffs
        if field.diff_type == DiffType.ADDED
    }
    removed = {
        _top_level_path(field.field_path): field.before
        for field in diff.field_diffs
        if field.diff_type == DiffType.REMOVED
    }
    modified = {
        _top_level_path(field.field_path): {"before": field.before, "after": field.after}
        for field in diff.field_diffs
        if field.diff_type == DiffType.MODIFIED
    }

    return ArtifactDiffResponse(
        session_id=session_id,
        stage=stage,
        before_version=v1,
        after_version=v2,
        summary=diff.summary,
        added=added,
        removed=removed,
        modified=modified,
    )


def _top_level_path(field_path: str) -> str:
    trimmed = field_path[2:] if field_path.startswith("$.") else field_path
    return trimmed.split(".", maxsplit=1)[0].split("[", maxsplit=1)[0]

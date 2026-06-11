from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.enums import DiffType
from archimedes.models.session import ArchitectureSession
from archimedes.state.diff_service import ArtifactDiffService

from api.deps import get_storage
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

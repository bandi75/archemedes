from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from archimedes.models.diffs import ArtifactDiff
from archimedes.models.enums import StageName
from archimedes.state.diff_service import ArtifactDiffService

from api.deps import get_storage
from api.errors import api_error
from api.storage import InMemoryArchimedesStorage


router = APIRouter(prefix="/sessions/{session_id}/diffs", tags=["diffs"])


class CreateDiffRequest(BaseModel):
    stage: StageName
    before_version: int = Field(ge=1)
    after_version: int = Field(ge=1)
    change_event_id: str | None = None


class ListDiffsResponse(BaseModel):
    items: list[ArtifactDiff]


@router.post("")
async def create_diff(
    session_id: str,
    request: CreateDiffRequest,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ArtifactDiff:
    if storage.read_session(session_id) is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")

    try:
        return ArtifactDiffService(storage).generate_diff(
            session_id,
            request.stage,
            request.before_version,
            request.after_version,
            change_event_id=request.change_event_id,
        )
    except ValueError as exc:
        message = str(exc)
        error_code = "validation_error" if "greater" in message else "artifact_not_found"
        status_code = 422 if error_code == "validation_error" else 404
        raise api_error(status_code, message, error_code) from exc


@router.get("")
async def list_diffs(
    session_id: str,
    stage: StageName | None = Query(default=None),
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ListDiffsResponse:
    if storage.read_session(session_id) is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")
    stage_value = stage.value if stage is not None else None
    return ListDiffsResponse(items=storage.list_diffs(session_id, stage=stage_value))


@router.get("/{diff_id}")
async def get_diff(
    session_id: str,
    diff_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ArtifactDiff:
    diff = storage.read_diff(session_id, diff_id)
    if diff is None:
        raise api_error(404, f"Diff not found: {diff_id}", "diff_not_found")
    return diff

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, Field

from archimedes.models.session import ArchitectureSession
from archimedes.orchestrator.controller import OrchestratorResponse, StageController

from api.deps import get_stage_controller, get_storage
from api.errors import api_error
from api.storage import InMemoryArchimedesStorage


router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    business_need: str = Field(min_length=1)
    title: str | None = None
    domain: str | None = None
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageRequest(BaseModel):
    message: str = Field(min_length=1)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ArchitectureSession:
    session = ArchitectureSession(
        title=request.title,
        business_need=request.business_need,
        user_id=request.created_by,
    )
    return storage.upsert_session(session)


@router.post("/{session_id}/messages")
async def post_message(
    session_id: str,
    request: MessageRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    controller: StageController = Depends(get_stage_controller),
) -> OrchestratorResponse:
    try:
        return controller.process_message(
            session_id,
            request.message,
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        if "Session not found" in str(exc):
            raise api_error(404, f"Session not found: {session_id}", "session_not_found") from exc
        raise


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ArchitectureSession:
    session = storage.read_session(session_id)
    if session is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")
    return session

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, status

logger = logging.getLogger(__name__)
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


class SessionSummary(BaseModel):
    session_id: str
    title: str | None
    current_stage: str | None
    created_at: Any


class SessionListResponse(BaseModel):
    items: list[SessionSummary]
    total: int


@router.get("")
async def list_sessions(
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> SessionListResponse:
    sessions = storage.list_sessions()
    items = [
        SessionSummary(
            session_id=s.session_id,
            title=s.title,
            current_stage=s.current_stage.value if hasattr(s.current_stage, "value") else s.current_stage,
            created_at=s.created_at,
        )
        for s in sessions
    ]
    return SessionListResponse(items=items, total=len(items))


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
    saved = storage.upsert_session(session)
    logger.info("[session] created session=%s title=%r", saved.session_id, saved.title)
    return saved


@router.post("/{session_id}/messages")
def post_message(
    session_id: str,
    request: MessageRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    controller: StageController = Depends(get_stage_controller),
) -> OrchestratorResponse:
    logger.info("[session] message session=%s idem=%s", session_id, idempotency_key)
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

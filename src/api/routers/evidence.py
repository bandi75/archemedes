from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from archimedes.models.claims import ClaimRecord
from archimedes.models.evidence import EvidenceSource

from api.deps import get_storage
from api.errors import api_error
from api.storage import InMemoryArchimedesStorage


router = APIRouter(prefix="/sessions/{session_id}", tags=["evidence"])


class ClaimsResponse(BaseModel):
    items: list[ClaimRecord] = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    items: list[EvidenceSource] = Field(default_factory=list)


def _ensure_session(storage: InMemoryArchimedesStorage, session_id: str) -> None:
    if storage.read_session(session_id) is None:
        raise api_error(404, f"Session not found: {session_id}", "session_not_found")


@router.get("/claims")
async def list_claims(
    session_id: str,
    stage: str | None = None,
    type: str | None = Query(default=None),
    requires_user_validation: bool | None = None,
    min_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ClaimsResponse:
    _ensure_session(storage, session_id)
    return ClaimsResponse(
        items=storage.list_claims(
            session_id,
            stage=stage,
            claim_type=type,
            requires_user_validation=requires_user_validation,
            min_confidence=min_confidence,
        )
    )


@router.get("/evidence")
async def list_evidence(
    session_id: str,
    retrieved_via: str | None = None,
    trust_level: str | None = None,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> EvidenceResponse:
    _ensure_session(storage, session_id)
    return EvidenceResponse(
        items=storage.list_evidence(
            session_id,
            retrieved_via=retrieved_via,
            trust_level=trust_level,
        )
    )

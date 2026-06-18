from __future__ import annotations

from datetime import datetime, timezone

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


class EvidenceAuditResponse(BaseModel):
    status: str
    total_claims: int
    evidence_sources: int
    unsupported_claims: int
    open_assumptions: int
    recommendation: str


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


@router.get("/claims/{claim_id}")
async def get_claim(
    session_id: str,
    claim_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ClaimRecord:
    _ensure_session(storage, session_id)
    claim = next(
        (item for item in storage.list_claims(session_id) if item.claim_id == claim_id),
        None,
    )
    if claim is None:
        raise api_error(404, f"Claim not found: {claim_id}", "claim_not_found")
    return claim


class ValidateClaimRequest(BaseModel):
    accepted: bool
    comment: str | None = None


@router.post("/claims/{claim_id}/validate")
async def validate_claim(
    session_id: str,
    claim_id: str,
    request: ValidateClaimRequest,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> ClaimRecord:
    _ensure_session(storage, session_id)
    updated = storage.update_claim(
        session_id,
        claim_id,
        validated_at=datetime.now(timezone.utc),
        validated_accepted=request.accepted,
        validation_comment=request.comment,
    )
    if updated is None:
        raise api_error(404, f"Claim not found: {claim_id}", "claim_not_found")
    return updated


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


@router.get("/audits/evidence/latest")
async def get_latest_evidence_audit(
    session_id: str,
    storage: InMemoryArchimedesStorage = Depends(get_storage),
) -> EvidenceAuditResponse:
    _ensure_session(storage, session_id)
    claims = storage.list_claims(session_id)
    evidence = storage.list_evidence(session_id)
    unsupported = sum(1 for claim in claims if not claim.evidence_ids)
    open_assumptions = sum(
        1
        for claim in claims
        if claim.requires_user_validation and claim.validated_accepted is None
    )
    return EvidenceAuditResponse(
        status="available",
        total_claims=len(claims),
        evidence_sources=len(evidence),
        unsupported_claims=unsupported,
        open_assumptions=open_assumptions,
        recommendation="review_flagged_items" if unsupported or open_assumptions else "proceed",
    )

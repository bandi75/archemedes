from __future__ import annotations

from datetime import datetime

from pydantic import Field, HttpUrl

from .base import ArchimedesModel, new_id, utc_now
from .enums import EvidenceRetrievalMethod, SourceFreshness, TrustLevel


class EvidenceSource(ArchimedesModel):
    evidence_id: str = Field(default_factory=lambda: new_id("evidence"))
    session_id: str
    source: str
    source_url: HttpUrl | None = None
    retrieved_via: EvidenceRetrievalMethod
    retrieved_at: datetime = Field(default_factory=utc_now)
    excerpt: str | None = None
    chunk_id: str | None = None

    kb_name: str | None = None
    kb_version: str | None = None
    source_document_version: str | None = None

    source_freshness: SourceFreshness = SourceFreshness.UNKNOWN
    trust_level: TrustLevel = TrustLevel.MEDIUM
    used_in_stages: list[str] = Field(default_factory=list)
    is_fixture: bool = False

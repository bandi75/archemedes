from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


class ArchimedesModel(BaseModel):
    """Base class for strict persisted schema objects."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class FlexibleContentModel(BaseModel):
    """Base class for generated payloads that may evolve."""

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class AuditFields(BaseModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: str | None = None
    updated_by: str | None = None

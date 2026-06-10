from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .base import ArchimedesModel, new_id, utc_now
from .enums import ChangeType, StageName


class ChangeEvent(ArchimedesModel):
    change_event_id: str = Field(default_factory=lambda: new_id("change"))
    session_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    change_type: ChangeType
    changed_field: str
    old_value_summary: str | None = None
    new_value_summary: str | None = None
    impacted_stages: list[StageName] = Field(default_factory=list)
    stable_stages: list[StageName] = Field(default_factory=list)
    user_message: str | None = None


class DependencyImpactResult(ArchimedesModel):
    impact_id: str = Field(default_factory=lambda: new_id("impact"))
    session_id: str
    change_event_id: str
    impacted_stages: list[StageName] = Field(default_factory=list)
    stable_stages: list[StageName] = Field(default_factory=list)
    reason_by_stage: dict[StageName, str] = Field(default_factory=dict)
    rerun_required: bool = True

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id
from .enums import DiffType, StageName


class FieldDiff(ArchimedesModel):
    field_path: str
    diff_type: DiffType
    before: Any | None = None
    after: Any | None = None
    summary: str | None = None


class ArtifactDiff(ArchimedesModel):
    diff_id: str = Field(default_factory=lambda: new_id("diff"))
    session_id: str
    stage: StageName
    before_version: int = Field(ge=1)
    after_version: int = Field(ge=1)
    change_event_id: str | None = None
    field_diffs: list[FieldDiff] = Field(default_factory=list)
    summary: str

    @model_validator(mode="after")
    def validate_versions(self):
        if self.after_version <= self.before_version:
            raise ValueError("after_version must be greater than before_version.")
        return self

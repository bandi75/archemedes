from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.diffs import ArtifactDiff, FieldDiff
from archimedes.models.enums import DiffType, StageName


class SupportsArtifactDiffStorage(Protocol):
    def read_artifact_version(
        self, session_id: str, stage: str, version: int
    ) -> VersionedArtifact | None: ...

    def upsert_diff(self, diff: ArtifactDiff) -> ArtifactDiff: ...


@dataclass(slots=True)
class ArtifactDiffService:
    storage: SupportsArtifactDiffStorage

    def generate_diff(
        self,
        session_id: str,
        stage: StageName | str,
        before_version: int,
        after_version: int,
        *,
        change_event_id: str | None = None,
    ) -> ArtifactDiff:
        if after_version <= before_version:
            raise ValueError("after_version must be greater than before_version")

        stage_value = _stage_value(stage)
        before = self.storage.read_artifact_version(session_id, stage_value, before_version)
        after = self.storage.read_artifact_version(session_id, stage_value, after_version)
        if before is None:
            raise ValueError(f"Artifact not found: {stage_value} v{before_version}")
        if after is None:
            raise ValueError(f"Artifact not found: {stage_value} v{after_version}")

        field_diffs = list(_diff_values(before.content, after.content))
        summary = _summary_for(field_diffs, before_version, after_version)
        diff = ArtifactDiff(
            session_id=session_id,
            stage=StageName(stage_value),
            before_version=before_version,
            after_version=after_version,
            change_event_id=change_event_id,
            field_diffs=field_diffs,
            summary=summary,
        )
        return self.storage.upsert_diff(diff)


def _diff_values(before: Any, after: Any, path: str = "$") -> list[FieldDiff]:
    if isinstance(before, dict) and isinstance(after, dict):
        diffs: list[FieldDiff] = []
        before_keys = set(before)
        after_keys = set(after)
        for key in sorted(after_keys - before_keys):
            field_path = f"{path}.{key}"
            diffs.append(
                FieldDiff(
                    field_path=field_path,
                    diff_type=DiffType.ADDED,
                    after=after[key],
                    summary=f"Added {field_path}",
                )
            )
        for key in sorted(before_keys - after_keys):
            field_path = f"{path}.{key}"
            diffs.append(
                FieldDiff(
                    field_path=field_path,
                    diff_type=DiffType.REMOVED,
                    before=before[key],
                    summary=f"Removed {field_path}",
                )
            )
        for key in sorted(before_keys & after_keys):
            diffs.extend(_diff_values(before[key], after[key], f"{path}.{key}"))
        return diffs

    if isinstance(before, list) and isinstance(after, list):
        diffs = []
        max_len = max(len(before), len(after))
        for index in range(max_len):
            field_path = f"{path}[{index}]"
            if index >= len(before):
                diffs.append(
                    FieldDiff(
                        field_path=field_path,
                        diff_type=DiffType.ADDED,
                        after=after[index],
                        summary=f"Added {field_path}",
                    )
                )
            elif index >= len(after):
                diffs.append(
                    FieldDiff(
                        field_path=field_path,
                        diff_type=DiffType.REMOVED,
                        before=before[index],
                        summary=f"Removed {field_path}",
                    )
                )
            else:
                diffs.extend(_diff_values(before[index], after[index], field_path))
        return diffs

    if before != after:
        return [
            FieldDiff(
                field_path=path,
                diff_type=DiffType.MODIFIED,
                before=before,
                after=after,
                summary=f"Modified {path}",
            )
        ]
    return []


def _summary_for(field_diffs: list[FieldDiff], before_version: int, after_version: int) -> str:
    counts = {DiffType.ADDED: 0, DiffType.REMOVED: 0, DiffType.MODIFIED: 0}
    for diff in field_diffs:
        counts[diff.diff_type] += 1
    return (
        f"{len(field_diffs)} field change(s) between v{before_version} and v{after_version}: "
        f"{counts[DiffType.ADDED]} added, {counts[DiffType.REMOVED]} removed, "
        f"{counts[DiffType.MODIFIED]} modified."
    )


def _stage_value(stage: StageName | str) -> str:
    return stage.value if isinstance(stage, StageName) else str(stage)

from __future__ import annotations

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.diffs import ArtifactDiff
from archimedes.models.enums import DiffType, StageName
from archimedes.models.quality_gates import QualityGateResult
from archimedes.state.diff_service import ArtifactDiffService


class DiffStorage:
    def __init__(self):
        self.artifacts = {}
        self.diffs: dict[str, ArtifactDiff] = {}

    def read_artifact_version(self, session_id: str, stage: str, version: int):
        return self.artifacts.get((session_id, stage, version))

    def upsert_diff(self, diff: ArtifactDiff):
        self.diffs[diff.diff_id] = diff
        return diff


def test_artifact_diff_service_generates_structured_field_diffs():
    storage = DiffStorage()
    storage.artifacts[("session_1", "hld_generation", 1)] = VersionedArtifact(
        session_id="session_1",
        stage=StageName.HLD_GENERATION,
        version=1,
        stage_run_id="run_1",
        content={"components": [{"name": "Event Hubs"}], "region": "single"},
        quality_gate=QualityGateResult(status="passed"),
    )
    storage.artifacts[("session_1", "hld_generation", 2)] = VersionedArtifact(
        session_id="session_1",
        stage=StageName.HLD_GENERATION,
        version=2,
        stage_run_id="run_2",
        content={
            "components": [{"name": "Partitioned Event Hubs"}, {"name": "AKS"}],
            "region": "multi-region",
        },
        quality_gate=QualityGateResult(status="passed"),
    )

    diff = ArtifactDiffService(storage).generate_diff(
        "session_1",
        StageName.HLD_GENERATION,
        1,
        2,
        change_event_id="change_1",
    )

    assert diff.change_event_id == "change_1"
    assert any(field.diff_type == DiffType.ADDED for field in diff.field_diffs)
    assert any(field.field_path == "$.region" for field in diff.field_diffs)
    assert diff.diff_id in storage.diffs

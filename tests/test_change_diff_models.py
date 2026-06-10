import pytest

from archimedes.models.change import ChangeEvent
from archimedes.models.diffs import ArtifactDiff, FieldDiff
from archimedes.models.enums import DiffType, StageName


def test_change_event_keeps_impacted_and_stable_stages():
    event = ChangeEvent(
        session_id="session_123",
        change_type="requirement_modified",
        changed_field="throughput_tps",
        old_value_summary="10K",
        new_value_summary="100K",
        impacted_stages=[StageName.OPTIONS_GENERATION, StageName.SOCRATIC_REVIEW],
        stable_stages=[StageName.INTAKE],
    )
    assert event.changed_field == "throughput_tps"
    assert len(event.impacted_stages) == 2


def test_artifact_diff_requires_after_version_gt_before_version():
    with pytest.raises(ValueError):
        ArtifactDiff(
            session_id="session_123",
            stage=StageName.HLD_GENERATION,
            before_version=2,
            after_version=2,
            summary="No-op",
            field_diffs=[
                FieldDiff(
                    field_path="components[0].name",
                    diff_type=DiffType.MODIFIED,
                    before="Event Hubs",
                    after="Event Hubs Dedicated",
                )
            ],
        )

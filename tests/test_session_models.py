from datetime import datetime, timezone

import pytest

from archimedes.models.enums import StageName, StageStatus
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.session import ArchitectureSession, StageExecution


def test_architecture_session_initializes_current_stage_execution():
    session = ArchitectureSession(business_need="Design fraud detection on Azure")
    assert session.current_stage == StageName.INTAKE
    assert StageName.INTAKE in session.stage_executions


def test_stage_execution_requires_failure_reason_on_failed_status():
    with pytest.raises(ValueError):
        StageExecution(stage=StageName.OPTIONS_GENERATION, status=StageStatus.FAILED)


def test_stage_execution_rejects_backwards_timestamps():
    started = datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
    completed = datetime(2026, 6, 10, 9, 59, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        StageExecution(
            stage=StageName.ADR_GENERATION,
            status=StageStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
        )


def test_quality_gate_failed_cannot_allow_override():
    with pytest.raises(ValueError):
        QualityGateResult(
            status="failed",
            blocking_failures=["missing required NFR"],
            user_override_allowed=True,
        )

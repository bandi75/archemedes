from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import hashlib
import json

import httpx
import pytest
from fastapi import HTTPException

from archimedes.models.base import new_id
from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.claims import ClaimRecord
from archimedes.models.evidence import EvidenceSource
from archimedes.models.enums import StageName
from archimedes.models.enums import ClaimType
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from api.main import Settings, create_app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _test_app():
    return create_app(Settings(validate_required_env=False, storage_backend="memory"))


class FakeAgentFactory:
    def run_stage(
        self,
        agent_name: str,
        *,
        session_id: str,
        stage: StageName,
        base_version: int,
        user_message: str,
    ) -> StagePatch:
        stage_value = stage.value if isinstance(stage, StageName) else str(stage)
        payload = {"stage": stage_value, "status": "generated", "summary": user_message[:80]}
        if stage == StageName.OPTIONS_GENERATION:
            payload["options"] = [
                {
                    "option_id": "option_event_streaming",
                    "name": "Event streaming",
                    "summary": "Streaming option",
                }
            ]
        if stage == StageName.HLD_GENERATION:
            payload["components"] = [{"name": "Event Hubs", "role": "ingestion"}]
        patch_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        stage_run_id = new_id("stage_run")
        evidence = EvidenceSource(
            session_id=session_id,
            source=f"fake-{stage_value}",
            retrieved_via="user_input",
            excerpt=user_message[:120],
        )
        claim = ClaimRecord(
            session_id=session_id,
            claim=f"{stage_value} processed by {agent_name}.",
            type=ClaimType.ASSUMPTION,
            confidence=0.65,
            stage=stage,
            evidence_ids=[evidence.evidence_id],
        )
        return StagePatch(
            session_id=session_id,
            stage=stage,
            stage_run_id=stage_run_id,
            base_version=base_version,
            target_version=base_version + 1,
            idempotency_key=hashlib.sha256(
                f"{session_id}:{stage_value}:{stage_run_id}:{patch_hash}".encode()
            ).hexdigest(),
            patch_hash=patch_hash,
            patch=payload,
            claims=[claim],
            evidence_sources=[evidence],
            quality_gate_result=QualityGateResult(status="passed"),
        )


@asynccontextmanager
async def _test_client(
    app=None,
    *,
    raise_server_exceptions: bool = True,
):
    app = app or _test_app()
    transport = httpx.ASGITransport(
        app=app,
        raise_app_exceptions=raise_server_exceptions,
    )
    async with app.router.lifespan_context(app):
        app.state.stage_controller.agent_factory = FakeAgentFactory()
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client


async def test_health_endpoint_returns_service_status():
    async with _test_client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "archimedes-api"


async def test_versioned_health_endpoint_returns_service_status():
    async with _test_client() as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_cors_allows_streamlit_origin():
    async with _test_client() as client:
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"


async def test_lifespan_validates_required_env_vars(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    app = create_app(
        Settings(
            required_env_vars=("FOUNDRY_PROJECT_ENDPOINT",),
            validate_required_env=True,
            storage_backend="memory",
        )
    )

    with pytest.raises(RuntimeError, match="FOUNDRY_PROJECT_ENDPOINT"):
        async with _test_client(app):
            pass


async def test_settings_reads_prefixed_cosmos_config(monkeypatch):
    monkeypatch.setenv(
        "ARCHIMEDES_API_COSMOS_ENDPOINT",
        "https://cosmos.example.documents.azure.com:443/",
    )
    monkeypatch.setenv("ARCHIMEDES_API_COSMOS_DATABASE_NAME", "archimedes-test")
    monkeypatch.setenv("ARCHIMEDES_API_COSMOS_KEY", "test-key")

    settings = Settings(_env_file=None)

    assert settings.cosmos_endpoint == "https://cosmos.example.documents.azure.com:443/"
    assert settings.cosmos_database_name == "archimedes-test"
    assert settings.cosmos_key == "test-key"


async def test_env_example_documents_settings_model_variables():
    env_example = Path(".env.example").read_text(encoding="utf-8")
    expected_names = {
        f"ARCHIMEDES_API_{field_name.upper()}"
        for field_name in Settings.model_fields
    }

    missing = [name for name in sorted(expected_names) if f"{name}=" not in env_example]

    assert missing == []


async def test_cosmos_storage_ignores_legacy_endpoint_env(monkeypatch):
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://legacy.example.documents.azure.com:443/")
    app = create_app(
        Settings(
            validate_required_env=False,
            storage_backend="cosmos",
            cosmos_endpoint=None,
        )
    )

    with pytest.raises(RuntimeError, match="ARCHIMEDES_API_COSMOS_ENDPOINT"):
        async with _test_client(app):
            pass


async def test_http_exception_handler_returns_structured_error():
    app = _test_app()

    @app.get("/boom")
    async def boom():
        raise HTTPException(
            status_code=404,
            detail={"detail": "Missing session", "error_code": "session_not_found"},
        )

    async with _test_client(app) as client:
        response = await client.get("/boom")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Missing session",
        "error_code": "session_not_found",
    }


async def test_unhandled_exception_handler_returns_structured_error():
    app = _test_app()

    @app.get("/boom")
    async def boom():
        raise ValueError("unexpected failure")

    async with _test_client(app, raise_server_exceptions=False) as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "unexpected failure",
        "error_code": "internal_error",
    }


async def test_validation_error_handler_returns_structured_error():
    async with _test_client() as client:
        response = await client.post("/api/v1/sessions", json={})

    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"


async def test_create_session_message_status_and_artifact_flow():
    async with _test_client() as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={
                "business_need": "Design a real-time fraud detection platform",
                "title": "Fraud detection",
            },
        )
        session_id = create_response.json()["session_id"]

        message_response = await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Need an Azure architecture for fraud detection"},
            headers={"Idempotency-Key": "idem-intake-1"},
        )
        status_response = await client.get(f"/api/v1/sessions/{session_id}/pipeline/status")
        artifact_response = await client.get(
            f"/api/v1/sessions/{session_id}/artifacts/intake/latest"
        )
        session_response = await client.get(f"/api/v1/sessions/{session_id}")

    assert create_response.status_code == 201
    assert message_response.status_code == 200
    assert message_response.json()["stage_status"] == "completed"
    assert status_response.status_code == 200
    assert status_response.json()["stages"][0]["stage"] == "intake"
    assert artifact_response.status_code == 200
    assert artifact_response.json()["version"] == 1
    # current_stage remains the last completed stage (intake) so refinement targets it correctly.
    # pending_next_stage reflects what executes next when the user says "proceed".
    assert session_response.json()["current_stage"] == "intake"
    assert session_response.json()["pending_next_stage"] == "requirements_extraction"


async def test_claims_endpoint_returns_claims_created_by_message_flow():
    async with _test_client() as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={"business_need": "Build an event-driven platform"},
        )
        session_id = create_response.json()["session_id"]
        await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Generate the intake output"},
        )

        claims_response = await client.get(f"/api/v1/sessions/{session_id}/claims")
        evidence_response = await client.get(f"/api/v1/sessions/{session_id}/evidence")

    assert claims_response.status_code == 200
    assert len(claims_response.json()["items"]) >= 1
    assert evidence_response.status_code == 200
    # Evidence count depends on whether the LLM called foundry_iq_retrieve; structure must be valid.
    assert isinstance(evidence_response.json()["items"], list)


async def test_artifact_version_and_diff_endpoints():
    app = _test_app()
    async with _test_client(app) as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={"business_need": "Build a streaming architecture"},
        )
        session_id = create_response.json()["session_id"]
        await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Generate an intake artifact"},
        )

        latest = app.state.storage.read_latest_artifact(session_id, "intake")
        app.state.storage.upsert_artifact(
            VersionedArtifact(
                session_id=session_id,
                stage=StageName.INTAKE,
                version=2,
                stage_run_id="stage_run_v2",
                content={"summary": "changed output", "new_field": "added"},
                quality_gate=QualityGateResult(status="passed"),
            )
        )

        version_response = await client.get(
            f"/api/v1/sessions/{session_id}/artifacts/intake?version=1"
        )
        diff_response = await client.get(
            f"/api/v1/sessions/{session_id}/artifacts/intake/diff?v1=1&v2=2"
        )

    assert latest is not None
    assert version_response.status_code == 200
    assert version_response.json()["version"] == 1
    assert diff_response.status_code == 200
    # new_field only exists in v2 → always added; summary may be added or modified depending on LLM output.
    assert diff_response.json()["added"].get("new_field") == "added"
    diff = diff_response.json()
    assert "summary" in diff.get("added", {}) or "summary" in diff.get("modified", {})


async def test_change_preview_message_rereasoning_and_structured_diff_endpoints():
    app = _test_app()
    async with _test_client(app) as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={"business_need": "Build a real-time fraud detection platform"},
        )
        session_id = create_response.json()["session_id"]
        # Gate stages require a proceed signal to advance. Non-gate stages (pattern_detection)
        # chain automatically. Sequence: intake → proceed → requirements_extraction → proceed → options_generation.
        for message in [
            "Build a real-time fraud detection platform for fintech processing 10K TPS.",
            "proceed",   # → requirements_extraction (gate); pattern_detection chains automatically after
            "proceed",   # → options_generation (gate)
        ]:
            await client.post(
                f"/api/v1/sessions/{session_id}/messages",
                json={"message": message},
            )

        preview_response = await client.post(
            f"/api/v1/sessions/{session_id}/changes/preview-impact",
            json={"user_message": "Actually make it 100K TPS and multi-region active-active"},
        )
        change_response = await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Actually make it 100K TPS and multi-region active-active"},
        )
        change_events = app.state.storage.list_change_events(session_id)
        assert change_events, "Expected at least one change event after re-reasoning"
        event = change_events[-1]
        diffs = change_response.json().get("diffs", [])
        list_response = await client.get(
            f"/api/v1/sessions/{session_id}/diffs?stage=options_generation"
        )

    assert preview_response.status_code == 200
    assert "options_generation" in preview_response.json()["impacted_stages"]
    assert change_response.status_code == 200
    assert change_response.json()["stage_status"] == "rereasoned"
    assert any(
        a.startswith("options_generation:v") for a in change_response.json()["artifacts_produced"]
    ), f"Expected options_generation artifact in {change_response.json()['artifacts_produced']}"
    assert list_response.status_code == 200
    assert isinstance(diffs, list)


async def test_react_view_model_and_event_endpoints():
    app = _test_app()
    async with _test_client(app) as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={
                "business_need": "Build a real-time fraud detection platform",
                "title": "Fraud detection",
            },
        )
        session_id = create_response.json()["session_id"]
        await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Generate an intake artifact"},
        )

        overview = await client.get(f"/api/v1/sessions/{session_id}/overview")
        pipeline = await client.get(f"/api/v1/sessions/{session_id}/pipeline/view")
        socrates = await client.get(f"/api/v1/sessions/{session_id}/socrates/view")
        evidence = await client.get(f"/api/v1/sessions/{session_id}/evidence/view")
        package = await client.get(f"/api/v1/sessions/{session_id}/artifacts/package-view")
        events = await client.get(f"/api/v1/sessions/{session_id}/events")
        stream = await client.get(f"/api/v1/sessions/{session_id}/events/stream")
        first_event_id = events.json()["items"][0]["event_id"]
        replay = await client.get(
            f"/api/v1/sessions/{session_id}/events",
            params={"after_event_id": first_event_id},
        )
        replay_stream = await client.get(
            f"/api/v1/sessions/{session_id}/events/stream",
            headers={"Last-Event-ID": first_event_id},
        )

    assert overview.status_code == 200
    assert overview.json()["session"]["session_id"] == session_id
    assert pipeline.status_code == 200
    assert pipeline.json()["session"]["session_id"] == session_id
    assert pipeline.json()["stages"]
    assert all("last_updated_at" in stage for stage in pipeline.json()["stages"])
    assert "recent_events" in pipeline.json()
    assert socrates.status_code == 200
    assert "synthesis" in socrates.json()
    assert evidence.status_code == 200
    assert evidence.json()["coverage"]["total_claims"] >= 1
    assert package.status_code == 200
    assert "artifacts" in package.json()
    assert events.status_code == 200
    assert events.json()["items"]
    assert events.json()["last_event_id"]
    assert all("severity" in event and "payload" in event for event in events.json()["items"])
    assert replay.status_code == 200
    assert first_event_id not in [event["event_id"] for event in replay.json()["items"]]
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert stream.headers["cache-control"] == "no-cache"
    assert "retry: 3000" in stream.text
    assert "event:" in stream.text
    assert replay_stream.status_code == 200
    assert f"id: {first_event_id}" not in replay_stream.text


async def test_react_pipeline_control_endpoints():
    async with _test_client() as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={"business_need": "Build a real-time fraud detection platform"},
        )
        session_id = create_response.json()["session_id"]
        await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Generate intake"},
        )

        pause = await client.post(
            f"/api/v1/sessions/{session_id}/pipeline/pause",
            json={"reason": "Review before next stage"},
        )
        resume = await client.post(f"/api/v1/sessions/{session_id}/pipeline/resume", json={})
        run_next = await client.post(f"/api/v1/sessions/{session_id}/pipeline/run-next", json={})
        run = await client.post(f"/api/v1/sessions/{session_id}/pipeline/run", json={})
        session = (await client.get(f"/api/v1/sessions/{session_id}")).json()
        stage_run_id = session["stage_executions"][session["current_stage"]]["stage_run_id"]
        retry = await client.post(
            f"/api/v1/sessions/{session_id}/pipeline/stages/{session['current_stage']}/retry",
            json={"reason": "retry test"},
        )
        cancel = await client.post(
            f"/api/v1/sessions/{session_id}/pipeline/stage-runs/{stage_run_id}/cancel"
        )

    assert pause.status_code == 200
    assert pause.json()["status"] == "paused"
    assert resume.status_code == 200
    assert run_next.status_code == 200
    assert run.status_code == 200
    assert retry.status_code == 200
    assert retry.json()["retry_count"] >= 1
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancel_requested"


async def test_full_workbench_view_and_resource_endpoints():
    async with _test_client() as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={"business_need": "Build a real-time fraud detection platform"},
        )
        session_id = create_response.json()["session_id"]
        await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Build a real-time fraud detection platform for fintech."},
        )

        requirements = await client.get(f"/api/v1/sessions/{session_id}/requirements/view")
        patterns = await client.get(f"/api/v1/sessions/{session_id}/patterns/view")
        options = await client.get(f"/api/v1/sessions/{session_id}/options/view")
        artifacts = await client.get(f"/api/v1/sessions/{session_id}/artifacts")
        claims = await client.get(f"/api/v1/sessions/{session_id}/claims")
        claim_id = claims.json()["items"][0]["claim_id"]
        claim = await client.get(f"/api/v1/sessions/{session_id}/claims/{claim_id}")
        audit = await client.get(f"/api/v1/sessions/{session_id}/audits/evidence/latest")

    assert requirements.status_code == 200
    assert "functional_requirements" in requirements.json()
    assert patterns.status_code == 200
    assert "primary_patterns" in patterns.json()
    assert options.status_code == 200
    assert "options" in options.json()
    assert artifacts.status_code == 200
    assert artifacts.json()["items"]
    assert claim.status_code == 200
    assert claim.json()["claim_id"] == claim_id
    assert audit.status_code == 200
    assert audit.json()["total_claims"] >= 1


async def test_change_impact_view_endpoint():
    app = _test_app()
    async with _test_client(app) as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={"business_need": "Build a real-time fraud detection platform"},
        )
        session_id = create_response.json()["session_id"]
        change_response = await client.post(
            f"/api/v1/sessions/{session_id}/changes",
            json={
                "changed_field": "scale",
                "old_value_summary": "10K TPS",
                "new_value_summary": "100K TPS",
                "user_message": "Actually make it 100K TPS",
            },
        )
        change_event_id = change_response.json()["change_event_id"]

        impact = await client.get(
            f"/api/v1/sessions/{session_id}/changes/{change_event_id}/impact-view"
        )

    assert impact.status_code == 200
    assert impact.json()["change_event"]["change_event_id"] == change_event_id
    assert "options_generation" in impact.json()["impact"]["impacted_stages"]


async def test_react_delivery_p0_p1_endpoint_checklist():
    async with _test_client() as client:
        create_response = await client.post(
            "/api/v1/sessions",
            json={"business_need": "Build a real-time fraud detection platform"},
        )
        session_id = create_response.json()["session_id"]
        await client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Generate the first architecture artifact"},
        )
        claims = await client.get(f"/api/v1/sessions/{session_id}/claims")
        claim_id = claims.json()["items"][0]["claim_id"]
        validate = await client.post(
            f"/api/v1/sessions/{session_id}/claims/{claim_id}/validate",
            json={"accepted": True, "comment": "Confirmed for endpoint checklist."},
        )
        change = await client.post(
            f"/api/v1/sessions/{session_id}/changes",
            json={
                "changed_field": "throughput",
                "old_value_summary": "10K TPS",
                "new_value_summary": "100K TPS",
                "user_message": "Increase throughput to 100K TPS",
            },
        )
        change_event_id = change.json()["change_event_id"]
        responses = [
            create_response,
            await client.get(f"/api/v1/sessions/{session_id}"),
            await client.get(f"/api/v1/sessions/{session_id}/overview"),
            await client.get(f"/api/v1/sessions/{session_id}/pipeline"),
            await client.get(f"/api/v1/sessions/{session_id}/pipeline/view"),
            await client.post(f"/api/v1/sessions/{session_id}/pipeline/run", json={}),
            await client.post(f"/api/v1/sessions/{session_id}/pipeline/run-next", json={}),
            await client.get(f"/api/v1/sessions/{session_id}/events"),
            await client.get(f"/api/v1/sessions/{session_id}/events/stream"),
            await client.get(f"/api/v1/sessions/{session_id}/socrates/view"),
            await client.get(f"/api/v1/sessions/{session_id}/evidence/view"),
            await client.get(f"/api/v1/sessions/{session_id}/artifacts/package-view"),
            validate,
            change,
            await client.get(
                f"/api/v1/sessions/{session_id}/changes/{change_event_id}/impact-view"
            ),
            await client.post(
                f"/api/v1/sessions/{session_id}/changes/{change_event_id}/rereason",
                json={},
            ),
            await client.get(f"/api/v1/sessions/{session_id}/diffs"),
            await client.get("/health"),
            await client.get("/health/ready"),
            await client.get("/api/v1/sessions"),
            await client.get(f"/api/v1/sessions/{session_id}/requirements/view"),
            await client.get(f"/api/v1/sessions/{session_id}/options/view"),
            await client.get(f"/api/v1/sessions/{session_id}/patterns/view"),
            await client.get(f"/api/v1/sessions/{session_id}/artifacts"),
            await client.get(f"/api/v1/sessions/{session_id}/artifacts/intake/latest"),
            claims,
            await client.get(f"/api/v1/sessions/{session_id}/claims/{claim_id}"),
            await client.get(f"/api/v1/sessions/{session_id}/evidence"),
            await client.get(f"/api/v1/sessions/{session_id}/audits/evidence/latest"),
        ]

    assert all(response.status_code < 400 for response in responses)


async def test_unknown_session_returns_structured_not_found():
    async with _test_client() as client:
        response = await client.get("/api/v1/sessions/missing")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Session not found: missing",
        "error_code": "session_not_found",
    }

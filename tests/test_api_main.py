from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.enums import StageName
from archimedes.models.quality_gates import QualityGateResult
from api.main import Settings, create_app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _test_app():
    return create_app(Settings(validate_required_env=False, storage_backend="memory"))


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
        options_v2 = app.state.storage.read_latest_artifact(session_id, "options_generation")
        diff_response = await client.post(
            f"/api/v1/sessions/{session_id}/diffs",
            json={
                "stage": "options_generation",
                "before_version": 1,
                "after_version": options_v2.version if options_v2 else 2,
                "change_event_id": event.change_event_id,
            },
        )
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
    assert diff_response.status_code == 200
    assert diff_response.json()["change_event_id"] == event.change_event_id
    assert list_response.json()["items"][0]["diff_id"] == diff_response.json()["diff_id"]


async def test_unknown_session_returns_structured_not_found():
    async with _test_client() as client:
        response = await client.get("/api/v1/sessions/missing")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Session not found: missing",
        "error_code": "session_not_found",
    }

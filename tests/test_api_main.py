from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from archimedes.models.artifacts import VersionedArtifact
from archimedes.models.enums import StageName
from archimedes.models.quality_gates import QualityGateResult
from api.main import Settings, create_app


def _test_app():
    return create_app(Settings(validate_required_env=False))


def test_health_endpoint_returns_service_status():
    with TestClient(_test_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "archimedes-api"


def test_versioned_health_endpoint_returns_service_status():
    with TestClient(_test_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_allows_streamlit_origin():
    with TestClient(_test_app()) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"


def test_lifespan_validates_required_env_vars(monkeypatch):
    monkeypatch.delenv("FOUNDRY_PROJECT_ENDPOINT", raising=False)
    app = create_app(Settings(required_env_vars=("FOUNDRY_PROJECT_ENDPOINT",)))

    with pytest.raises(RuntimeError, match="FOUNDRY_PROJECT_ENDPOINT"):
        with TestClient(app):
            pass


def test_http_exception_handler_returns_structured_error():
    app = _test_app()

    @app.get("/boom")
    async def boom():
        raise HTTPException(
            status_code=404,
            detail={"detail": "Missing session", "error_code": "session_not_found"},
        )

    with TestClient(app) as client:
        response = client.get("/boom")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Missing session",
        "error_code": "session_not_found",
    }


def test_unhandled_exception_handler_returns_structured_error():
    app = _test_app()

    @app.get("/boom")
    async def boom():
        raise ValueError("unexpected failure")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "unexpected failure",
        "error_code": "internal_error",
    }


def test_validation_error_handler_returns_structured_error():
    with TestClient(_test_app()) as client:
        response = client.post("/api/v1/sessions", json={})

    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"


def test_create_session_message_status_and_artifact_flow():
    with TestClient(_test_app()) as client:
        create_response = client.post(
            "/api/v1/sessions",
            json={
                "business_need": "Design a real-time fraud detection platform",
                "title": "Fraud detection",
            },
        )
        session_id = create_response.json()["session_id"]

        message_response = client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Need an Azure architecture for fraud detection"},
            headers={"Idempotency-Key": "idem-intake-1"},
        )
        status_response = client.get(f"/api/v1/sessions/{session_id}/pipeline/status")
        artifact_response = client.get(f"/api/v1/sessions/{session_id}/artifacts/intake/latest")
        session_response = client.get(f"/api/v1/sessions/{session_id}")

    assert create_response.status_code == 201
    assert message_response.status_code == 200
    assert message_response.json()["stage_status"] == "completed"
    assert status_response.status_code == 200
    assert status_response.json()["stages"][0]["stage"] == "intake"
    assert artifact_response.status_code == 200
    assert artifact_response.json()["version"] == 1
    assert session_response.json()["current_stage"] == "requirements_extraction"


def test_claims_endpoint_returns_claims_created_by_message_flow():
    with TestClient(_test_app()) as client:
        create_response = client.post(
            "/api/v1/sessions",
            json={"business_need": "Build an event-driven platform"},
        )
        session_id = create_response.json()["session_id"]
        client.post(
            f"/api/v1/sessions/{session_id}/messages",
            json={"message": "Generate the intake output"},
        )

        claims_response = client.get(f"/api/v1/sessions/{session_id}/claims")
        evidence_response = client.get(f"/api/v1/sessions/{session_id}/evidence")

    assert claims_response.status_code == 200
    assert len(claims_response.json()["items"]) == 1
    assert evidence_response.status_code == 200
    assert evidence_response.json() == {"items": []}


def test_artifact_version_and_diff_endpoints():
    app = _test_app()
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/sessions",
            json={"business_need": "Build a streaming architecture"},
        )
        session_id = create_response.json()["session_id"]
        client.post(
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

        version_response = client.get(f"/api/v1/sessions/{session_id}/artifacts/intake?version=1")
        diff_response = client.get(
            f"/api/v1/sessions/{session_id}/artifacts/intake/diff?v1=1&v2=2"
        )

    assert latest is not None
    assert version_response.status_code == 200
    assert version_response.json()["version"] == 1
    assert diff_response.status_code == 200
    assert diff_response.json()["added"] == {"new_field": "added"}
    assert "summary" in diff_response.json()["modified"]


def test_unknown_session_returns_structured_not_found():
    with TestClient(_test_app()) as client:
        response = client.get("/api/v1/sessions/missing")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Session not found: missing",
        "error_code": "session_not_found",
    }

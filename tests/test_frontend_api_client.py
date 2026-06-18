from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "streamlit_ui"))

from api_client import ArchimedesApiClient, ArchimedesApiError


def _transport(handler):
    return httpx.MockTransport(handler)


def test_api_client_creates_session_with_default_base_url():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/sessions"
        return httpx.Response(201, json={"session_id": "session-1", "business_need": "Need"})

    client = ArchimedesApiClient(transport=_transport(handler))

    response = client.create_session("Need")

    assert response["session_id"] == "session-1"


def test_api_client_sends_idempotency_key_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Idempotency-Key"] == "idem-1"
        return httpx.Response(200, json={"stage_status": "completed"})

    client = ArchimedesApiClient(transport=_transport(handler))

    response = client.send_message("session-1", "hello", idempotency_key="idem-1")

    assert response["stage_status"] == "completed"


def test_api_client_returns_none_for_missing_artifact():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "missing", "error_code": "artifact_not_found"})

    client = ArchimedesApiClient(transport=_transport(handler))

    assert client.get_latest_artifact("session-1", "hld_generation") is None


def test_api_client_raises_structured_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "boom", "error_code": "internal_error"})

    client = ArchimedesApiClient(transport=_transport(handler))

    with pytest.raises(ArchimedesApiError) as exc:
        client.get_session("session-1")

    assert exc.value.detail == "boom"
    assert exc.value.error_code == "internal_error"

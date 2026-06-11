from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import httpx


DEFAULT_API_URL = "http://localhost:8000/api/v1"


class ArchimedesApiError(RuntimeError):
    def __init__(self, detail: str, *, error_code: str | None = None):
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


@dataclass(slots=True)
class ArchimedesApiClient:
    base_url: str = field(default_factory=lambda: os.getenv("ARCHIMEDES_API_URL", DEFAULT_API_URL))
    timeout: float = 120.0
    transport: httpx.BaseTransport | None = None

    def create_session(
        self,
        business_need: str,
        *,
        title: str | None = None,
        domain: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"business_need": business_need}
        if title:
            payload["title"] = title
        if domain:
            payload["domain"] = domain
        return self._request("POST", "/sessions", json=payload)

    def send_message(
        self,
        session_id: str,
        message: str,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._request(
            "POST",
            f"/sessions/{session_id}/messages",
            json={"message": message},
            headers=headers,
        )

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/sessions/{session_id}")

    def get_pipeline_status(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/sessions/{session_id}/pipeline/status")

    def get_latest_artifact(self, session_id: str, stage: str) -> dict[str, Any] | None:
        try:
            return self._request("GET", f"/sessions/{session_id}/artifacts/{stage}/latest")
        except ArchimedesApiError as exc:
            if exc.error_code == "artifact_not_found":
                return None
            raise

    def get_artifact_version(
        self,
        session_id: str,
        stage: str,
        version: int,
    ) -> dict[str, Any] | None:
        try:
            return self._request("GET", f"/sessions/{session_id}/artifacts/{stage}", params={"version": version})
        except ArchimedesApiError as exc:
            if exc.error_code == "artifact_not_found":
                return None
            raise

    def get_claims(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/sessions/{session_id}/claims")

    def get_evidence(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/sessions/{session_id}/evidence")

    def get_artifact_diff(
        self,
        session_id: str,
        stage: str,
        v1: int,
        v2: int,
    ) -> dict[str, Any] | None:
        try:
            return self._request(
                "GET",
                f"/sessions/{session_id}/artifacts/{stage}/diff",
                params={"v1": v1, "v2": v2},
            )
        except ArchimedesApiError as exc:
            if exc.error_code in {"artifact_not_found", "validation_error"}:
                return None
            raise

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        with httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            response = client.request(method, path, **kwargs)
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = {"detail": response.text, "error_code": None}
            raise ArchimedesApiError(
                str(payload.get("detail", "API request failed")),
                error_code=payload.get("error_code"),
            )
        return response.json()

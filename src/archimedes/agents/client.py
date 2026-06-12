from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class FoundryChatClient:
    """Lightweight shared client wrapper for specialist agent routines."""

    project_endpoint: str
    model: str
    credential: Any


def create_foundry_chat_client() -> FoundryChatClient:
    project_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    if not project_endpoint:
        raise ValueError("Missing FOUNDRY_PROJECT_ENDPOINT.")

    model = os.getenv("DEFAULT_ARCHITECTURE_MODEL", "gpt-4.1")

    try:
        from azure.identity import DefaultAzureCredential
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("azure-identity is required for Foundry client initialization.") from exc

    credential = DefaultAzureCredential()
    return FoundryChatClient(
        project_endpoint=project_endpoint,
        model=model,
        credential=credential,
    )

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class FoundryChatClient:
    """Shared client wrapper for LLM calls via Azure OpenAI (openai SDK)."""

    azure_endpoint: str
    model: str
    api_key: str

    def complete(
        self,
        messages: list,
        *,
        tools: list | None = None,
        response_format: type | None = None,
    ) -> Any:
        from openai import AzureOpenAI

        client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version="2025-01-01-preview",
        )
        kwargs: dict[str, Any] = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if response_format is not None:
            # Use structured output: the model's final (non-tool-call) response
            # is validated against the Pydantic schema.
            kwargs["response_format"] = response_format
            return client.beta.chat.completions.parse(**kwargs)

        return client.chat.completions.create(**kwargs)


def create_foundry_chat_client() -> FoundryChatClient:
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    if not azure_endpoint:
        raise ValueError("Missing AZURE_OPENAI_ENDPOINT.")

    # AzureOpenAI needs the bare resource URL; strip /openai/v1 path if present.
    for suffix in ("/openai/v1/", "/openai/v1"):
        if azure_endpoint.endswith(suffix):
            azure_endpoint = azure_endpoint[: -len(suffix)]
            break

    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing AZURE_OPENAI_API_KEY.")

    model = os.getenv("DEFAULT_ARCHITECTURE_MODEL", "gpt-4.1")

    return FoundryChatClient(
        azure_endpoint=azure_endpoint,
        model=model,
        api_key=api_key,
    )

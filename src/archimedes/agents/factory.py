from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from archimedes.agents.client import FoundryChatClient, create_foundry_chat_client
from archimedes.state.quality_gates import evaluate_quality_gate
from archimedes.tools.foundry_iq import FoundryIQRetriever


AgentTool = Callable[..., Any]


@dataclass(slots=True)
class AgentDefinition:
    name: str
    instructions: str
    tools: dict[str, AgentTool]
    client: FoundryChatClient


class AgentFactory:
    """Build and cache specialist agent definitions from prompts and shared client."""

    def __init__(
        self,
        prompts_root: Path,
        *,
        client: FoundryChatClient | None = None,
        kb_adapter: FoundryIQRetriever | None = None,
    ):
        self.prompts_root = prompts_root
        self.client = client or create_foundry_chat_client()
        self.kb_adapter = kb_adapter or FoundryIQRetriever()
        self._cache: dict[str, AgentDefinition] = {}

    @classmethod
    def from_repo_root(cls, repo_root: str | Path, *, kb_adapter: FoundryIQRetriever | None = None):
        return cls(prompts_root=Path(repo_root) / "prompts", kb_adapter=kb_adapter)

    def get_agent(self, name: str) -> AgentDefinition:
        if name in self._cache:
            return self._cache[name]

        prompt_file = self._prompt_file_for(name)
        instructions = prompt_file.read_text(encoding="utf-8")
        tools = self._toolset_for(name)

        agent = AgentDefinition(
            name=name,
            instructions=instructions,
            tools=tools,
            client=self.client,
        )
        self._cache[name] = agent
        return agent

    def _prompt_file_for(self, name: str) -> Path:
        mapping = {
            "IntakeAgent": self.prompts_root / "intake.md",
            "RequirementsEngineer": self.prompts_root / "requirements.md",
            "OptionsGenerator": self.prompts_root / "options.md",
            "ADRWriter": self.prompts_root / "adr.md",
            "HLDDesigner": self.prompts_root / "hld.md",
            "WAFReviewer": self.prompts_root / "waf.md",
        }
        if name not in mapping:
            raise ValueError(f"Unknown agent name: {name}")
        return mapping[name]

    def _toolset_for(self, name: str) -> dict[str, AgentTool]:
        tools: dict[str, dict[str, AgentTool]] = {
            "IntakeAgent": {
                "foundry_iq_retrieve": self.kb_adapter.retrieve,
            },
            "RequirementsEngineer": {
                "foundry_iq_retrieve": self.kb_adapter.retrieve,
                "evaluate_quality_gate": evaluate_quality_gate,
            },
            "OptionsGenerator": {
                "foundry_iq_retrieve": self.kb_adapter.retrieve,
            },
            "ADRWriter": {
                "foundry_iq_retrieve": self.kb_adapter.retrieve,
            },
            "HLDDesigner": {
                "foundry_iq_retrieve": self.kb_adapter.retrieve,
            },
            "WAFReviewer": {
                "foundry_iq_retrieve": self.kb_adapter.retrieve,
            },
        }

        if name not in tools:
            raise ValueError(f"Unknown agent name: {name}")

        # The retriever internally switches to fixtures when USE_MOCK_KB=true.
        _ = os.getenv("USE_MOCK_KB", "false")
        return tools[name]

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from archimedes.agents.client import FoundryChatClient, create_foundry_chat_client
from archimedes.models.base import new_id
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ClaimType, QualityGateStatus, StageName
from archimedes.models.evidence import EvidenceSource
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.state.quality_gates import evaluate_quality_gate
from archimedes.tools.foundry_iq import FoundryIQRetriever


AgentTool = Callable[..., Any]

# JSON schemas exposed to the LLM for each callable tool
_TOOL_SCHEMAS: dict[str, dict] = {
    "foundry_iq_retrieve": {
        "type": "function",
        "function": {
            "name": "foundry_iq_retrieve",
            "description": (
                "Retrieve relevant architecture reference chunks from Azure AI Search. "
                "Use this to ground your response with patterns, service guidance, and NFR benchmarks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query targeting architecture patterns, Azure services, or NFRs.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    "evaluate_quality_gate": {
        "type": "function",
        "function": {
            "name": "evaluate_quality_gate",
            "description": "Evaluate quality gate checks for the current pipeline stage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stage": {
                        "type": "string",
                        "description": "Pipeline stage name (e.g. 'requirements_extraction').",
                    },
                    "checklist_results": {
                        "type": "object",
                        "description": (
                            "Map of check_id to either a boolean or "
                            "{passed: bool, message: str}."
                        ),
                        "additionalProperties": {
                            "oneOf": [
                                {"type": "boolean"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "passed": {"type": "boolean"},
                                        "message": {"type": "string"},
                                    },
                                    "required": ["passed"],
                                },
                            ]
                        },
                    },
                },
                "required": ["stage", "checklist_results"],
            },
        },
    },
}


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
        self._client = client  # created lazily on first agent call
        self.kb_adapter = kb_adapter or FoundryIQRetriever()
        self._cache: dict[str, AgentDefinition] = {}

    @property
    def client(self) -> FoundryChatClient:
        if self._client is None:
            self._client = create_foundry_chat_client()
        return self._client

    @classmethod
    def from_repo_root(cls, repo_root: str | Path, *, kb_adapter: FoundryIQRetriever | None = None):
        return cls(prompts_root=Path(repo_root) / "prompts", kb_adapter=kb_adapter)

    @classmethod
    def from_env(cls) -> AgentFactory:
        # factory.py → agents/ → archimedes/ → src/ → project root
        repo_root = Path(__file__).resolve().parents[3]
        return cls.from_repo_root(repo_root)

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

    def run_stage(
        self,
        agent_name: str,
        *,
        session_id: str,
        stage: StageName,
        base_version: int,
        user_message: str,
    ) -> StagePatch:
        """Run a specialist agent for a pipeline stage and return the resulting StagePatch."""
        from azure.ai.inference.models import AssistantMessage, SystemMessage, ToolMessage, UserMessage

        agent = self.get_agent(agent_name)
        tool_defs = [_TOOL_SCHEMAS[name] for name in agent.tools if name in _TOOL_SCHEMAS]

        messages: list = [
            SystemMessage(content=agent.instructions),
            UserMessage(content=user_message),
        ]
        collected_evidence: list[EvidenceSource] = []
        quality_gate: QualityGateResult | None = None
        reply = None

        while True:
            response = agent.client.complete(messages, tools=tool_defs or None)
            reply = response.choices[0].message

            if not reply.tool_calls:
                break

            messages.append(AssistantMessage(tool_calls=reply.tool_calls))
            for tc in reply.tool_calls:
                fn_name = tc.function.name
                fn = agent.tools.get(fn_name)
                if fn is None:
                    result_str = json.dumps({"error": f"Unknown tool: {fn_name}"})
                else:
                    args = json.loads(tc.function.arguments or "{}")
                    if fn_name == "foundry_iq_retrieve":
                        args.setdefault("session_id", session_id)
                        evidence_items: list[EvidenceSource] = fn(**args)
                        collected_evidence.extend(evidence_items)
                        result_str = json.dumps([e.model_dump(mode="json") for e in evidence_items])
                    elif fn_name == "evaluate_quality_gate":
                        gate_result = fn(**args)
                        quality_gate = gate_result
                        result_str = json.dumps(gate_result.model_dump(mode="json"))
                    else:
                        raw = fn(**args)
                        result_str = json.dumps(raw) if not isinstance(raw, str) else raw
                messages.append(ToolMessage(tool_call_id=tc.id, content=result_str))

        content = (reply.content if reply is not None else None) or "{}"
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            payload = {"content": content}

        patch_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        stage_run_id = new_id("stage_run")
        stage_value = stage.value if isinstance(stage, StageName) else str(stage)

        claim = ClaimRecord(
            session_id=session_id,
            claim=f"{stage_value} artifact generated by {agent_name}.",
            type=ClaimType.RECOMMENDATION,
            confidence=0.75,
            stage=stage,
            evidence_ids=[e.evidence_id for e in collected_evidence],
        )
        if quality_gate is None:
            quality_gate = QualityGateResult(status=QualityGateStatus.PASSED)

        idempotency_key = hashlib.sha256(
            f"{session_id}:{stage_value}:{stage_run_id}:{patch_hash}".encode()
        ).hexdigest()

        return StagePatch(
            session_id=session_id,
            stage=stage,
            stage_run_id=stage_run_id,
            base_version=base_version,
            target_version=base_version + 1,
            idempotency_key=idempotency_key,
            patch_hash=patch_hash,
            patch=payload,
            claims=[claim],
            evidence_sources=collected_evidence,
            quality_gate_result=quality_gate,
        )

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
        return tools[name]

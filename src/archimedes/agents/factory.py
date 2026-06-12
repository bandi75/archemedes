from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel

from archimedes.agents.client import FoundryChatClient, create_foundry_chat_client
from archimedes.agents.schemas import AGENT_OUTPUT_SCHEMAS
from archimedes.models.base import new_id
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ClaimType, QualityGateStatus, StageName
from archimedes.models.evidence import EvidenceSource
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.state.quality_gates import evaluate_quality_gate
from archimedes.tools.foundry_iq import FoundryIQRetriever


AgentTool = Callable[..., Any]

# JSON schemas exposed to the LLM for each callable tool.
# strict=true is required by beta.chat.completions.parse(); it enforces
# additionalProperties:false and all properties listed in "required".
_TOOL_SCHEMAS: dict[str, dict] = {
    "foundry_iq_retrieve": {
        "type": "function",
        "function": {
            "name": "foundry_iq_retrieve",
            "strict": True,
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
                        "anyOf": [{"type": "integer"}, {"type": "null"}],
                        "description": "Maximum number of results to return. Pass null to use the default of 5.",
                    },
                },
                "required": ["query", "top_k"],
                "additionalProperties": False,
            },
        },
    },
    "evaluate_quality_gate": {
        "type": "function",
        "function": {
            "name": "evaluate_quality_gate",
            "strict": True,
            "description": "Evaluate quality gate checks for the current pipeline stage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stage": {
                        "type": "string",
                        "description": "Pipeline stage name (e.g. 'requirements_extraction').",
                    },
                    "checklist_results": {
                        "type": "string",
                        "description": (
                            "JSON-encoded map of check_id to boolean or "
                            "{\"passed\": bool, \"message\": str}. "
                            "Example: '{\"scale_defined\": true, \"latency_defined\": false}'"
                        ),
                    },
                },
                "required": ["stage", "checklist_results"],
                "additionalProperties": False,
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
    output_schema: type[BaseModel] | None = None


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
            output_schema=AGENT_OUTPUT_SCHEMAS.get(name),
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
        agent = self.get_agent(agent_name)
        tool_defs = [_TOOL_SCHEMAS[name] for name in agent.tools if name in _TOOL_SCHEMAS]

        messages: list = [
            {"role": "system", "content": agent.instructions},
            {"role": "user", "content": user_message},
        ]
        collected_evidence: list[EvidenceSource] = []
        quality_gate: QualityGateResult | None = None
        reply = None

        while True:
            response = agent.client.complete(
                messages,
                tools=tool_defs or None,
                response_format=agent.output_schema,
            )
            reply = response.choices[0].message

            if not reply.tool_calls:
                break

            messages.append({
                "role": "assistant",
                "content": reply.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in reply.tool_calls
                ],
            })
            for tc in reply.tool_calls:
                fn_name = tc.function.name
                fn = agent.tools.get(fn_name)
                if fn is None:
                    result_str = json.dumps({"error": f"Unknown tool: {fn_name}"})
                else:
                    args = json.loads(tc.function.arguments or "{}")
                    if fn_name == "foundry_iq_retrieve":
                        args.setdefault("session_id", session_id)
                        # top_k may be null from strict-mode schema — fall back to default.
                        if args.get("top_k") is None:
                            args.pop("top_k", None)
                        evidence_items: list[EvidenceSource] = fn(**args)
                        collected_evidence.extend(evidence_items)
                        result_str = json.dumps([e.model_dump(mode="json") for e in evidence_items])
                    elif fn_name == "evaluate_quality_gate":
                        # checklist_results arrives as a JSON string in strict-mode tools.
                        raw = args.get("checklist_results", "{}")
                        if isinstance(raw, str):
                            try:
                                args["checklist_results"] = json.loads(raw)
                            except json.JSONDecodeError:
                                args["checklist_results"] = {}
                        gate_result = fn(**args)
                        quality_gate = gate_result
                        result_str = json.dumps(gate_result.model_dump(mode="json"))
                    else:
                        raw = fn(**args)
                        result_str = json.dumps(raw) if not isinstance(raw, str) else raw
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

        # Use the schema-parsed Pydantic object when available (structured output),
        # otherwise fall back to parsing the raw content string.
        if reply is not None and getattr(reply, "parsed", None) is not None:
            payload = reply.parsed.model_dump(mode="json")
        else:
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

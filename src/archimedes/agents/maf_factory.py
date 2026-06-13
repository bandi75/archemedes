"""MAF-backed agent factory using Microsoft Agent Framework.

Drop-in replacement for AgentFactory. The public run_stage() signature is identical;
internally it delegates to agent_framework.Agent with FoundryChatClient instead of the
hand-rolled AzureOpenAI tool-call loop in factory.py.

Switch at startup via ARCHIMEDES_API_AGENT_RUNTIME=maf (default) or =legacy.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field

from archimedes.agents.schemas import AGENT_OUTPUT_SCHEMAS
from archimedes.models.base import new_id
from archimedes.models.claims import ClaimRecord
from archimedes.models.enums import ClaimType, QualityGateStatus, StageName
from archimedes.models.evidence import EvidenceSource
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.state.quality_gates import evaluate_quality_gate as _evaluate_quality_gate
from archimedes.tools.foundry_iq import FoundryIQRetriever

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from LLM response text, handling markdown fences."""
    text = text.strip()
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # ```json ... ``` or ``` ... ```
    for pattern in [r"```json\s*([\s\S]+?)\s*```", r"```\s*([\s\S]+?)\s*```"]:
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    # First { ... } block
    m = re.search(r"\{[\s\S]+\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning("[maf-factory] JSON extraction failed — wrapping raw response as content")
    return {"content": text}


def _run_in_new_loop(coro: Any) -> Any:
    """Run an async coroutine in a fresh event loop inside a worker thread.

    FastAPI sync routes run in a thread pool but do not own an event loop, so
    asyncio.run() works directly there. Using a dedicated thread makes the call
    safe regardless of the calling context (sync route, test, CLI, etc.).

    On Windows, SelectorEventLoop is used explicitly to avoid a ProactorEventLoop
    bug where SSL/TLS transport cleanup callbacks fail after loop.close().
    """
    def _runner() -> Any:
        import sys
        if sys.platform == "win32":
            loop: asyncio.AbstractEventLoop = asyncio.SelectorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                asyncio.set_event_loop(None)
                loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_runner).result()


def _make_tools(
    kb: FoundryIQRetriever,
    session_id: str,
    collected_evidence: list[EvidenceSource],
    quality_gate_holder: list[QualityGateResult | None],
):
    """Return @tool-decorated closures bound to the per-call state containers.

    Each invocation of run_stage() creates fresh closures so evidence and gate
    results stay isolated between concurrent calls.
    """
    from agent_framework import tool  # deferred to avoid import at module load

    @tool(approval_mode="never_require")
    def foundry_iq_retrieve(
        query: Annotated[
            str,
            Field(description="Search query targeting architecture patterns, Azure services, or NFRs."),
        ],
        top_k: Annotated[
            int,
            Field(description="Maximum number of results to return. Default is 5."),
        ] = 5,
    ) -> str:
        """Retrieve relevant architecture reference chunks from the knowledge base.

        Use this to ground your response with patterns, service guidance, and NFR benchmarks
        before producing any artifact content.
        """
        items = kb.retrieve(query=query, top_k=top_k, session_id=session_id)
        collected_evidence.extend(items)
        logger.info("[maf-factory] foundry_iq_retrieve query=%r → %d items", query[:80], len(items))
        return json.dumps([e.model_dump(mode="json") for e in items])

    @tool(approval_mode="never_require")
    def evaluate_quality_gate(
        stage: Annotated[
            str,
            Field(description="Pipeline stage name, e.g. 'requirements_extraction'."),
        ],
        checklist_results: Annotated[
            str,
            Field(description="JSON-encoded map of check_id to bool or {passed, message}."),
        ],
    ) -> str:
        """Evaluate quality gate checks for the current pipeline stage.

        Call this after producing your artifact to record which quality checks passed.
        """
        try:
            checks = json.loads(checklist_results) if isinstance(checklist_results, str) else checklist_results
        except json.JSONDecodeError:
            checks = {}
        gate = _evaluate_quality_gate(stage=stage, checklist_results=checks)
        quality_gate_holder[0] = gate
        return json.dumps(gate.model_dump(mode="json"))

    return foundry_iq_retrieve, evaluate_quality_gate


# ---------------------------------------------------------------------------
# Agent → tool mapping
# ---------------------------------------------------------------------------

_AGENT_TOOLS: dict[str, list[str]] = {
    "IntakeAgent":           ["foundry_iq_retrieve"],
    "RequirementsEngineer":  ["foundry_iq_retrieve", "evaluate_quality_gate"],
    "OptionsGenerator":      ["foundry_iq_retrieve"],
    "ADRWriter":             ["foundry_iq_retrieve"],
    "HLDDesigner":           ["foundry_iq_retrieve"],
    "WAFReviewer":           ["foundry_iq_retrieve"],
}

_AGENT_PROMPTS: dict[str, str] = {
    "IntakeAgent":          "intake.md",
    "RequirementsEngineer": "requirements.md",
    "OptionsGenerator":     "options.md",
    "ADRWriter":            "adr.md",
    "HLDDesigner":          "hld.md",
    "WAFReviewer":          "waf.md",
}


# ---------------------------------------------------------------------------
# MAFAgentFactory
# ---------------------------------------------------------------------------

class MAFAgentFactory:
    """Agent factory backed by Microsoft Agent Framework.

    Identical public interface to AgentFactory so StageController needs no changes.
    Internally:
      - FoundryChatClient wraps the Foundry Responses API (FOUNDRY_PROJECT_ENDPOINT)
      - Agent.run() owns the tool-call loop — no manual round-trip code
      - @tool closures capture evidence and quality gate results per call
      - Async MAF execution bridges to sync callers via a dedicated worker thread
    """

    def __init__(
        self,
        prompts_root: Path,
        *,
        kb_adapter: FoundryIQRetriever | None = None,
    ) -> None:
        self.prompts_root = Path(prompts_root)
        self.kb_adapter = kb_adapter or FoundryIQRetriever()
        self._maf_client: Any = None  # created lazily on first run_stage() call

    # ------------------------------------------------------------------
    # Client — lazily created so the server can start without the endpoint
    # ------------------------------------------------------------------

    @property
    def maf_client(self) -> Any:
        if self._maf_client is None:
            from agent_framework.foundry import FoundryChatClient
            from azure.identity import DefaultAzureCredential

            endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
            if not endpoint:
                raise ValueError(
                    "FOUNDRY_PROJECT_ENDPOINT is required for MAF runtime. "
                    "Set ARCHIMEDES_API_AGENT_RUNTIME=legacy to use the OpenAI fallback."
                )
            model = os.getenv("DEFAULT_ARCHITECTURE_MODEL", "gpt-4.1")
            logger.info(
                "[maf-factory] creating FoundryChatClient endpoint=%s model=%s",
                endpoint[:70],
                model,
            )
            self._maf_client = FoundryChatClient(
                project_endpoint=endpoint,
                model=model,
                credential=DefaultAzureCredential(),
            )
        return self._maf_client

    # ------------------------------------------------------------------
    # Class-level constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_env(cls) -> MAFAgentFactory:
        # maf_factory.py → agents/ → archimedes/ → src/ → repo root
        repo_root = Path(__file__).resolve().parents[3]
        return cls(prompts_root=repo_root / "prompts")

    @classmethod
    def from_repo_root(cls, repo_root: str | Path, *, kb_adapter: FoundryIQRetriever | None = None) -> MAFAgentFactory:
        return cls(prompts_root=Path(repo_root) / "prompts", kb_adapter=kb_adapter)

    # ------------------------------------------------------------------
    # Public sync interface — identical to AgentFactory
    # ------------------------------------------------------------------

    def run_stage(
        self,
        agent_name: str,
        *,
        session_id: str,
        stage: StageName,
        base_version: int,
        user_message: str,
    ) -> StagePatch:
        """Execute an LLM agent stage via MAF and return the resulting StagePatch.

        Bridges the sync StageController interface to MAF's async Agent.run() by
        running the coroutine in a fresh event loop on a worker thread.
        """
        return _run_in_new_loop(
            self._run_stage_async(
                agent_name,
                session_id=session_id,
                stage=stage,
                base_version=base_version,
                user_message=user_message,
            )
        )

    # ------------------------------------------------------------------
    # Async implementation
    # ------------------------------------------------------------------

    async def _run_stage_async(
        self,
        agent_name: str,
        *,
        session_id: str,
        stage: StageName,
        base_version: int,
        user_message: str,
    ) -> StagePatch:
        from agent_framework import Agent

        if agent_name not in _AGENT_PROMPTS:
            raise ValueError(f"Unknown agent: {agent_name!r}")

        collected_evidence: list[EvidenceSource] = []
        quality_gate_holder: list[QualityGateResult | None] = [None]

        foundry_iq_tool, gate_tool = _make_tools(
            self.kb_adapter, session_id, collected_evidence, quality_gate_holder
        )
        tool_names = _AGENT_TOOLS[agent_name]
        tools = []
        if "foundry_iq_retrieve" in tool_names:
            tools.append(foundry_iq_tool)
        if "evaluate_quality_gate" in tool_names:
            tools.append(gate_tool)

        instructions = (self.prompts_root / _AGENT_PROMPTS[agent_name]).read_text(encoding="utf-8")

        agent = Agent(
            client=self.maf_client,
            name=agent_name,
            instructions=instructions,
            tools=tools,
        )

        logger.info(
            "[maf-factory] agent.run agent=%s stage=%s session=%s",
            agent_name,
            stage,
            session_id,
        )
        result = await agent.run(user_message)
        response_text = result.text if hasattr(result, "text") else str(result)
        logger.info(
            "[maf-factory] agent.run complete agent=%s response_len=%d evidence=%d",
            agent_name,
            len(response_text),
            len(collected_evidence),
        )

        payload = _extract_json(response_text)

        # Validate against the per-agent Pydantic schema when available
        schema_cls = AGENT_OUTPUT_SCHEMAS.get(agent_name)
        if schema_cls is not None:
            try:
                payload = schema_cls.model_validate(payload).model_dump(mode="json")
            except Exception as exc:
                logger.warning(
                    "[maf-factory] schema validation failed agent=%s: %s", agent_name, exc
                )

        return self._build_patch(
            session_id=session_id,
            stage=stage,
            agent_name=agent_name,
            base_version=base_version,
            payload=payload,
            collected_evidence=collected_evidence,
            quality_gate=quality_gate_holder[0],
        )

    # ------------------------------------------------------------------
    # StagePatch builder — identical logic to AgentFactory
    # ------------------------------------------------------------------

    @staticmethod
    def _build_patch(
        *,
        session_id: str,
        stage: StageName,
        agent_name: str,
        base_version: int,
        payload: dict[str, Any],
        collected_evidence: list[EvidenceSource],
        quality_gate: QualityGateResult | None,
    ) -> StagePatch:
        patch_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        stage_run_id = new_id("stage_run")
        stage_value = stage.value if isinstance(stage, StageName) else str(stage)

        claim = ClaimRecord(
            session_id=session_id,
            claim=f"{stage_value} artifact generated by {agent_name} via MAF.",
            type=ClaimType.RECOMMENDATION,
            confidence=0.75,
            stage=stage,
            evidence_ids=[e.evidence_id for e in collected_evidence],
        )
        quality_gate = quality_gate or QualityGateResult(status=QualityGateStatus.PASSED)
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

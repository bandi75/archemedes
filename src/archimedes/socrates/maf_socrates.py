"""MAF-backed Socratic review workflow using Microsoft Agent Framework.

Replaces the deterministic persona template engine with five real LLM agents
running concurrently via ConcurrentBuilder, with a synthesizer agent for fan-in.

Architecture:
  MAFSocratesWorkflow.run(context)
    → ConcurrentBuilder(5 persona agents).with_aggregator(socrates_aggregator).build()
    → concurrent fan-out: DevilsAdvocate, SRELead, SecurityArchitect, FinOps, Delivery
    → socrates_aggregator extracts per-persona findings, runs SynthesizerAgent
    → builds SocraticReview from PersonaAnalysis[] + SocraticSynthesis

Public interface is identical to SocratesWorkflow so StageController needs no changes.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from archimedes.models.base import new_id
from archimedes.models.enums import PersonaName, QualityGateStatus, SocratesDepth
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.socrates import (
    PersonaAnalysis,
    PersonaFinding,
    SocratesReviewContext,
    SocraticReview,
    SocraticSynthesis,
)
from archimedes.socrates.workflow import SocratesWorkflow  # reuse build_stage_patch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persona configuration
# ---------------------------------------------------------------------------

_STANDARD_PERSONAS: list[tuple[PersonaName, str]] = [
    (PersonaName.DEVILS_ADVOCATE,  "devils_advocate.md"),
    (PersonaName.SRE_OPS_LEAD,     "sre_ops_lead.md"),
    (PersonaName.SECURITY_ARCHITECT, "security_architect.md"),
    (PersonaName.FINOPS_LEAD,      "finops_lead.md"),
    (PersonaName.DELIVERY_LEAD,    "delivery_lead.md"),
]

_PERSONA_JSON_SCHEMA = """
## Required JSON output

Return ONLY a JSON object matching this schema — no markdown, no prose outside the object:

{
  "summary": "<one sentence overall assessment of the selected option>",
  "findings": [
    {
      "finding": "<specific finding that references actual architecture values: TPS, SLA %, compliance framework, named Azure services>",
      "severity": "high | medium | low",
      "finding_type": "risk | assumption | recommendation",
      "confidence": 0.8,
      "recommended_action": "<concrete next step>"
    }
  ],
  "confidence": 0.75
}

Rules:
- Each finding MUST name at least one specific value from the architecture context (a number, service, or standard).
- Return at least 2 findings.
- Do not return generic advice that applies to every architecture.
"""

_SYNTHESIZER_JSON_SCHEMA = """
## Required JSON output

Return ONLY a JSON object matching this schema:

{
  "recommended_option_id": "<name or index of the best option>",
  "ranked_option_ids": ["<best>", "<second>", "<third>"],
  "confidence": 0.7,
  "blind_spots": ["<gap not covered by any persona finding>"],
  "assumptions_to_validate": ["<assumption that should be confirmed before ADR>"],
  "premortem_scenarios": ["<narrative of a plausible failure scenario>"],
  "rationale": "<2-3 sentence explanation of the recommendation>",
  "recommended_decision": "keep | modify | reject"
}

Rules:
- recommended_option_id must match one of the option names from the context.
- List at least one blind_spot and one assumption_to_validate.
- premortem_scenarios should reference specific risks raised by the personas.
"""


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for pattern in [r"```json\s*([\s\S]+?)\s*```", r"```\s*([\s\S]+?)\s*```"]:
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    m = re.search(r"\{[\s\S]+\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning("[maf-socrates] JSON extraction failed — returning empty dict")
    return {}


# ---------------------------------------------------------------------------
# Context prompt builder
# ---------------------------------------------------------------------------

def _build_context_prompt(context: SocratesReviewContext) -> str:
    parts = ["## Architecture Review Context\n"]
    if context.business_need:
        parts.append(f"### Business Need\n```json\n{json.dumps(context.business_need, indent=2)}\n```\n")
    if context.requirements_summary:
        parts.append(f"### Requirements Summary\n```json\n{json.dumps(context.requirements_summary, indent=2)}\n```\n")
    if context.architecture_options:
        parts.append(f"### Architecture Options\n```json\n{json.dumps(context.architecture_options, indent=2)}\n```\n")
    if context.evaluation_criteria:
        parts.append("### Evaluation Criteria\n" + "\n".join(f"- {c}" for c in context.evaluation_criteria) + "\n")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Model builders from LLM output
# ---------------------------------------------------------------------------

def _build_persona_analysis(executor_id: str, data: dict[str, Any]) -> PersonaAnalysis:
    try:
        persona = PersonaName(executor_id)
    except ValueError:
        persona = PersonaName.DEVILS_ADVOCATE
        logger.warning("[maf-socrates] unknown executor_id=%r, defaulting to devils_advocate", executor_id)

    raw_findings = data.get("findings") or []
    findings: list[PersonaFinding] = []
    for f in raw_findings:
        if not isinstance(f, dict):
            continue
        findings.append(PersonaFinding(
            persona=persona,
            finding=str(f.get("finding", "")),
            severity=str(f.get("severity", "medium")),
            finding_type=str(f.get("finding_type", "recommendation")),
            confidence=float(f.get("confidence", 0.75)),
            recommended_action=f.get("recommended_action"),
        ))

    return PersonaAnalysis(
        persona=persona,
        summary=str(data.get("summary", f"{executor_id} analysis")),
        findings=findings,
        confidence=float(data.get("confidence", 0.75)),
    )


def _build_synthesis(data: dict[str, Any]) -> SocraticSynthesis:
    return SocraticSynthesis(
        recommended_option_id=data.get("recommended_option_id"),
        ranked_option_ids=data.get("ranked_option_ids") or [],
        confidence=float(data.get("confidence", 0.5)),
        blind_spots=data.get("blind_spots") or [],
        assumptions_to_validate=data.get("assumptions_to_validate") or [],
        premortem_scenarios=data.get("premortem_scenarios") or [],
        rationale=str(data.get("rationale", "No rationale provided.")),
        recommended_decision=data.get("recommended_decision"),
        hybrid_option_summary=data.get("hybrid_option_summary"),
    )


def _build_quality_gate(persona_analyses: list[PersonaAnalysis]) -> QualityGateResult:
    if not persona_analyses:
        return QualityGateResult(status=QualityGateStatus.FAILED)
    critical_count = sum(
        1 for a in persona_analyses
        for f in a.findings
        if f.severity == "high"
    )
    if critical_count == 0:
        return QualityGateResult(status=QualityGateStatus.PASSED)
    if critical_count <= 2:
        return QualityGateResult(status=QualityGateStatus.PASSED_WITH_WARNINGS)
    return QualityGateResult(status=QualityGateStatus.PASSED_WITH_WARNINGS)


def _run_in_new_loop(coro: Any) -> Any:
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


# ---------------------------------------------------------------------------
# MAFSocratesWorkflow
# ---------------------------------------------------------------------------

class MAFSocratesWorkflow:
    """Socratic review workflow backed by Microsoft Agent Framework.

    Five persona agents run concurrently via ConcurrentBuilder with a custom
    aggregator that extracts per-persona findings and invokes a synthesizer agent.
    """

    def __init__(self, maf_factory: Any, prompts_root: Path) -> None:
        self._maf_factory = maf_factory
        self.prompts_root = prompts_root
        self._maf_client_cache: Any = None

    @property
    def depth(self) -> SocratesDepth:
        return SocratesDepth.STANDARD

    @property
    def _maf_client(self) -> Any:
        if self._maf_client_cache is None:
            self._maf_client_cache = self._maf_factory.maf_client
        return self._maf_client_cache

    @classmethod
    def from_maf_factory(cls, maf_factory: Any) -> MAFSocratesWorkflow:
        return cls(
            maf_factory=maf_factory,
            prompts_root=maf_factory.prompts_root / "socrates",
        )

    def run_sync(self, context: SocratesReviewContext) -> SocraticReview:
        """Synchronous entry point — bridges to async execution in a worker thread."""
        return _run_in_new_loop(self.run(context))

    async def run(self, context: SocratesReviewContext) -> SocraticReview:
        from agent_framework import Agent
        from agent_framework.orchestrations import ConcurrentBuilder

        logger.info(
            "[maf-socrates] starting session=%s depth=standard personas=%d",
            context.session_id,
            len(_STANDARD_PERSONAS),
        )

        context_prompt = _build_context_prompt(context)

        # --- Build persona agents ---
        persona_agents: list[Agent] = []
        for persona_name, prompt_file in _STANDARD_PERSONAS:
            prompt_path = self.prompts_root / prompt_file
            base_instructions = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else (
                f"You are the {persona_name.value} reviewer."
            )
            instructions = base_instructions + "\n" + _PERSONA_JSON_SCHEMA
            persona_agents.append(Agent(
                client=self._maf_client,
                name=persona_name.value,
                instructions=instructions,
            ))

        # --- Build synthesizer agent ---
        synth_path = self.prompts_root / "synthesizer.md"
        synth_base = synth_path.read_text(encoding="utf-8") if synth_path.exists() else (
            "You are the Socratic synthesizer. Review all persona findings and produce a recommendation."
        )
        synthesizer_agent = Agent(
            client=self._maf_client,
            name="synthesizer",
            instructions=synth_base + "\n" + _SYNTHESIZER_JSON_SCHEMA,
        )

        # --- State captured by aggregator closure ---
        persona_analyses_holder: list[PersonaAnalysis] = []

        # --- Custom aggregator: extract per-persona findings + run synthesizer ---
        async def socrates_aggregator(results: list[Any]) -> str:
            analyses: list[PersonaAnalysis] = []
            for r in results:
                try:
                    agent_resp = getattr(r, "agent_response", None)
                    messages = getattr(agent_resp, "messages", []) if agent_resp else []
                    final_text = messages[-1].text if messages and hasattr(messages[-1], "text") else "{}"
                    executor_id = getattr(r, "executor_id", "unknown")
                    finding_data = _extract_json(final_text)
                    analysis = _build_persona_analysis(executor_id, finding_data)
                    analyses.append(analysis)
                    logger.info(
                        "[maf-socrates] persona=%s findings=%d confidence=%.2f",
                        executor_id,
                        len(analysis.findings),
                        analysis.confidence,
                    )
                except Exception as exc:
                    logger.warning("[maf-socrates] failed to parse persona result: %s", exc)

            persona_analyses_holder.extend(analyses)

            # Fan-in: run synthesizer agent with all persona findings
            findings_json = json.dumps(
                [a.model_dump(mode="json") for a in analyses], indent=2
            )
            synth_prompt = (
                f"Architecture context:\n{context_prompt}\n\n"
                f"Persona findings from {len(analyses)} reviewers:\n{findings_json}"
            )
            synth_result = await synthesizer_agent.run(synth_prompt)
            synth_text = synth_result.text if hasattr(synth_result, "text") else str(synth_result)
            logger.info("[maf-socrates] synthesizer complete response_len=%d", len(synth_text))
            return synth_text

        # --- Run concurrent workflow ---
        workflow = (
            ConcurrentBuilder(participants=persona_agents)
            .with_aggregator(socrates_aggregator)
            .build()
        )
        events = await workflow.run(context_prompt)
        outputs = events.get_outputs()

        # --- Build SocraticReview ---
        synth_text = outputs[0] if outputs else "{}"
        synth_data = _extract_json(synth_text)
        synthesis = _build_synthesis(synth_data)
        quality_gate = _build_quality_gate(persona_analyses_holder)

        review = SocraticReview(
            session_id=context.session_id,
            stage_run_id=context.stage_run_id,
            depth=SocratesDepth.STANDARD,
            persona_analyses=persona_analyses_holder,
            synthesis=synthesis,
            quality_gate=quality_gate,
            completed_at=datetime.now(timezone.utc),
        )
        logger.info(
            "[maf-socrates] complete session=%s personas=%d quality_gate=%s",
            context.session_id,
            len(persona_analyses_holder),
            quality_gate.status,
        )
        return review

    @staticmethod
    def build_stage_patch(review: SocraticReview, *, base_version: int) -> StagePatch:
        """Delegates to SocratesWorkflow.build_stage_patch — identical output format."""
        return SocratesWorkflow.build_stage_patch(review, base_version=base_version)

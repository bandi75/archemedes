from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from archimedes.models.enums import PersonaName, SocratesDepth, StageName
from archimedes.models.patches import StagePatch
from archimedes.models.socrates import (
    PersonaAnalysis,
    SocratesReviewContext,
    SocraticReview,
)

from .dispatcher import DispatcherExecutor
from .persona import PersonaExecutor
from .synthesizer import SocratesSynthesizerExecutor


DEPTH_PERSONAS: dict[SocratesDepth, list[PersonaName]] = {
    SocratesDepth.LIGHT: [
        PersonaName.DEVILS_ADVOCATE,
        PersonaName.SRE_OPS_LEAD,
        PersonaName.DELIVERY_LEAD,
    ],
    SocratesDepth.STANDARD: [
        PersonaName.DEVILS_ADVOCATE,
        PersonaName.SRE_OPS_LEAD,
        PersonaName.SECURITY_ARCHITECT,
        PersonaName.FINOPS_LEAD,
        PersonaName.DELIVERY_LEAD,
    ],
    SocratesDepth.DEEP: [
        PersonaName.DEVILS_ADVOCATE,
        PersonaName.SRE_OPS_LEAD,
        PersonaName.SECURITY_ARCHITECT,
        PersonaName.FINOPS_LEAD,
        PersonaName.DELIVERY_LEAD,
        PersonaName.CUSTOMER_BIZ_SPONSOR,
        PersonaName.DATA_ARCHITECT,
    ],
}

MINIMUM_PERSONAS: dict[SocratesDepth, int] = {
    SocratesDepth.LIGHT: 2,
    SocratesDepth.STANDARD: 4,
    SocratesDepth.DEEP: 5,
}

PROMPT_FILES: dict[PersonaName, str] = {
    PersonaName.DEVILS_ADVOCATE: "devils_advocate.md",
    PersonaName.SRE_OPS_LEAD: "sre_ops_lead.md",
    PersonaName.SECURITY_ARCHITECT: "security_architect.md",
    PersonaName.FINOPS_LEAD: "finops_lead.md",
    PersonaName.DELIVERY_LEAD: "delivery_lead.md",
}


@dataclass(slots=True)
class SocratesWorkflow:
    depth: SocratesDepth
    dispatcher: DispatcherExecutor
    persona_executors: list[PersonaExecutor]
    synthesizer: SocratesSynthesizerExecutor
    include_cross_examiner: bool = False

    async def run(self, context: SocratesReviewContext) -> SocraticReview:
        dispatch = await self.dispatcher.dispatch(context)
        analyses = await asyncio.gather(
            *(executor.run(dispatch.context) for executor in self.persona_executors)
        )
        cross_examination = self._cross_examine(analyses) if self.include_cross_examiner else None
        return await self.synthesizer.synthesize(
            context,
            list(analyses),
            cross_examination=cross_examination,
        )

    def run_sync(self, context: SocratesReviewContext) -> SocraticReview:
        return asyncio.run(self.run(context))

    @staticmethod
    def build_stage_patch(review: SocraticReview, *, base_version: int) -> StagePatch:
        review_payload = review.model_dump(mode="json")
        patch_payload = {"socratic_review": review_payload}
        patch_hash = _compute_hash(patch_payload)
        return StagePatch(
            session_id=review.session_id,
            stage=StageName.SOCRATIC_REVIEW,
            stage_run_id=review.stage_run_id,
            base_version=base_version,
            target_version=base_version + 1,
            idempotency_key=_idempotency_key(review.session_id, review.stage_run_id, patch_hash),
            patch_hash=patch_hash,
            patch=patch_payload,
            claims=[],
            evidence_sources=[],
            quality_gate_result=review.quality_gate,
        )

    @staticmethod
    def _cross_examine(analyses: list[PersonaAnalysis]) -> str:
        personas = ", ".join(str(analysis.persona) for analysis in analyses)
        return f"Cross-examination reviewed tensions across: {personas}."


def build_socrates_workflow(
    depth: str | SocratesDepth = SocratesDepth.STANDARD,
    *,
    prompts_root: str | Path | None = None,
) -> SocratesWorkflow:
    depth_value = SocratesDepth(depth)
    root = Path(prompts_root) if prompts_root else _default_prompts_root()
    personas = DEPTH_PERSONAS[depth_value]
    persona_executors = [
        PersonaExecutor(persona=persona, prompt=_read_prompt(root, persona))
        for persona in personas
    ]
    synthesizer = SocratesSynthesizerExecutor(
        prompt=_read_synthesizer_prompt(root),
        minimum_personas=MINIMUM_PERSONAS[depth_value],
    )
    return SocratesWorkflow(
        depth=depth_value,
        dispatcher=DispatcherExecutor(recipients=[persona.value for persona in personas]),
        persona_executors=persona_executors,
        synthesizer=synthesizer,
        include_cross_examiner=depth_value == SocratesDepth.DEEP,
    )


def _default_prompts_root() -> Path:
    return Path(__file__).resolve().parents[3] / "prompts" / "socrates"


def _read_prompt(root: Path, persona: PersonaName) -> str:
    filename = PROMPT_FILES.get(persona)
    if filename is None:
        return f"You are the {persona.value} Socrates reviewer. Return concise structured JSON."
    return (root / filename).read_text(encoding="utf-8")


def _read_synthesizer_prompt(root: Path) -> str:
    return (root / "synthesizer.md").read_text(encoding="utf-8")


def _compute_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _idempotency_key(session_id: str, stage_run_id: str, patch_hash: str) -> str:
    return hashlib.sha256(
        f"{session_id}:{StageName.SOCRATIC_REVIEW.value}:{stage_run_id}:{patch_hash}".encode("utf-8")
    ).hexdigest()

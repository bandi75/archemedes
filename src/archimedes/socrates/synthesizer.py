from __future__ import annotations

from dataclasses import dataclass

from archimedes.models.enums import QualityGateStatus
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.socrates import (
    PersonaAnalysis,
    SocratesReviewContext,
    SocraticReview,
    SocraticSynthesis,
)
from archimedes.models.base import utc_now


@dataclass(slots=True)
class SocratesSynthesizerExecutor:
    prompt: str
    minimum_personas: int

    async def synthesize(
        self,
        context: SocratesReviewContext,
        persona_analyses: list[PersonaAnalysis],
        *,
        cross_examination: str | None = None,
    ) -> SocraticReview:
        completed = [analysis for analysis in persona_analyses if not analysis.failed]
        option_ids = self._option_ids(context)
        recommended = option_ids[0] if option_ids else None
        blind_spots = [
            finding.finding
            for analysis in completed
            for finding in analysis.findings
            if finding.severity in {"high", "critical"}
        ][:5]
        assumptions = [
            finding.finding
            for analysis in completed
            for finding in analysis.findings
            if finding.requires_validation
        ][:5]
        premortem = self._premortem(completed)
        confidence = self._confidence(completed)
        gate = self._quality_gate(
            completed_count=len(completed),
            recommended_option_id=recommended,
            blind_spots=blind_spots,
            premortem_scenarios=premortem,
        )

        synthesis = SocraticSynthesis(
            recommended_option_id=recommended,
            ranked_option_ids=option_ids,
            confidence=confidence,
            blind_spots=blind_spots,
            assumptions_to_validate=assumptions,
            premortem_scenarios=premortem,
            hybrid_option_summary=(
                "Combine the leading option with explicit security, operations, and cost controls."
                if recommended
                else None
            ),
            rationale=(
                f"Recommend {recommended} because it is the strongest starting point, "
                "provided the highlighted assumptions and controls are validated."
                if recommended
                else "No option could be recommended because no options were supplied."
            ),
            claim_classifications=[
                {
                    "claim": finding.finding,
                    "type": finding.finding_type,
                    "persona": analysis.persona,
                }
                for analysis in completed
                for finding in analysis.findings
            ],
        )

        return SocraticReview(
            session_id=context.session_id,
            stage_run_id=context.stage_run_id,
            depth=context.depth,
            persona_analyses=persona_analyses,
            cross_examination=cross_examination,
            synthesis=synthesis,
            quality_gate=gate,
            completed_at=utc_now(),
        )

    def _quality_gate(
        self,
        *,
        completed_count: int,
        recommended_option_id: str | None,
        blind_spots: list[str],
        premortem_scenarios: list[str],
    ) -> QualityGateResult:
        blocking: list[str] = []
        warnings: list[str] = []
        if completed_count < self.minimum_personas:
            blocking.append("Minimum completed Socrates personas not met.")
        if not recommended_option_id:
            blocking.append("Socrates synthesis did not recommend an option.")
        if not premortem_scenarios:
            blocking.append("Socrates synthesis did not include pre-mortem scenarios.")
        if not blind_spots:
            warnings.append("Socrates synthesis did not identify high-severity blind spots.")

        if blocking:
            return QualityGateResult(
                status=QualityGateStatus.FAILED,
                blocking_failures=blocking,
                warnings=warnings,
                user_override_allowed=False,
            )
        return QualityGateResult(
            status=QualityGateStatus.PASSED_WITH_WARNINGS if warnings else QualityGateStatus.PASSED,
            warnings=warnings,
        )

    @staticmethod
    def _option_ids(context: SocratesReviewContext) -> list[str]:
        return [
            str(option.get("option_id") or option.get("id") or option.get("name"))
            for option in context.architecture_options
            if option.get("option_id") or option.get("id") or option.get("name")
        ]

    @staticmethod
    def _confidence(completed: list[PersonaAnalysis]) -> float:
        if not completed:
            return 0.0
        return round(sum(analysis.confidence for analysis in completed) / len(completed), 3)

    @staticmethod
    def _premortem(completed: list[PersonaAnalysis]) -> list[str]:
        findings = [
            finding.finding
            for analysis in completed
            for finding in analysis.findings
        ]
        if not findings:
            return []
        return [
            "The decision fails if critical assumptions remain unvalidated before implementation.",
            "The design degrades if operational, security, cost, and delivery controls are not added to the HLD.",
        ]

from __future__ import annotations

from dataclasses import dataclass

from archimedes.models.enums import PersonaName
from archimedes.models.socrates import PersonaAnalysis, PersonaFinding, SocratesReviewContext


PERSONA_LABELS: dict[PersonaName, str] = {
    PersonaName.DEVILS_ADVOCATE: "Devil's Advocate",
    PersonaName.SRE_OPS_LEAD: "SRE / Operations Lead",
    PersonaName.SECURITY_ARCHITECT: "Security Architect",
    PersonaName.FINOPS_LEAD: "FinOps Lead",
    PersonaName.DELIVERY_LEAD: "Delivery Lead",
    PersonaName.CUSTOMER_BIZ_SPONSOR: "Customer / Business Sponsor",
    PersonaName.DATA_ARCHITECT: "Data Architect",
}


@dataclass(slots=True)
class PersonaExecutor:
    persona: PersonaName
    prompt: str

    async def run(self, context: SocratesReviewContext) -> PersonaAnalysis:
        # MVP fallback path: deterministic structured analysis until live MAF calls are wired.
        options = context.architecture_options or [{"option_id": "OPT-UNKNOWN", "summary": "No option supplied"}]
        primary = options[0]
        option_id = str(primary.get("option_id") or primary.get("id") or primary.get("name") or "OPT-UNKNOWN")
        finding = self._finding_for(option_id, context)
        label = PERSONA_LABELS.get(self.persona, self.persona.value)
        return PersonaAnalysis(
            persona=self.persona,
            summary=f"{label} reviewed {len(options)} option(s) and found actionable risk.",
            findings=[finding],
            confidence=finding.confidence,
        )

    def _finding_for(self, option_id: str, context: SocratesReviewContext) -> PersonaFinding:
        if self.persona == PersonaName.DEVILS_ADVOCATE:
            return PersonaFinding(
                persona=self.persona,
                target_option_id=option_id,
                finding="The leading option depends on assumptions that need explicit validation before commitment.",
                severity="high",
                finding_type="assumption",
                confidence=0.78,
                requires_validation=True,
                recommended_action="Record the assumption in the ADR and validate it during the next stage.",
            )
        if self.persona == PersonaName.SRE_OPS_LEAD:
            return PersonaFinding(
                persona=self.persona,
                target_option_id=option_id,
                finding="Operational readiness needs clearer telemetry, replay, and incident-response paths.",
                severity="medium",
                confidence=0.8,
                recommended_action="Add monitoring, alerting, replay, and runbook requirements to the HLD.",
            )
        if self.persona == PersonaName.SECURITY_ARCHITECT:
            return PersonaFinding(
                persona=self.persona,
                target_option_id=option_id,
                finding="Trust boundaries, identity flows, and sensitive-data handling must be explicit.",
                severity="high",
                confidence=0.82,
                requires_validation=True,
                recommended_action="Add threat-model notes and least-privilege controls before approval.",
            )
        if self.persona == PersonaName.FINOPS_LEAD:
            return PersonaFinding(
                persona=self.persona,
                target_option_id=option_id,
                finding="Cost sensitivity may grow with throughput, retention, cross-region traffic, and observability volume.",
                severity="medium",
                confidence=0.74,
                recommended_action="Carry sizing assumptions and cost drivers into the decision record.",
            )
        if self.persona == PersonaName.DELIVERY_LEAD:
            return PersonaFinding(
                persona=self.persona,
                target_option_id=option_id,
                finding="Delivery risk depends on team familiarity, rollout sequencing, and dependency readiness.",
                severity="medium",
                confidence=0.76,
                recommended_action="Define an MVP slice and defer nonessential topology complexity.",
            )
        if self.persona == PersonaName.CUSTOMER_BIZ_SPONSOR:
            return PersonaFinding(
                persona=self.persona,
                target_option_id=option_id,
                finding="Business value depends on time-to-value and clear acceptance criteria.",
                severity="medium",
                confidence=0.7,
                recommended_action="Tie architecture milestones to measurable business outcomes.",
            )
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding="Data ownership, lineage, retention, and consistency decisions need explicit documentation.",
            severity="medium",
            confidence=0.72,
            recommended_action="Add data lifecycle and consistency notes to the HLD.",
        )

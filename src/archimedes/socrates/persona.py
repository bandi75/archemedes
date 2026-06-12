from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

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


@dataclass(frozen=True)
class _ArchSignals:
    """Signals extracted from SocratesReviewContext so persona findings reference the real architecture."""

    option_name: str
    option_summary: str
    services: list[str]
    key_risks: list[str]
    scale_hint: str
    availability_target: str
    compliance_flags: list[str]
    cost_score: int        # 1–10 from TradeOffScores; higher = more expensive
    component_count: int

    @classmethod
    def extract(cls, context: SocratesReviewContext, option_id: str) -> "_ArchSignals":
        primary = _primary_option(context.architecture_options, option_id)
        components = primary.get("components") or []
        services = [
            str(c.get("azure_service") or c.get("name") or "")
            for c in components
            if isinstance(c, dict)
        ]
        services = [s for s in services if s][:6]

        trade_offs = primary.get("trade_off_scores") or {}
        cost_score = int(trade_offs.get("cost") or 5)

        # Combine both free-text fields for signal extraction
        raw_input = str(context.business_need.get("raw_input") or "")
        user_message = str(context.business_need.get("latest_user_message") or "")
        combined_text = f"{raw_input} {user_message}"
        reqs = context.requirements_summary

        return cls(
            option_name=str(primary.get("name") or option_id),
            option_summary=str(primary.get("summary") or ""),
            services=services,
            key_risks=list(primary.get("key_risks") or [])[:3],
            scale_hint=_extract_scale(combined_text, reqs),
            availability_target=_extract_availability(combined_text, reqs),
            compliance_flags=_extract_compliance(combined_text, reqs),
            cost_score=cost_score,
            component_count=len(components),
        )

    @property
    def services_str(self) -> str:
        return ", ".join(self.services) if self.services else "the proposed Azure services"

    @property
    def two_services(self) -> str:
        if len(self.services) >= 2:
            return f"{self.services[0]} and {self.services[1]}"
        return self.services[0] if self.services else "the core services"

    @property
    def compliance_str(self) -> str:
        return " and ".join(self.compliance_flags) if self.compliance_flags else ""


@dataclass(slots=True)
class PersonaExecutor:
    persona: PersonaName
    prompt: str

    async def run(self, context: SocratesReviewContext) -> PersonaAnalysis:
        options = context.architecture_options or [{"option_id": "OPT-UNKNOWN", "summary": "No option supplied"}]
        primary = options[0]
        option_id = str(primary.get("option_id") or primary.get("id") or primary.get("name") or "OPT-UNKNOWN")
        signals = _ArchSignals.extract(context, option_id)
        finding = self._finding_for(option_id, signals)
        label = PERSONA_LABELS.get(self.persona, self.persona.value)
        return PersonaAnalysis(
            persona=self.persona,
            summary=(
                f"{label} reviewed {len(options)} option(s) against the architecture context "
                f"and raised a {finding.severity}-severity concern."
            ),
            findings=[finding],
            confidence=finding.confidence,
        )

    def _finding_for(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        if self.persona == PersonaName.DEVILS_ADVOCATE:
            return self._devils_advocate(option_id, s)
        if self.persona == PersonaName.SRE_OPS_LEAD:
            return self._sre_ops_lead(option_id, s)
        if self.persona == PersonaName.SECURITY_ARCHITECT:
            return self._security_architect(option_id, s)
        if self.persona == PersonaName.FINOPS_LEAD:
            return self._finops_lead(option_id, s)
        if self.persona == PersonaName.DELIVERY_LEAD:
            return self._delivery_lead(option_id, s)
        if self.persona == PersonaName.CUSTOMER_BIZ_SPONSOR:
            return self._customer_biz_sponsor(option_id, s)
        return self._data_architect(option_id, s)

    # ------------------------------------------------------------------
    # Per-persona finding builders
    # ------------------------------------------------------------------

    def _devils_advocate(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        if s.key_risks:
            risk = s.key_risks[0]
            finding = (
                f"Option '{s.option_name}' carries a stated risk: '{risk}'. "
                f"This assumption must be explicitly recorded and validated in the ADR "
                f"before committing to this architecture."
            )
            action = (
                f"Add '{risk}' as a validated assumption in the ADR "
                f"and confirm it is resolved before the HLD stage."
            )
        elif s.services:
            scale_clause = f" at {s.scale_hint}" if s.scale_hint else ""
            finding = (
                f"Option '{s.option_name}' depends on {s.two_services}{scale_clause}. "
                f"The throughput, partitioning, and retention assumptions for these services "
                f"are not yet validated and could invalidate the design if wrong."
            )
            action = (
                f"Document and validate throughput, partition count, and retention assumptions "
                f"for {s.two_services} before the ADR is finalised."
            )
        else:
            finding = (
                f"Option '{s.option_name}' depends on assumptions that have not been explicitly "
                f"recorded. If any are wrong, the selected design could fail in production."
            )
            action = "Record all key assumptions in the ADR and validate each one during the next stage."
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding=finding,
            severity="high",
            finding_type="assumption",
            confidence=0.78,
            requires_validation=True,
            recommended_action=action,
        )

    def _sre_ops_lead(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        avail_clause = f" to meet the {s.availability_target} SLA" if s.availability_target else ""
        finding = (
            f"Option '{s.option_name}' uses {s.services_str}. "
            f"Achieving operational readiness{avail_clause} requires explicit telemetry, "
            f"dead-letter/replay paths, and documented incident-response runbooks "
            f"for each service in this stack."
        )
        action = (
            f"Add Azure Monitor alerts, structured logging, replay mechanisms, "
            f"and on-call runbooks for {s.two_services} to the HLD."
        )
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding=finding,
            severity="medium",
            confidence=0.8,
            recommended_action=action,
        )

    def _security_architect(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        if s.compliance_str:
            compliance_clause = (
                f" {s.compliance_str} requirements demand documented network segmentation, "
                f"least-privilege RBAC, encryption at rest and in transit, and audit logging "
                f"across all tiers."
            )
        else:
            compliance_clause = (
                " Trust boundaries, identity flows, and sensitive-data handling paths "
                "must be explicitly documented and validated."
            )
        finding = (
            f"Option '{s.option_name}' spans {s.services_str}.{compliance_clause}"
        )
        action = (
            f"Add threat-model annotations, RBAC assignments, network segmentation controls, "
            f"and data-classification labels for {s.two_services} before architecture approval."
        )
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding=finding,
            severity="high",
            confidence=0.82,
            requires_validation=True,
            recommended_action=action,
        )

    def _finops_lead(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        scale_clause = f"At {s.scale_hint}, " if s.scale_hint else ""
        cost_clause = (
            f"the cost score for '{s.option_name}' ({s.cost_score}/10) "
            if s.cost_score
            else f"the cost profile for '{s.option_name}' "
        )
        finding = (
            f"{scale_clause}{cost_clause}will grow non-linearly with throughput, data retention, "
            f"cross-region traffic, and observability volume across {s.services_str}. "
            f"Explicit budget guardrails and cost-driver assumptions are not yet documented."
        )
        action = (
            f"Add monthly cost estimates and budget guardrails for {s.two_services} "
            f"to the decision record, including scale-sensitive cost drivers."
        )
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding=finding,
            severity="medium",
            confidence=0.74,
            recommended_action=action,
        )

    def _delivery_lead(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        count_clause = f"{s.component_count} components" if s.component_count else "multiple components"
        finding = (
            f"Option '{s.option_name}' spans {count_clause} including {s.services_str}. "
            f"Delivery risk is elevated without a staged rollout plan, clear team skill mapping "
            f"across each service, and explicit dependency sequencing."
        )
        action = (
            f"Define an MVP delivery slice focused on {s.two_services} "
            f"and defer non-essential topology complexity to later iterations."
        )
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding=finding,
            severity="medium",
            confidence=0.76,
            recommended_action=action,
        )

    def _customer_biz_sponsor(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        scale_clause = f" at {s.scale_hint}" if s.scale_hint else ""
        finding = (
            f"Option '{s.option_name}' must demonstrate clear, measurable business value{scale_clause}. "
            f"Time-to-value, go-live milestones, and acceptance criteria are not yet defined "
            f"for this architecture."
        )
        action = (
            "Tie each architecture phase to a measurable business outcome "
            "and define acceptance criteria before the HLD is approved."
        )
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding=finding,
            severity="medium",
            confidence=0.7,
            recommended_action=action,
        )

    def _data_architect(self, option_id: str, s: _ArchSignals) -> PersonaFinding:
        finding = (
            f"Option '{s.option_name}' using {s.services_str} must explicitly document "
            f"data ownership, lineage, retention policies, and consistency semantics. "
            f"These decisions have downstream impact on compliance, cost, and correctness."
        )
        return PersonaFinding(
            persona=self.persona,
            target_option_id=option_id,
            finding=finding,
            severity="medium",
            confidence=0.72,
            recommended_action=(
                "Add data lifecycle, ownership, retention, and consistency decisions "
                "to the HLD before the WAF review."
            ),
        )


# ------------------------------------------------------------------
# Signal extraction helpers
# ------------------------------------------------------------------

def _primary_option(options: list[dict[str, Any]], option_id: str) -> dict[str, Any]:
    for opt in options:
        if str(opt.get("option_id") or opt.get("id") or opt.get("name")) == option_id:
            return opt
    return options[0] if options else {}


def _extract_scale(text: str, requirements: dict[str, Any]) -> str:
    patterns = [
        r"\d+[KkMm]?\s*TPS",
        r"\d+[KkMm]?\s*RPS",
        r"\d+[KkMm]?\s*(?:requests?|transactions?|events?)\s+per\s+(?:second|minute|hour)",
        r"\d+[KkMm]?\s*(?:concurrent\s+)?users?",
        r"\d+[KkMm]?\s*msgs?\s+per\s+(?:second|minute)",
        r"\d+[KkMm]?\s*messages?\s+per\s+(?:second|minute)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    # Fall back to claims in requirements artifact
    for claim in _iter_claims(requirements):
        label = claim.get("label", "").lower()
        if any(kw in label for kw in ("scale", "throughput", "tps", "rps", "load", "volume", "capacity")):
            value = str(claim.get("value") or "")
            if value:
                return value[:60]
    return ""


def _extract_availability(text: str, requirements: dict[str, Any]) -> str:
    m = re.search(r"99\.\d+\s*%", text)
    if m:
        return m.group(0).strip()
    for claim in _iter_claims(requirements):
        label = claim.get("label", "").lower()
        if any(kw in label for kw in ("availability", "sla", "uptime", "nines", "resilience")):
            value = str(claim.get("value") or "")
            if value:
                return value[:40]
    return ""


def _extract_compliance(text: str, requirements: dict[str, Any]) -> list[str]:
    known: dict[str, str] = {
        "PCI-DSS": r"\bPCI[\s-]?DSS\b",
        "GDPR": r"\bGDPR\b",
        "HIPAA": r"\bHIPAA\b",
        "SOC 2": r"\bSOC\s*2\b",
        "ISO 27001": r"\bISO\s*27001\b",
        "FedRAMP": r"\bFedRAMP\b",
        "NIST": r"\bNIST\b",
    }
    flags: list[str] = [
        name for name, pattern in known.items()
        if re.search(pattern, text, re.IGNORECASE)
    ]
    if not flags:
        for claim in _iter_claims(requirements):
            label = claim.get("label", "").lower()
            value = str(claim.get("value") or "")
            if any(kw in label for kw in ("compliance", "regulatory", "framework", "standard", "audit")) and value:
                flags.append(value[:40])
    return flags[:3]


def _iter_claims(requirements: dict[str, Any]):
    claims = requirements.get("claims") or []
    for claim in claims:
        if isinstance(claim, dict):
            yield claim

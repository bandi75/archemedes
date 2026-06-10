# Socrates Engine Specification

**Document ID:** `08-socrates-engine.md`  
**Solution:** Archimedes — AI Architecture Workbench  
**Version:** v2.2  
**Status:** Implementation-ready baseline  
**Last updated:** 2026-06-09  
**Related documents:** `01-archimedes-hld.md`, `03-pydantic-schemas.md`, `06-stage-pipeline.md`, `07-agent-specifications.md`, `09-tool-specifications.md`, `10-foundry-iq-knowledge-base.md`, `11-evidence-and-claims.md`, `12-dependency-and-rereasoning.md`

---

## 1. Purpose

This document defines the **Socrates Engine**, the adversarial decision-quality workflow inside Archimedes.

Socrates is responsible for stress-testing architecture options before an Architecture Decision Record is generated. It does this by running multiple architecture-review personas in parallel, collecting their independent findings, and producing a synthesized decision brief.

Socrates is not a generic chatbot and not a separate product in the MVP. It is a structured reasoning workflow embedded inside the Archimedes stage pipeline.

The MVP goal is:

> Given a set of requirements and candidate architecture options, Socrates identifies risks, blind spots, operational concerns, security gaps, cost traps, delivery risks, assumptions requiring validation, and a confidence-scored recommendation.

---

## 2. Scope

### 2.1 In Scope

This document defines:

- Socrates role in the Archimedes lifecycle.
- Socrates input and output contracts.
- Workflow topology using fan-out/fan-in.
- Dispatcher, persona executors, optional cross-examiner, and synthesizer.
- Persona depth levels: light, standard, and deep.
- Persona responsibilities and prompt templates.
- Evidence and claim rules.
- Quality gate rules for the Socratic Review stage.
- Latency/cost controls.
- Failure handling, retry, and partial-output behavior.
- MVP implementation structure.
- Test scenarios and acceptance criteria.

### 2.2 Out of Scope

This document does not define:

- Full agent prompts for non-Socrates routines. See `07-agent-specifications.md`.
- Full function tool implementation. See `09-tool-specifications.md`.
- Pydantic class definitions for every model. See `03-pydantic-schemas.md`.
- Cosmos DB physical container design. See `04-database-design.md`.
- Full re-reasoning and artifact diff implementation. See `12-dependency-and-rereasoning.md`.

---

## 3. Design Principles

The Socrates Engine follows these principles:

1. **Structured adversarial reasoning over free-form debate**  
   Socrates is a deterministic workflow that invokes persona-specific LLM calls with controlled inputs and expected structured outputs.

2. **Personas are reviewers, not autonomous decision-makers**  
   Personas challenge, analyze, and expose weaknesses. Final recommendation comes from the Synthesizer, not from any single persona.

3. **Evidence-aware, not evidence-only**  
   Socrates should distinguish between facts, assumptions, and architectural judgment.

4. **Parallel where possible**  
   Persona analysis should fan out in parallel to reduce latency.

5. **Configurable depth**  
   Light, standard, and deep modes allow trade-offs between speed, cost, and review thoroughness.

6. **State writes only through StagePatch**  
   Socrates does not directly write to Cosmos DB. It returns a StagePatch candidate to the Orchestrator/State Manager.

7. **Review quality over verbosity**  
   Persona output should be concise, specific, and actionable.

8. **Demo impact matters**  
   For MVP, the Standard depth mode should be polished and predictable because this is one of the main demo differentiators.

---

## 4. Position in the Stage Pipeline

Socrates executes at Stage 5 of the Archimedes MVP pipeline.

```text
1.  Intake
2.  Requirements Extraction       -> Quality Gate
3.  Pattern Detection             -> Quality Gate
4.  Options Generation            -> Quality Gate
5.  Socratic Review               -> Quality Gate
6.  Evidence Audit Checkpoint
7.  ADR Generation                -> Quality Gate
8.  HLD + Mermaid Diagrams        -> Quality Gate
9.  Mini WAF Review               -> Quality Gate
10. Final Evidence Audit
11. Requirement Change Handling   -> Selective Re-run + Diff
```

Socrates consumes outputs from:

- Intake
- Requirements Extraction
- Pattern Detection
- Options Generation

Socrates produces inputs for:

- Evidence Audit Checkpoint
- ADR Generation
- Re-reasoning and decision diff flow

---

## 5. Socrates Responsibilities

Socrates is responsible for answering these questions:

1. What can go wrong with each architecture option?
2. Which option is operationally easiest or hardest to run?
3. Which option has security, privacy, or compliance concerns?
4. Which option may create hidden cost or scaling problems?
5. Which option has delivery or skill risks?
6. Which assumptions are unvalidated?
7. Are any options clearly unsuitable?
8. Is there a hybrid option that is stronger than the generated options?
9. What blind spots should the architect/user investigate before committing?
10. What is the final recommendation confidence level?

---

## 6. Runtime Topology

### 6.1 Workflow Topology

Socrates uses a fan-out/fan-in workflow.

```text
                 +----------------+
                 |   Dispatcher   |
                 +--------+-------+
                          |
              fan-out to personas
                          |
     +--------------------+--------------------+
     |                    |                    |
+----v----+        +------v------+      +------v------+
| Devil's |        | SRE / Ops   |      | Security    |
|Advocate |        | Lead        |      | Architect   |
+----+----+        +------+------+      +------+------+
     |                    |                    |
     +--------------------+--------------------+
                          |
                       fan-in
                          |
                  +-------v-------+
                  |  Synthesizer  |
                  +-------+-------+
                          |
                  Socratic Review
                  StagePatch output
```

Deep mode optionally inserts a Cross-Examiner between persona analysis and synthesis.

```text
Personas -> Cross-Examiner -> Synthesizer
```

### 6.2 Why Fan-Out/Fan-In

This structure is preferred because:

- Persona analysis is independent and can run concurrently.
- Each persona has a narrow prompt and review lens.
- The Synthesizer receives all findings and reconciles them.
- The workflow is easier to trace and debug than a single long multi-role prompt.
- It can degrade gracefully when one persona fails.

---

## 7. Socrates Depth Levels

Socrates supports three depth levels.

### 7.1 Light Mode

Used when the user wants quick feedback or when latency/cost must be minimized.

| Property | Value |
|---|---|
| Personas | 3 |
| Cross-examination | No |
| Estimated LLM calls | 4 |
| Use case | Quick option stress test |
| MVP priority | Optional |

Personas:

1. Devil's Advocate
2. SRE / Operations Lead
3. Delivery Lead

### 7.2 Standard Mode

Default mode for MVP and demo.

| Property | Value |
|---|---|
| Personas | 5 |
| Cross-examination | No |
| Estimated LLM calls | 6 |
| Use case | Architecture decision review |
| MVP priority | Must-have |

Personas:

1. Devil's Advocate
2. SRE / Operations Lead
3. Security Architect
4. FinOps Lead
5. Delivery Lead

### 7.3 Deep Mode

Used for high-stakes decisions or post-MVP enhancement.

| Property | Value |
|---|---|
| Personas | 7 |
| Cross-examination | Yes |
| Estimated LLM calls | 9 |
| Use case | High-stakes architecture board review |
| MVP priority | Defer |

Personas:

1. Devil's Advocate
2. SRE / Operations Lead
3. Security Architect
4. FinOps Lead
5. Delivery Lead
6. Customer / Business Sponsor
7. Data Architect

---

## 8. Persona Catalog

### 8.1 Devil's Advocate

**Purpose:** Challenge every option and expose hidden weaknesses.

**Primary concerns:**

- Failure modes
- Unsupported assumptions
- Over-complex designs
- Architectural lock-in
- Unproven technology choices
- Overfitting to the demo scenario

**Questions this persona asks:**

- What would make this architecture fail?
- What is the strongest argument against each option?
- Which option looks good on paper but breaks under real constraints?
- What has the Options Generator assumed without evidence?

**Expected output:**

- Critical risks per option
- Unsupported assumptions
- Option rejection candidates
- Severity ratings

---

### 8.2 SRE / Operations Lead

**Purpose:** Evaluate operability and production supportability.

**Primary concerns:**

- Observability
- Incident response
- Deployment complexity
- Blast radius
- Recovery behavior
- Operational toil
- Rollback and failover

**Questions this persona asks:**

- How hard is this to run at 3 AM?
- Can the team detect failures quickly?
- Can the system recover without manual heroics?
- What is the operational blast radius of a component failure?

**Expected output:**

- Operability risks
- Monitoring/logging/tracing gaps
- Reliability concerns
- Incident response recommendations

---

### 8.3 Security Architect

**Purpose:** Evaluate identity, network, data protection, compliance, and attack surface concerns.

**Primary concerns:**

- Identity and access control
- Network boundaries
- Secret management
- Data encryption
- Data exfiltration risk
- Compliance fit
- Threat model completeness

**Questions this persona asks:**

- Where are the trust boundaries?
- What data is sensitive?
- How are identities and secrets managed?
- What is the most likely attack path?
- Does the design support the stated compliance needs?

**Expected output:**

- Security risks per option
- Required controls
- Threat-model notes
- Compliance concerns

---

### 8.4 FinOps Lead

**Purpose:** Evaluate cost growth, scaling economics, hidden charges, and sizing assumptions.

**Primary concerns:**

- Fixed vs variable cost
- Scale sensitivity
- Idle resource waste
- Premium SKU dependencies
- Cross-region and egress charges
- Retrieval/model token costs
- Observability cost growth

**Questions this persona asks:**

- What costs grow with transaction volume?
- Which cost driver can surprise the team later?
- Is the recommended SKU reasonable for the stated scale?
- What must be measured before committing to the estimate?

**Expected output:**

- Cost risks
- Major cost drivers
- Cost sensitivity notes
- Sizing assumptions requiring validation

---

### 8.5 Delivery Lead

**Purpose:** Evaluate feasibility, team skills, timeline, dependencies, and MVP shape.

**Primary concerns:**

- Build complexity
- Team skill gaps
- Dependency risks
- Phasing strategy
- MVP vs full-scope separation
- Implementation risk

**Questions this persona asks:**

- Can the team actually build this in the expected timeline?
- Which option is easiest to deliver incrementally?
- What skills are missing?
- Which dependencies could block delivery?

**Expected output:**

- Delivery risks
- Skill gaps
- Phasing recommendations
- MVP suitability scores

---

### 8.6 Customer / Business Sponsor

**Purpose:** Evaluate business value, adoption, time-to-value, and stakeholder impact.

**Primary concerns:**

- Business outcome alignment
- User adoption
- ROI and time-to-value
- Process disruption
- Stakeholder risk
- Value clarity

**Questions this persona asks:**

- Which option best serves the business objective?
- Which option is easiest to explain to stakeholders?
- What value can be demonstrated quickly?
- What trade-offs would a sponsor challenge?

**Expected output:**

- Business-value risks
- Adoption risks
- Value realization notes
- Stakeholder concerns

---

### 8.7 Data Architect

**Purpose:** Evaluate data architecture, consistency, lineage, governance, retention, and analytical needs.

**Primary concerns:**

- Data flow completeness
- Data quality
- Data lineage
- Schema evolution
- Retention and archival
- Analytical workload support
- Governance and ownership

**Questions this persona asks:**

- What data is created, moved, transformed, and stored?
- Are consistency and ordering requirements clear?
- What is the data retention strategy?
- Are analytics and operational stores separated properly?

**Expected output:**

- Data design risks
- Lineage/governance gaps
- Retention concerns
- Data-platform implications

---

## 9. Socrates Input Contract

Socrates receives a compact review package from the Orchestrator.

The Orchestrator should not pass raw full artifacts unless necessary. It should pass summarized and structured stage outputs.

### 9.1 Required Inputs

```json
{
  "session_id": "arch-2026-06-09-fraud-detection",
  "stage_run_id": "socratic-review-run-001",
  "base_version": 1,
  "target_version": 1,
  "depth": "standard",
  "business_need": {
    "raw_input": "Design a real-time fraud detection platform...",
    "refined_statement": "...",
    "domain": "fintech"
  },
  "requirements_summary": {
    "functional": [],
    "non_functional": [],
    "constraints": [],
    "assumptions": [],
    "open_questions": []
  },
  "pattern_detection_summary": {
    "primary_pattern": "real_time_streaming",
    "secondary_patterns": ["event_driven_integration"],
    "typical_pipeline": "Ingestion -> Enrichment -> Scoring -> Alert/Action"
  },
  "architecture_options": [
    {
      "option_id": "OPT-A",
      "name": "Event Hubs + Stream Analytics + Azure Functions",
      "summary": "...",
      "components": [],
      "tradeoff_scores": {},
      "known_risks": []
    }
  ],
  "evaluation_criteria": [
    {"name": "time_to_market", "weight": 0.3},
    {"name": "scalability", "weight": 0.3},
    {"name": "operational_burden", "weight": 0.2},
    {"name": "cost", "weight": 0.2}
  ],
  "available_evidence": [],
  "user_preferences": {
    "prefer_managed_services": true,
    "risk_tolerance": "medium"
  }
}
```

### 9.2 Optional Inputs

```json
{
  "change_context": {
    "is_rerun": true,
    "change_event_id": "chg-001",
    "changed_fields": ["requirements.non_functional.scale"],
    "old_value_summary": "10K TPS, single-region",
    "new_value_summary": "100K TPS, active-active multi-region"
  },
  "prior_socratic_review_summary": {
    "version": 1,
    "recommendation": "OPT-A",
    "confidence": 0.82,
    "key_risks": []
  }
}
```

---

## 10. Persona Output Contract

Each persona must produce structured output.

### 10.1 Persona Finding Format

```json
{
  "persona": "SRE / Operations Lead",
  "summary": "Option B has stronger scale characteristics but higher operational burden.",
  "option_findings": [
    {
      "option_id": "OPT-A",
      "finding": "The design is operationally simple but may need explicit replay and dead-letter handling.",
      "severity": "medium",
      "type": "recommendation",
      "confidence": 0.78,
      "evidence_ids": [],
      "requires_validation": false,
      "recommended_action": "Add replay strategy and dead-letter queue handling to HLD."
    }
  ],
  "cross_option_findings": [
    {
      "finding": "All options need clearer observability requirements for p99 latency and failed transaction flows.",
      "severity": "medium",
      "type": "recommendation",
      "confidence": 0.8,
      "recommended_action": "Add operational dashboards and alerting requirements."
    }
  ],
  "assumptions_to_validate": [
    {
      "assumption": "The operations team can support Kafka/Flink if Option B is selected.",
      "impact_if_false": "Option B delivery and support risk increases significantly."
    }
  ]
}
```

### 10.2 Allowed Finding Types

| Type | Meaning |
|---|---|
| `fact` | Directly supported by a retrieved source or deterministic tool output |
| `assumption` | Inferred from user context or missing information |
| `recommendation` | Architectural judgment informed by facts and assumptions |

### 10.3 Severity Values

| Severity | Meaning |
|---|---|
| `critical` | Could invalidate an option or block a decision |
| `high` | Significant risk requiring mitigation before implementation |
| `medium` | Important concern that should be addressed in ADR/HLD/WAF |
| `low` | Minor improvement or design note |
| `info` | Useful observation |

---

## 11. Synthesizer Output Contract

The Synthesizer produces the Socratic Review artifact.

```json
{
  "review_summary": "Socrates recommends OPT-A for MVP with explicit mitigations, while noting that OPT-B may become preferable at much higher sustained throughput.",
  "ranked_recommendations": [
    {
      "rank": 1,
      "option_id": "OPT-A",
      "recommendation": "Recommended for MVP",
      "confidence": 0.82,
      "rationale": "Best balance of time-to-market, operational simplicity, and managed-service fit.",
      "conditions": [
        "Validate Event Hubs throughput and partitioning model for expected peak load.",
        "Add replay/dead-letter strategy."
      ]
    }
  ],
  "rejected_or_deprioritized_options": [
    {
      "option_id": "OPT-C",
      "reason": "Cannot meet the stated scale/latency assumptions without excessive risk.",
      "confidence": 0.76
    }
  ],
  "blind_spots": [
    "Data residency requirement is not yet explicit.",
    "Burst traffic and replay behavior are not modeled."
  ],
  "premortem": [
    {
      "failure_scenario": "Peak transaction volume exceeds partitioning assumptions and causes delayed fraud decisions.",
      "leading_indicators": ["p99 latency rising", "consumer lag increasing"],
      "mitigation": "Add throughput headroom, lag alerts, and load test gate before production."
    }
  ],
  "assumptions_requiring_validation": [
    {
      "assumption": "The team prefers managed services over self-managed streaming platforms.",
      "why_it_matters": "This materially affects OPT-A vs OPT-B selection."
    }
  ],
  "hybrid_option": {
    "proposed": false,
    "description": null
  },
  "persona_summaries": [],
  "quality_gate_checklist": {
    "blind_spots_generated": true,
    "premortem_generated": true,
    "min_personas": true,
    "confidence_scored": true
  }
}
```

---

## 12. StagePatch Output from Socrates

Socrates does not directly persist the review. The Orchestrator wraps the Synthesizer output into a `StagePatch` and submits it to the Architecture State Manager.

### 12.1 StagePatch Requirements

The Socratic Review StagePatch must contain:

- `session_id`
- `stage = "socratic_review"`
- `stage_run_id`
- `base_version`
- `target_version`
- `idempotency_key`
- `patch_hash`
- `patch.socratic_review`
- `claims`
- `evidence_sources`
- `quality_gate_result`
- `requires_user_input`

### 12.2 Example StagePatch Shape

```json
{
  "session_id": "arch-2026-06-09-fraud-detection",
  "stage": "socratic_review",
  "stage_run_id": "socratic-review-run-001",
  "base_version": 0,
  "target_version": 1,
  "idempotency_key": "arch-2026-06-09-fraud-detection:socratic_review:001:hash",
  "patch_hash": "sha256:...",
  "patch": {
    "socratic_review": {
      "depth": "standard",
      "recommendation": "OPT-A",
      "confidence": 0.82,
      "blind_spots": [],
      "premortem": [],
      "persona_findings": [],
      "synthesis": {}
    }
  },
  "claims": [],
  "evidence_sources": [],
  "quality_gate_result": {
    "status": "passed",
    "blocking_failures": [],
    "warnings": [],
    "user_override_allowed": true
  },
  "requires_user_input": []
}
```

---

## 13. Quality Gate for Socratic Review

The Socratic Review quality gate is evaluated deterministically after synthesis.

### 13.1 Blocking Checks

| Check ID | Description |
|---|---|
| `blind_spots_generated` | At least one meaningful blind spot is produced |
| `premortem_generated` | At least one pre-mortem failure scenario is produced |
| `recommendation_present` | Ranked recommendation exists |
| `confidence_scored` | Recommendation confidence score exists and is between 0.0 and 1.0 |

### 13.2 Warning Checks

| Check ID | Description |
|---|---|
| `min_personas` | Expected number of personas completed for the selected depth |
| `all_options_reviewed` | Every generated option was reviewed by at least one persona |
| `assumptions_identified` | Missing or unvalidated assumptions were identified |
| `evidence_links_present` | Findings that are factual have evidence links where available |

### 13.3 Quality Gate Evaluation

```python
def evaluate_socratic_quality_gate(review: dict, depth: str) -> QualityGateResult:
    blocking_failures = []
    warnings = []

    if not review.get("blind_spots"):
        blocking_failures.append("Socratic review must identify blind spots.")

    if not review.get("premortem"):
        blocking_failures.append("Socratic review must include a pre-mortem.")

    if not review.get("ranked_recommendations"):
        blocking_failures.append("Socratic review must include a ranked recommendation.")

    confidence = review.get("ranked_recommendations", [{}])[0].get("confidence")
    if confidence is None or not (0 <= confidence <= 1):
        blocking_failures.append("Socratic review must include a valid confidence score.")

    expected_personas = len(SOCRATES_DEPTH_LEVELS[depth]["personas"])
    completed_personas = len(review.get("persona_summaries", []))
    if completed_personas < expected_personas:
        warnings.append("Some Socrates personas did not complete.")

    if blocking_failures:
        status = "failed"
    elif warnings:
        status = "passed_with_warnings"
    else:
        status = "passed"

    return QualityGateResult(
        status=status,
        blocking_failures=blocking_failures,
        warnings=warnings,
        user_override_allowed=not blocking_failures,
    )
```

---

## 14. Prompt Templates

This section provides implementation-ready prompt templates. The actual implementation may store these under `app/agents/prompts/socrates/`.

### 14.1 Shared Persona Instructions

Every Socrates persona receives these common rules.

```text
You are a Socrates reviewer inside Archimedes, an AI architecture workbench.

You are reviewing architecture options produced by Archimedes. Your job is to challenge, analyze, and improve decision quality from your assigned perspective.

Rules:
1. Stay within your assigned persona lens.
2. Review all options, not just the recommended one.
3. Separate FACTS, ASSUMPTIONS, and RECOMMENDATIONS.
4. Do not invent Azure service capabilities or pricing.
5. If a claim requires official documentation and no evidence is available, mark it as an assumption or recommendation, not a fact.
6. Prefer specific findings over generic advice.
7. Provide severity for every finding.
8. Identify assumptions that require user validation.
9. Keep output concise and structured.
10. Return only valid JSON matching the expected persona output shape.
```

### 14.2 Devil's Advocate Prompt

```text
You are the Devil's Advocate reviewer.

Your role is to find flaws, failure modes, hidden assumptions, and reasons an option may fail.

Focus on:
- Architectural weak points
- Missing requirements
- Scale and latency risk
- Over-engineering or under-engineering
- Vendor lock-in
- Unsupported assumptions
- Technology choices that may not fit the stated constraints

For each option:
- Identify the strongest argument against it.
- Identify what could make it fail in production.
- Identify whether any finding should disqualify the option.

Return structured JSON only.
```

### 14.3 SRE / Operations Lead Prompt

```text
You are the SRE / Operations Lead reviewer.

Your role is to evaluate whether each option can be operated reliably in production.

Focus on:
- Monitoring, logging, and tracing
- Incident response
- Deployment and rollback
- Recovery and failover
- Consumer lag, queue buildup, retries, and replay
- Blast radius
- Operational complexity
- Mean time to detect and recover

For each option:
- Identify operational strengths and weaknesses.
- Identify what the team must monitor.
- Identify operational risks that should be added to the ADR or HLD.

Return structured JSON only.
```

### 14.4 Security Architect Prompt

```text
You are the Security Architect reviewer.

Your role is to evaluate security, privacy, and compliance implications of each architecture option.

Focus on:
- Identity and access control
- Network isolation and trust boundaries
- Secrets management
- Data encryption at rest and in transit
- Sensitive data handling
- Compliance fit
- Attack surface
- Least privilege
- Audit logging

For each option:
- Identify security gaps.
- Identify required controls.
- Identify assumptions requiring validation.
- Flag any design that cannot meet stated compliance constraints.

Return structured JSON only.
```

### 14.5 FinOps Lead Prompt

```text
You are the FinOps Lead reviewer.

Your role is to evaluate cost risk and scaling economics.

Focus on:
- Fixed vs variable costs
- Premium SKU dependencies
- Cross-region costs
- Egress and data movement costs
- Idle capacity
- Token/retrieval costs where relevant
- Cost sensitivity to volume growth
- Observability and retention costs

For each option:
- Identify likely major cost drivers.
- Identify cost assumptions that must be validated.
- Identify whether costs scale linearly or non-linearly.
- Flag hidden cost risks.

Return structured JSON only.
```

### 14.6 Delivery Lead Prompt

```text
You are the Delivery Lead reviewer.

Your role is to evaluate delivery feasibility.

Focus on:
- Implementation complexity
- Required skills
- Team learning curve
- External dependencies
- MVP suitability
- Timeline risk
- Testing and release complexity
- Migration or rollout complexity

For each option:
- Identify build risks.
- Identify team skill gaps.
- Identify what can be delivered first.
- Identify whether the option is realistic for MVP.

Return structured JSON only.
```

### 14.7 Customer / Business Sponsor Prompt

```text
You are the Customer / Business Sponsor reviewer.

Your role is to evaluate business value, stakeholder clarity, adoption, and time-to-value.

Focus on:
- Business outcome alignment
- Time-to-value
- Stakeholder confidence
- Operational disruption
- Adoption risk
- ROI clarity
- Explainability of the recommendation

For each option:
- Identify business advantages and disadvantages.
- Identify stakeholder concerns.
- Identify adoption risks.
- Identify whether the option supports a clear MVP story.

Return structured JSON only.
```

### 14.8 Data Architect Prompt

```text
You are the Data Architect reviewer.

Your role is to evaluate data flow, consistency, lineage, governance, and analytical requirements.

Focus on:
- Data ingestion and flow
- Schema evolution
- Data quality
- Data consistency and ordering
- Data retention
- Data lineage
- Operational vs analytical storage
- Governance and ownership

For each option:
- Identify data architecture gaps.
- Identify data governance risks.
- Identify retention and lineage concerns.
- Identify what must be added to the HLD.

Return structured JSON only.
```

### 14.9 Cross-Examiner Prompt

Used only in Deep mode.

```text
You are the Socrates Cross-Examiner.

You are given independent persona analyses. Your job is to identify tensions, contradictions, and unresolved disagreements between personas.

Focus on:
- Where personas disagree.
- Where one persona's recommendation creates risk for another persona.
- Where a trade-off must be explicitly accepted.
- Where evidence is insufficient to decide.
- Where a hybrid option may resolve the tension.

Do not produce the final recommendation. Produce cross-examination findings that will help the Synthesizer make the final decision.

Return structured JSON only.
```

### 14.10 Synthesizer Prompt

```text
You are the Socrates Synthesizer and Chief Architect reviewer.

You are given:
- Business need
- Requirements summary
- Pattern detection summary
- Architecture options
- Evaluation criteria
- Persona findings
- Optional cross-examination findings

Your job is to reconcile the persona findings into a decision-quality brief.

You must produce:
1. Review summary.
2. Ranked recommendation with confidence score.
3. Reasons for deprioritized or rejected options.
4. Blind spots.
5. Pre-mortem failure scenarios.
6. Assumptions requiring validation.
7. Optional hybrid option if the debate reveals one.
8. Persona summary table.
9. Quality gate checklist.

Rules:
- Separate facts, assumptions, and recommendations.
- Do not claim certainty where evidence is weak.
- If evidence is missing, mark the item as assumption or recommendation.
- Prefer concise and decision-ready output.
- Return only valid JSON matching the Socratic Review output contract.
```

---

## 15. Implementation Design

### 15.1 Suggested Module Structure

```text
app/
├── agents/
│   ├── socrates/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── workflow.py
│   │   ├── personas.py
│   │   ├── prompts.py
│   │   ├── synthesizer.py
│   │   ├── quality_gate.py
│   │   └── models.py
│   └── prompts/
│       └── socrates/
│           ├── shared.txt
│           ├── devils_advocate.txt
│           ├── sre_ops_lead.txt
│           ├── security_architect.txt
│           ├── finops_lead.txt
│           ├── delivery_lead.txt
│           ├── customer_sponsor.txt
│           ├── data_architect.txt
│           ├── cross_examiner.txt
│           └── synthesizer.txt
```

### 15.2 Main Classes

| Class | Responsibility |
|---|---|
| `SocratesEngine` | Public interface used by Orchestrator |
| `SocratesWorkflowFactory` | Builds light/standard/deep workflows |
| `DispatcherExecutor` | Broadcasts review context to personas |
| `PersonaExecutor` | Runs one persona review call |
| `CrossExaminerExecutor` | Optional deep-mode cross-examination |
| `SocratesSynthesizerExecutor` | Produces final Socratic Review artifact |
| `SocratesQualityGateEvaluator` | Evaluates Socratic Review quality gate |
| `SocratesPatchBuilder` | Converts review result into StagePatch |

---

## 16. Conceptual WorkflowBuilder Implementation

The implementation must include the Dispatcher registration and correct depth-level indexing.

```python
class DispatcherExecutor(Executor):
    """Accepts debate context and broadcasts it to all persona executors."""

    @handler
    async def dispatch(self, context: str, ctx: WorkflowContext) -> None:
        await ctx.send_message(context)


def build_socrates_workflow(depth: str = "standard"):
    pack = SOCRATES_DEPTH_LEVELS[depth]
    persona_configs = pack["personas"]

    builder = WorkflowBuilder(
        name="SocraticDebate",
        description=f"Adversarial architecture review ({depth} depth)",
    )

    builder.register_executor(
        lambda: DispatcherExecutor(id="dispatcher"),
        name="Dispatcher",
    )

    persona_names = []
    for persona in persona_configs:
        name = persona["name"].replace(" ", "_").replace("/", "_")
        persona_names.append(name)
        builder.register_executor(
            lambda p=persona, n=name: PersonaExecutor(
                id=f"persona_{n}",
                persona_name=p["name"],
                persona_prompt=p["prompt"],
            ),
            name=name,
        )

    if pack.get("cross_examination"):
        builder.register_executor(
            lambda: CrossExaminerExecutor(id="cross_examiner"),
            name="CrossExaminer",
        )

    builder.register_executor(
        lambda: SocratesSynthesizerExecutor(id="synthesizer"),
        name="Synthesizer",
    )

    builder.add_fan_out_edges("Dispatcher", persona_names)

    if pack.get("cross_examination"):
        builder.add_fan_in_edges(persona_names, "CrossExaminer")
        builder.add_edge("CrossExaminer", "Synthesizer")
    else:
        builder.add_fan_in_edges(persona_names, "Synthesizer")

    builder.set_start_executor("Dispatcher")

    return builder.build()
```

This code is intentionally conceptual. Exact imports and method signatures should be verified during implementation against the installed Agent Framework SDK version.

---

## 17. Execution Algorithm

```text
1. Orchestrator receives request to run Stage 5: Socratic Review.
2. Orchestrator loads ArchitectureSession and latest artifacts from stages 1-4.
3. Orchestrator builds SocratesReviewContext.
4. SocratesEngine selects depth mode.
5. Dispatcher receives review context.
6. Persona executors run independently.
7. Failed persona calls are retried based on retry policy.
8. Completed persona outputs are normalized.
9. Deep mode optionally runs Cross-Examiner.
10. Synthesizer produces SocraticReview artifact.
11. SocratesQualityGateEvaluator evaluates quality gate.
12. SocratesPatchBuilder creates StagePatch.
13. Orchestrator submits StagePatch to Architecture State Manager.
14. State Manager validates idempotency/concurrency and persists artifact.
15. Pipeline advances to Evidence Audit Checkpoint.
```

---

## 18. Error Handling

### 18.1 Persona Failure

If one persona fails:

- Retry once.
- If still failed, continue if minimum persona threshold is met.
- Mark quality gate as `passed_with_warnings`.
- Include failed persona in warnings.

Minimum thresholds:

| Depth | Expected Personas | Minimum Completed Personas |
|---|---:|---:|
| Light | 3 | 2 |
| Standard | 5 | 4 |
| Deep | 7 | 5 |

### 18.2 Synthesizer Failure

If Synthesizer fails:

- Retry once with a compacted persona summary.
- If still failed, mark stage as failed.
- Do not persist partial Socratic Review as completed artifact.
- Store failure reason in `StageExecution`.

### 18.3 Invalid JSON Output

If persona or synthesizer output is invalid JSON:

1. Attempt schema repair once using a deterministic JSON cleanup function.
2. If repair fails, ask the model once to reformat to valid JSON without changing content.
3. If still invalid, mark that executor as failed.

### 18.4 Timeout

Timeout policy:

| Step | Timeout |
|---|---:|
| Persona call | 60 seconds |
| Cross-examiner | 90 seconds |
| Synthesizer | 90 seconds |
| Entire standard review | 3 minutes |

For MVP, use conservative timeouts and surface progress in the UI.

---

## 19. Latency and Cost Controls

### 19.1 Controls

- Use Standard mode by default.
- Use Light mode for quick review.
- Use Deep mode only on explicit user request.
- Parallelize persona calls.
- Summarize stage artifacts before passing to Socrates.
- Limit each persona response to concise structured output.
- Avoid web search inside persona calls for MVP unless explicitly needed.
- Prefer evidence already retrieved during earlier stages.

### 19.2 Token Budget

Suggested context packaging:

| Input | Budget |
|---|---:|
| Business need | 300 tokens |
| Requirements summary | 1,000 tokens |
| Pattern summary | 300 tokens |
| Architecture options | 2,000 tokens |
| Evidence summary | 1,000 tokens |
| Persona instructions | 800 tokens |
| Output | 1,000 tokens/persona |

The Orchestrator should never pass full HLD or long raw documents into Socrates.

---

## 20. Evidence and Claim Behavior

Socrates must follow the evidence rules defined in `11-evidence-and-claims.md`.

### 20.1 Claim Rules

- Factual claims must link to evidence when available.
- Unsupported factual claims must be downgraded to assumptions or recommendations.
- Recommendations may reference multiple evidence records but are still classified as recommendations.
- User-context statements should usually be assumptions unless explicitly provided by the user.

### 20.2 Evidence Source Usage

Socrates should primarily use evidence already retrieved in earlier stages.

For MVP:

- Personas do not independently call Foundry IQ.
- Options Generator and earlier stages provide available evidence.
- Synthesizer may flag missing evidence.
- Evidence Audit Checkpoint validates the Socratic Review after completion.

Post-MVP:

- Allow selected personas to request additional evidence through a controlled retrieval step.
- For example, the Security Architect may request official Azure security baseline evidence.

---

## 21. Requirement Change and Re-Reasoning Behavior

When re-running Socrates after a requirement change, the Socrates context should include change information.

Example:

```json
{
  "is_rerun": true,
  "changed_fields": ["requirements.non_functional.scale", "requirements.non_functional.availability"],
  "old_value_summary": "10K TPS, 99.95%, single-region",
  "new_value_summary": "100K TPS, active-active multi-region",
  "prior_recommendation": "OPT-A",
  "prior_confidence": 0.82
}
```

On re-run, Socrates should explicitly answer:

- Does the prior recommendation still hold?
- Which persona findings changed?
- Which risks became more severe?
- Did any option become unsuitable?
- Did a new hybrid option emerge?
- Did confidence increase or decrease?

The resulting Socratic Review becomes a new `VersionedArtifact` version.

---

## 22. Frontend Behavior

The frontend should show Socrates as a visible reasoning stage.

### 22.1 Standard View

Show:

- Socrates stage status.
- Persona progress cards.
- Final recommendation.
- Confidence score.
- Blind spots.
- Pre-mortem.
- Assumptions requiring validation.

### 22.2 Persona Progress

Example UI state:

```text
Socrates Review: Running

[✓] Devil's Advocate
[✓] SRE / Operations Lead
[✓] Security Architect
[~] FinOps Lead
[ ] Delivery Lead

Synthesizer: Waiting for persona findings
```

### 22.3 Final Socrates Card

Example final display:

```text
Socrates Recommendation
Recommended Option: OPT-A
Confidence: 0.82

Key Blind Spots:
- Burst traffic behavior not modeled.
- Data residency requirement still open.

Pre-Mortem:
- Peak volume exceeds partitioning assumptions and causes delayed fraud decisions.

Assumptions to Validate:
- Team prefers managed services over self-managed streaming platforms.
```

### 22.4 Re-Reasoning Diff View

On requirement change, show before/after Socrates changes:

```text
Socrates Review Diff: v1 -> v2

Recommendation:
- Before: OPT-A recommended with confidence 0.82
- After: OPT-B recommended with confidence 0.74

Risks Increased:
- Operational burden: medium -> high
- Cost sensitivity: medium -> high

New Blind Spots:
- Cross-region consistency model not defined.
- Active-active conflict handling not specified.
```

---

## 23. MVP Behavior

For MVP, implement only:

- Standard depth mode.
- Five personas.
- No cross-examination.
- Synthesizer output.
- Socratic Review quality gate.
- StagePatch output.
- Evidence Audit Checkpoint after Socrates.
- Basic before/after Socrates diff for requirement change.

Defer:

- Deep mode.
- Customer / Business Sponsor persona.
- Data Architect persona.
- Persona-level Foundry IQ retrieval.
- Cross-examination.
- Human voting or approval workflow.

---

## 24. Testing Strategy

### 24.1 Unit Tests

| Test | Expected Result |
|---|---|
| Build standard workflow | Dispatcher, 5 personas, Synthesizer registered |
| Build light workflow | Dispatcher, 3 personas, Synthesizer registered |
| Build deep workflow | Dispatcher, 7 personas, CrossExaminer, Synthesizer registered |
| Invalid depth | Raises validation error |
| Quality gate passes | Blind spots, pre-mortem, recommendation, confidence present |
| Quality gate fails | Missing recommendation or pre-mortem blocks stage |
| Partial persona failure | Review passes with warning if threshold met |
| StagePatch build | Includes idempotency/concurrency fields |

### 24.2 Integration Tests

Use the demo scenario:

```text
Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.
```

Expected Socrates result:

- Reviews all generated options.
- Produces clear recommendation.
- Produces blind spots.
- Produces pre-mortem.
- Identifies assumptions requiring validation.
- Passes quality gate.

### 24.3 Re-Reasoning Test

Change:

```text
Actually, make it 100K TPS and multi-region active-active.
```

Expected Socrates result:

- Reviews whether prior recommendation still holds.
- Updates risk severity.
- May reduce confidence or recommend a different option.
- Produces new versioned Socratic Review artifact.
- Diff service can compare v1 and v2.

---

## 25. Observability

Log the following per Socrates run:

- `session_id`
- `stage_run_id`
- `depth`
- `persona_count_expected`
- `persona_count_completed`
- `persona_failures`
- `total_latency_ms`
- `persona_latency_ms`
- `synthesizer_latency_ms`
- `token_usage_input`
- `token_usage_output`
- `quality_gate_status`
- `recommendation_option_id`
- `recommendation_confidence`

Metrics:

| Metric | Purpose |
|---|---|
| `socrates_run_count` | Total executions |
| `socrates_failure_count` | Reliability tracking |
| `socrates_latency_ms` | Performance tracking |
| `socrates_persona_failure_count` | Persona stability |
| `socrates_quality_gate_failed_count` | Output quality tracking |
| `socrates_recommendation_confidence_avg` | Decision confidence trend |

---

## 26. Security and Safety Notes

- Persona prompts must not allow tool execution outside the approved tool set.
- Socrates should not directly call persistence APIs.
- Socrates should not override quality gate failures.
- Socrates should not fabricate citations.
- Socrates should not represent assumptions as facts.
- Socrates output must go through schema validation before persistence.
- Prompt templates should be version-controlled.
- Persona outputs should be treated as untrusted until validated.

---

## 27. Acceptance Criteria

Socrates MVP is accepted when:

1. Standard-depth Socrates workflow runs end-to-end.
2. Dispatcher is registered and fan-out/fan-in works.
3. Five personas produce structured findings.
4. Synthesizer produces recommendation, confidence, blind spots, pre-mortem, and assumptions.
5. Quality gate evaluates correctly.
6. StagePatch includes idempotency and concurrency metadata.
7. Socratic Review artifact is persisted only through State Manager.
8. Evidence Audit Checkpoint can audit Socrates output.
9. Requirement-change re-run produces a new versioned Socratic Review artifact.
10. Frontend can show persona progress and final Socrates decision card.

---

## 28. Implementation Checklist

### Build First

- [ ] Define Socrates input/output models.
- [ ] Define persona finding model.
- [ ] Define Socratic Review artifact model.
- [ ] Create prompt files.
- [ ] Implement `DispatcherExecutor`.
- [ ] Implement `PersonaExecutor`.
- [ ] Implement `SocratesSynthesizerExecutor`.
- [ ] Implement workflow factory for Standard depth.
- [ ] Implement quality gate evaluator.
- [ ] Implement StagePatch builder.
- [ ] Add unit tests.
- [ ] Integrate with Orchestrator Stage 5.

### Build Next

- [ ] Add Light depth.
- [ ] Add Deep depth skeleton.
- [ ] Add CrossExaminer.
- [ ] Add re-reasoning input context.
- [ ] Add frontend progress events.
- [ ] Add Socrates diff summary.

### Defer

- [ ] Persona-level retrieval.
- [ ] Human voting workflow.
- [ ] Business strategy persona pack.
- [ ] Generic standalone Socrates product mode.

---

## 29. Open Questions

| Question | Recommendation for MVP |
|---|---|
| Should personas call Foundry IQ directly? | No. Use evidence from earlier stages. |
| Should Socrates always run? | Yes for MVP after options generation. |
| Should users choose depth? | Default to Standard; hide advanced controls initially. |
| Should cross-examination run in MVP? | No. Defer to Deep mode. |
| Should Socrates block ADR generation? | Yes if blocking quality gate failures exist. |
| Should users override Socrates warnings? | Yes, warnings can be overridden. Blocking failures cannot. |

---

## 30. Summary

Socrates is the decision-quality engine inside Archimedes.

It converts architecture option selection from a single model recommendation into a structured adversarial review involving multiple focused perspectives. The design uses a fan-out/fan-in workflow, configurable depth levels, structured persona outputs, deterministic quality gates, and StagePatch-based persistence.

For MVP, Standard mode with five personas is sufficient to create a strong demo and a credible architecture-review capability.

The core demo moment is:

> Archimedes generates options. Socrates stress-tests them. The Synthesizer produces a confidence-scored decision brief. When requirements change, Socrates re-runs only where impacted and shows how the decision changed.

# Archimedes Evidence and Claims Model

**Document ID:** `11-evidence-and-claims.md`  
**Solution:** Archimedes — AI Architecture Workbench  
**Version:** v2.2  
**Status:** Implementation-ready baseline  
**Last updated:** 2026-06-09  
**Related documents:** `01-archimedes-hld.md`, `02-domain-models.md`, `03-pydantic-schemas.md`, `04-database-design.md`, `06-stage-pipeline.md`, `10-foundry-iq-knowledge-base.md`

---

## 1. Purpose

This document defines the evidence and claims model for Archimedes.

Archimedes must not behave like a generic architecture chatbot. It must produce architecture recommendations that are traceable, auditable, and grounded in trusted sources where appropriate. To support this, the platform separates:

- **Claims**: statements made by agents or tools.
- **Evidence sources**: retrieved or computed information used to support claims.
- **Assumptions**: inferred or user-context-dependent statements that require validation.
- **Recommendations**: architectural judgment based on facts, assumptions, constraints, and trade-offs.
- **Evidence audits**: checks that validate citation relevance, trust, freshness, and contradictions.

The evidence and claims model supports the following core goals:

1. Prevent unsupported factual claims from silently becoming architecture decisions.
2. Make the difference between facts, assumptions, and recommendations explicit.
3. Preserve source metadata, including Foundry IQ knowledge base version information.
4. Enable Evidence Auditor checkpoints after Socrates and before final architecture output.
5. Support later compliance, governance, and architecture review board style workflows.

---

## 2. Scope

This document covers:

- Claim taxonomy.
- Evidence source taxonomy.
- Relationship between claims and evidence sources.
- Trust and freshness model.
- Evidence capture during pipeline execution.
- Evidence audit checkpoints.
- Unsupported claim handling.
- Contradiction detection.
- User validation flow for assumptions.
- Cosmos DB storage expectations.
- Implementation guidance for the Evidence Auditor.

This document does not cover:

- Full Pydantic code. See `03-pydantic-schemas.md`.
- Cosmos DB physical indexing and partitioning. See `04-database-design.md`.
- Foundry IQ knowledge base setup. See `10-foundry-iq-knowledge-base.md`.
- Full agent system prompts. See `07-agent-specifications.md`.
- Pipeline sequencing. See `06-stage-pipeline.md`.

---

## 3. Design Principles

The evidence and claims subsystem follows these principles:

1. **Claims are not evidence**  
   A claim is what Archimedes says. Evidence is where the supporting information came from.

2. **Recommendations do not need direct citations for every sentence**  
   Architecture recommendations are often expert judgment. The facts informing the recommendation must be evidence-backed, but the recommendation itself should be classified as judgment.

3. **Facts require relevant evidence**  
   A source must support the specific claim. A citation about a service feature does not support a claim about cost, limits, security, or SLA unless the source actually covers those topics.

4. **Assumptions must be visible**  
   If Archimedes infers something about the user, organization, team skill, timeline, budget, compliance posture, or operational maturity, it must be marked as an assumption.

5. **Evidence has freshness and trust metadata**  
   Pricing, service limits, preview/GA status, and regional availability are time-sensitive. These claims need freshness flags.

6. **Knowledge base versioning is mandatory**  
   Foundry IQ outputs must include KB/source version metadata where available, so later changes to indexed documentation do not invalidate the audit trail.

7. **Contradictions should be surfaced, not hidden**  
   If two trusted sources disagree, Archimedes should flag the contradiction and avoid overconfident recommendations.

8. **Evidence audit is a quality control step**  
   Evidence audit is not a content-generation step. It is a validation checkpoint.

---

## 4. Core Concepts

### 4.1 Claim

A **Claim** is a statement made by Archimedes during a stage.

Examples:

```text
Azure Event Hubs is a managed event ingestion service for high-throughput streaming workloads.
```

```text
The customer team may not have deep Kafka operations experience.
```

```text
For the first release, a managed streaming option is preferable to self-managed Kafka.
```

Each of these statements has a different classification.

### 4.2 Evidence Source

An **Evidence Source** is a source, retrieved excerpt, tool output, or structured lookup used to support one or more claims.

Examples:

```text
Microsoft Learn page retrieved through Foundry IQ.
```

```text
Azure pricing JSON used by cost estimator function.
```

```text
Foundry Web Search result about a recent Azure service update.
```

```text
User-provided requirement: “Must support 100K TPS.”
```

### 4.3 Claim-Evidence Link

Claims and evidence sources have a many-to-many relationship:

- One claim may be supported by multiple evidence sources.
- One evidence source may support multiple claims.
- Assumptions may have no external evidence, but should include the reason they were inferred.
- Recommendations should link to the facts and assumptions that informed the recommendation.

---

## 5. Claim Taxonomy

Archimedes uses three primary claim types.

| Claim type | Meaning | Evidence requirement | Example |
|---|---|---|---|
| `fact` | A statement presented as objectively true | Must have relevant, trusted evidence | “Azure AI Search supports vector search.” |
| `assumption` | An inferred statement about context, constraints, people, maturity, or unstated requirements | May not have external evidence, but must be visible and validation status tracked | “The team likely prefers managed services.” |
| `recommendation` | Architectural judgment based on facts, assumptions, priorities, and trade-offs | Should link to supporting claims/evidence but is not itself a raw fact | “Choose Event Hubs over self-managed Kafka for MVP.” |

### 5.1 Fact

A fact is a claim that Archimedes states as true.

Fact claims should be used for:

- Azure service capabilities.
- Service limits.
- Regional availability.
- SLA or resiliency characteristics.
- Pricing dimensions.
- Security features.
- Compliance documentation.
- Well-Architected Framework guidance.
- Architecture patterns documented by Microsoft.

Fact claims must include at least one relevant evidence source unless the statement is derived from user input.

Example:

```json
{
  "claim_id": "clm_001",
  "claim": "Azure Event Hubs is suitable for high-throughput event ingestion workloads.",
  "type": "fact",
  "confidence": 0.92,
  "stage": "options_generation",
  "evidence_ids": ["ev_001"],
  "requires_user_validation": false
}
```

### 5.2 Assumption

An assumption is a statement Archimedes infers but cannot confirm from available evidence.

Assumptions commonly include:

- Team skill level.
- Delivery timeline feasibility.
- Operational maturity.
- Budget sensitivity.
- Preference for managed services.
- Existing enterprise standards.
- Existing network/security posture.
- Data residency expectations.
- Acceptable vendor lock-in.

Example:

```json
{
  "claim_id": "clm_014",
  "claim": "The implementation team may have limited experience operating Kafka on Kubernetes.",
  "type": "assumption",
  "confidence": 0.55,
  "stage": "socratic_review",
  "evidence_ids": [],
  "requires_user_validation": true
}
```

Assumptions should not be hidden inside the narrative. They should be surfaced in the artifact and, where important, presented to the user for validation.

### 5.3 Recommendation

A recommendation is a reasoned architecture judgment.

Recommendations are not raw facts. They combine:

- Requirements.
- Evidence-backed service capabilities.
- Constraints.
- Risk profile.
- Trade-off priorities.
- Assumptions.
- Socratic persona findings.

Example:

```json
{
  "claim_id": "clm_027",
  "claim": "For the MVP, prefer Azure Event Hubs plus Stream Analytics over AKS-hosted Kafka due to lower operational burden and faster delivery.",
  "type": "recommendation",
  "confidence": 0.81,
  "stage": "socratic_review",
  "evidence_ids": ["ev_001", "ev_004", "ev_009"],
  "requires_user_validation": false
}
```

Recommendations should link to evidence-backed facts and visible assumptions. They do not require a source that states the exact recommendation.

---

## 6. Evidence Source Taxonomy

Evidence sources are classified by retrieval or origin method.

| Source type | `retrieved_via` value | Typical use |
|---|---|---|
| Foundry IQ KB retrieval | `foundry_iq` | Azure architecture docs, WAF docs, CAF, service docs, security baselines |
| Web search | `web_search` | Recent Azure updates, preview/GA status, current announcements |
| Function tool output | `function_tool` | Cost calculation, STRIDE mapping, Mermaid render check, quality gate result |
| User input | `user_input` | Business need, explicit requirements, user-validated assumptions |
| Model judgment | `model_judgment` | Internal reasoning classification; should not support facts directly |

For implementation simplicity, `model_judgment` may be used on `ClaimRecord` or audit output, but it should not be treated as an evidence source that supports factual claims.

---

## 7. Evidence Source Model

The concrete schema is defined in `03-pydantic-schemas.md`. Conceptually, an Evidence Source contains:

```json
{
  "evidence_id": "ev_001",
  "source": "Azure Event Hubs documentation",
  "source_url": "https://learn.microsoft.com/...",
  "retrieved_via": "foundry_iq",
  "retrieved_at": "2026-06-09T10:30:00Z",
  "excerpt": "Relevant excerpt or chunk summary...",
  "kb_name": "azure-architecture-kb",
  "kb_version": "2026-06-09",
  "source_document_version": "2026-06-01",
  "source_freshness": "current",
  "trust_level": "high"
}
```

### 7.1 Required fields

At minimum, every evidence source must include:

- `evidence_id`
- `source`
- `retrieved_via`
- `retrieved_at`
- `trust_level`

For Foundry IQ evidence, also include:

- `kb_name`
- `kb_version`
- `source_document_version`, if available
- `source_url`, if available
- retrieved chunk/excerpt or a chunk reference

### 7.2 Evidence source immutability

Evidence sources should be append-only.

Do not update historical evidence records except for non-semantic metadata corrections. If the same source is retrieved again after KB refresh, create a new evidence record with a new `retrieved_at` and `kb_version`.

---

## 8. Claim Model

The concrete schema is defined in `03-pydantic-schemas.md`. Conceptually, a Claim Record contains:

```json
{
  "claim_id": "clm_001",
  "claim": "Azure Event Hubs is suitable for high-throughput event ingestion workloads.",
  "type": "fact",
  "confidence": 0.92,
  "stage": "options_generation",
  "evidence_ids": ["ev_001", "ev_002"],
  "requires_user_validation": false
}
```

### 8.1 Required fields

Every claim must include:

- `claim_id`
- `claim`
- `type`
- `confidence`
- `stage`
- `evidence_ids`, which may be empty only for assumptions or explicitly marked model judgment
- `requires_user_validation`

### 8.2 Confidence semantics

Confidence is not a probability of truth. It is an operational confidence score indicating how strongly Archimedes can rely on the claim for the current decision.

Recommended scoring guidance:

| Confidence range | Meaning |
|---|---|
| `0.90–1.00` | Strong, trusted, current evidence directly supports the claim |
| `0.75–0.89` | Good evidence supports the claim, minor caveats remain |
| `0.60–0.74` | Plausible but may depend on assumptions or incomplete context |
| `0.40–0.59` | Weak or context-dependent claim; should be validated |
| `< 0.40` | Do not use for major decisions without validation |

---

## 9. Source Trust Model

Archimedes assigns trust levels to evidence sources.

| Trust level | Description | Examples |
|---|---|---|
| `high` | Official, authoritative, directly relevant | Microsoft Learn, Azure Architecture Center, official Azure pricing/service docs, WAF docs, official SLA pages |
| `medium` | Credible but not authoritative for final decisions | Microsoft blogs, engineering blogs, reputable third-party analysis, conference materials |
| `low` | Useful for discovery only, not final grounding | Forum posts, unverified blogs, social media, vendor marketing pages without technical detail |

### 9.1 Trusted source allowlist

For MVP, high-trust sources should include:

- Microsoft Learn
- Azure Architecture Center
- Azure Well-Architected Framework documentation
- Azure Cloud Adoption Framework documentation
- Official Azure service documentation
- Official Azure pricing pages or curated pricing data
- Official Azure SLA pages
- Official Microsoft security baseline documentation
- Official Microsoft architecture pattern documentation

### 9.2 Low-trust source usage

Low-trust sources may be used for:

- Discovering terms.
- Identifying candidate patterns.
- Detecting recent buzz or announcements.

Low-trust sources should not be used as the only evidence for:

- Service capability claims.
- Cost or pricing claims.
- Security or compliance claims.
- SLA or availability claims.
- Architecture decision records.

---

## 10. Source Freshness Model

Evidence freshness is especially important for Azure services, pricing, quotas, preview/GA status, and regional availability.

| Freshness value | Meaning |
|---|---|
| `current` | Retrieved recently and source is considered up to date for the claim type |
| `recent` | Not latest, but likely acceptable for stable architecture guidance |
| `stale` | Too old for the type of claim; should not be used without verification |
| `unknown` | Retrieval did not provide a reliable publication/update timestamp |

### 10.1 Freshness rules by claim type

| Claim category | Freshness expectation |
|---|---|
| Pricing | Must be current or explicitly marked estimate/assumption |
| Service limits / quotas | Should be current or recent; stale must trigger warning |
| Preview / GA status | Must be current |
| Security/compliance claims | Should be current or recent |
| Architecture patterns | Can tolerate recent or older if pattern is stable |
| WAF design principles | Can tolerate recent if docs are stable |

### 10.2 Stale evidence handling

If evidence is stale but still useful, Archimedes should:

1. Keep the evidence record.
2. Mark `source_freshness = stale`.
3. Lower the claim confidence.
4. Add an Evidence Auditor warning.
5. Avoid using the claim as the sole basis for a major decision.

---

## 11. Claim Classification Rules

### 11.1 Fact classification

Use `fact` only when:

- The statement is directly supported by relevant evidence.
- The source is trusted enough for the claim type.
- The claim is not merely an architectural interpretation.

Good fact:

```text
Azure AI Search provides indexing and retrieval capabilities used by Foundry IQ knowledge bases.
```

Bad fact:

```text
Azure AI Search is the best option for all enterprise search workloads.
```

The second statement is a recommendation or judgment, not a fact.

### 11.2 Assumption classification

Use `assumption` when:

- The statement is inferred from context.
- The user has not confirmed it.
- It affects option selection, risk, cost, or implementation feasibility.

Examples:

```text
The team is likely to prefer managed Azure services over self-managed open-source platforms.
```

```text
The organization may already have Microsoft Entra ID as the enterprise identity provider.
```

### 11.3 Recommendation classification

Use `recommendation` when:

- The statement involves preference, ranking, or design choice.
- The statement synthesizes multiple facts and assumptions.
- The statement depends on priorities or trade-offs.

Example:

```text
Recommend a managed streaming architecture for MVP because it reduces operational burden and improves delivery speed.
```

---

## 12. Evidence Capture by Pipeline Stage

Each stage produces claims and may produce evidence sources.

| Stage | Claim/evidence behavior |
|---|---|
| Intake | Captures user-provided business need as user-input evidence |
| Requirements Extraction | Produces requirement claims, assumptions, and open questions |
| Pattern Detection | Produces pattern classification claims and supporting pattern evidence |
| Options Generation | Produces service capability facts, option trade-off claims, and recommendations |
| Socratic Review | Produces persona findings, risks, assumptions, and recommendation confidence |
| Evidence Audit Checkpoint | Reviews options and Socrates claims before ADR generation |
| ADR Generation | Produces decision claims and links to supporting option/Socrates evidence |
| HLD Generation | Produces design claims, component claims, and diagram rationale |
| Mini WAF Review | Produces WAF findings, risks, and mitigations |
| Final Evidence Audit | Reviews full architecture package before final response/export |
| Re-reasoning | Produces new versions of impacted stage claims and evidence |

---

## 13. Evidence Audit Checkpoints

Archimedes runs evidence audit at two points in the MVP pipeline.

### 13.1 Checkpoint 1: After Socratic Review

Purpose:

```text
Are the architecture options and adversarial debate grounded enough to create an ADR?
```

This checkpoint focuses on:

- Service capability facts.
- Option comparison claims.
- Socrates persona claims.
- Risk claims.
- Unsupported assertions that may influence the ADR.
- Assumptions that require user validation.

If this audit fails, the ADR should not be generated automatically.

### 13.2 Checkpoint 2: Before Final Output

Purpose:

```text
Is the full architecture package evidence-backed and safe to present as a decision brief?
```

This checkpoint focuses on:

- ADR decision rationale.
- HLD component claims.
- WAF findings.
- Security and reliability recommendations.
- Cost assumptions, if present.
- Contradictions across stages.
- Stale or low-trust evidence used in final recommendations.

If this audit fails, the final output should include warnings and unresolved validation items.

---

## 14. Evidence Auditor Responsibilities

The Evidence Auditor is a specialist routine that inspects claims and evidence records. It does not generate new architecture content.

Responsibilities:

1. Check whether factual claims have evidence.
2. Check whether cited evidence actually supports the claim.
3. Check source trust level.
4. Check evidence freshness.
5. Check whether each claim is correctly classified.
6. Identify unsupported claims.
7. Identify irrelevant citations.
8. Identify stale evidence.
9. Identify low-trust sources used for major decisions.
10. Detect contradictions.
11. Identify assumptions requiring user validation.
12. Produce a structured audit result.

---

## 15. Evidence Auditor Input

The Evidence Auditor should receive:

```json
{
  "session_id": "arch_001",
  "audit_scope": "post_socrates",
  "stages_to_audit": ["requirements", "pattern_detection", "options_generation", "socratic_review"],
  "claims": [],
  "evidence_sources": [],
  "artifacts": []
}
```

For final audit:

```json
{
  "session_id": "arch_001",
  "audit_scope": "final_architecture_package",
  "stages_to_audit": [
    "requirements",
    "pattern_detection",
    "options_generation",
    "socratic_review",
    "adr_generation",
    "hld_generation",
    "mini_waf_review"
  ],
  "claims": [],
  "evidence_sources": [],
  "artifacts": []
}
```

---

## 16. Evidence Auditor Output

The Evidence Auditor should produce a structured artifact.

```json
{
  "audit_id": "audit_001",
  "session_id": "arch_001",
  "audit_scope": "post_socrates",
  "overall_evidence_quality": "adequate",
  "recommendation": "proceed_with_warnings",
  "summary": {
    "total_claims": 42,
    "facts_cited": 21,
    "recommendations_with_evidence": 9,
    "assumptions_unvalidated": 5,
    "unsupported_claims": 2,
    "irrelevant_citations": 1,
    "low_trust_sources": 0,
    "stale_citations": 1,
    "contradictions": 0
  },
  "findings": [],
  "requires_user_validation": [],
  "blocking_failures": [],
  "warnings": []
}
```

### 16.1 Audit recommendation values

| Value | Meaning |
|---|---|
| `proceed` | Evidence quality is strong; continue automatically |
| `proceed_with_warnings` | Continue, but show warnings and track unresolved items |
| `review_flagged_items` | Pause or ask user to review important warnings |
| `pause_and_validate` | Do not proceed until critical assumptions or unsupported claims are resolved |

### 16.2 Overall evidence quality values

| Value | Meaning |
|---|---|
| `strong` | Most factual claims have relevant, trusted, current evidence |
| `adequate` | Enough evidence exists to proceed; some warnings remain |
| `weak` | Too many unsupported, stale, low-trust, or irrelevant citations |

---

## 17. Audit Finding Model

Each audit finding should be structured.

```json
{
  "finding_id": "aud_find_001",
  "severity": "warning",
  "category": "unsupported_claim",
  "claim_id": "clm_019",
  "evidence_id": null,
  "message": "The claim about 100K TPS throughput has no supporting source.",
  "recommended_action": "Retrieve current Event Hubs throughput documentation or downgrade claim to assumption.",
  "blocks_progression": false
}
```

### 17.1 Finding categories

| Category | Description |
|---|---|
| `unsupported_claim` | Claim has no evidence but is presented as fact |
| `irrelevant_citation` | Evidence does not support the specific claim |
| `low_trust_source` | Source is not authoritative enough for the claim type |
| `stale_source` | Source is too old for the claim type |
| `misclassified_claim` | Claim type should be fact/assumption/recommendation but is incorrectly labeled |
| `contradiction` | Two or more sources or claims disagree |
| `missing_user_validation` | Important assumption requires user confirmation |
| `weak_confidence` | Claim confidence is too low for decision impact |
| `missing_kb_version` | Foundry IQ evidence lacks KB/source version metadata |

### 17.2 Severity values

| Severity | Meaning |
|---|---|
| `info` | Useful note; does not affect progression |
| `warning` | Should be visible but does not block progression |
| `error` | Significant issue; may require review |
| `blocking` | Must be fixed or explicitly handled before progression |

---

## 18. Audit Decision Rules

### 18.1 Blocking conditions

Evidence audit should block progression when:

1. A critical recommendation depends on unsupported factual claims.
2. A service limit, pricing, SLA, security, or compliance claim has no trusted evidence.
3. A contradiction affects the selected architecture option.
4. A required assumption is unvalidated and materially changes the decision.
5. Evidence from low-trust sources is used as the only support for an ADR decision.

### 18.2 Warning conditions

Evidence audit should warn but not block when:

1. A non-critical claim has weak or stale evidence.
2. A recommendation is evidence-informed but not directly source-backed.
3. An assumption is plausible and non-critical.
4. Source freshness is unknown for stable architecture guidance.
5. Citation is relevant but not the best available source.

### 18.3 Proceed conditions

Evidence audit can allow progression when:

1. Critical facts are supported by relevant trusted sources.
2. Recommendations clearly separate evidence from judgment.
3. Assumptions are visible and either validated or non-blocking.
4. No material contradictions remain unresolved.

---

## 19. Contradiction Detection

Contradiction detection is required because architecture decisions often depend on changing service details.

### 19.1 Types of contradictions

| Type | Example |
|---|---|
| Source contradiction | Two sources disagree on service limits |
| Stage contradiction | Requirements say single-region; HLD proposes multi-region |
| Recommendation contradiction | Socrates recommends managed service; ADR selects self-managed service without explaining why |
| Assumption contradiction | User validates low budget; cost model assumes premium SKUs |
| Freshness contradiction | Older source says preview; newer source says GA |

### 19.2 MVP contradiction detection approach

For MVP, use a pragmatic approach:

1. Group claims by topic tags.
2. Compare claims within the same topic.
3. Use exact or semantic matching for key values.
4. Flag conflicting numeric, status, or decision values.
5. Let Evidence Auditor classify severity.

Example topic tags:

```text
service:event-hubs
category:throughput
category:pricing
category:sla
category:security
requirement:availability
stage:adr
```

### 19.3 Contradiction output

```json
{
  "finding_id": "aud_find_014",
  "severity": "blocking",
  "category": "contradiction",
  "message": "Options stage assumes single-region deployment, but HLD includes active-active multi-region without a requirement change record.",
  "claim_ids": ["clm_021", "clm_044"],
  "recommended_action": "Create a change event or revise HLD to match the selected option."
}
```

---

## 20. User Validation Flow for Assumptions

Some assumptions must be validated before they are used in decisions.

### 20.1 Validation states

| State | Meaning |
|---|---|
| `unvalidated` | Assumption has not been reviewed by user |
| `validated` | User confirmed the assumption |
| `rejected` | User rejected the assumption |
| `deferred` | User allows progression but accepts risk |

### 20.2 User validation prompt

When an assumption is material, the frontend should present it clearly:

```text
Archimedes inferred the following assumption:

“The implementation team has limited Kafka operations experience.”

This affects the recommendation to prefer managed Event Hubs over AKS-hosted Kafka.

Choose one:
[Confirm] [Reject] [Defer for now]
```

### 20.3 Validation impact

If the user rejects a material assumption, Archimedes should:

1. Create a `ChangeEvent`.
2. Mark impacted stages.
3. Re-run options or Socrates if required.
4. Produce updated artifacts and diff.

---

## 21. Evidence Capture Flow

The evidence capture flow runs inside every stage.

```text
Agent/tool retrieves information
        │
        ▼
Create EvidenceSource records
        │
        ▼
Agent produces claims
        │
        ▼
Link claims to evidence IDs
        │
        ▼
Create StagePatch
        │
        ▼
StagePatch Validator checks schema and required links
        │
        ▼
Architecture State Manager writes artifact, claims, evidence
        │
        ▼
Evidence Auditor later checks quality and consistency
```

---

## 22. Storage Design Summary

The detailed database design is covered in `04-database-design.md`. Evidence and claims are stored in separate containers.

### 22.1 Claims container

Purpose:

```text
Store statements made by Archimedes, linked to evidence and stages.
```

Suggested partition key:

```text
/session_id
```

Common queries:

```text
Get all claims for a session
Get claims by stage
Get claims by type
Get claims requiring user validation
Get claims linked to a specific evidence source
```

### 22.2 Evidence container

Purpose:

```text
Store retrieved source metadata and excerpts.
```

Suggested partition key:

```text
/session_id
```

Common queries:

```text
Get evidence for a session
Get evidence by trust level
Get evidence by freshness
Get Foundry IQ evidence by kb_version
Get evidence used in a specific stage
```

### 22.3 Audit artifacts

Evidence audit outputs should be stored as `VersionedArtifact` records with stage values such as:

```text
post_socrates_evidence_audit
final_evidence_audit
```

---

## 23. StagePatch Validation Rules for Claims and Evidence

Before applying a StagePatch, the validator should check:

1. Every `claim_id` is unique within the patch.
2. Every `evidence_id` is unique within the patch.
3. Every evidence ID referenced by a claim exists either in the patch or already in the session evidence store.
4. Every `fact` claim has at least one evidence ID unless marked as `user_input`.
5. Every `assumption` with confidence below threshold is marked `requires_user_validation = true`.
6. Every `recommendation` links to at least one supporting fact or assumption when possible.
7. Every Foundry IQ evidence source includes `kb_name`, `kb_version`, and `retrieved_at` when available.
8. No factual claim is supported only by `model_judgment`.

---

## 24. Evidence Auditor Prompt Contract

The full prompt belongs in `07-agent-specifications.md`, but the Evidence Auditor must follow this contract.

### 24.1 Role

```text
You are the Evidence Auditor for Archimedes. Your job is to validate evidence quality, not to generate new architecture content.
```

### 24.2 Required checks

```text
1. Citation presence
2. Citation relevance
3. Source trust
4. Source freshness
5. Claim classification
6. Contradiction detection
7. User validation needs
8. KB/source version completeness
```

### 24.3 Required output

The Evidence Auditor must return structured JSON compatible with the audit artifact schema, including:

- Audit scope.
- Summary counts.
- Overall evidence quality.
- Recommendation.
- Findings.
- Blocking failures.
- Warnings.
- Required user validations.

---

## 25. Evidence Use in ADR Generation

ADR generation must use evidence and claims carefully.

The ADR should include:

1. Decision title.
2. Context.
3. Considered options.
4. Selected option.
5. Evidence-backed facts.
6. Assumptions used.
7. Consequences.
8. Risks and mitigations.
9. Evidence audit status.

Example ADR evidence section:

```markdown
## Evidence Summary

### Facts
- Azure Event Hubs is a managed event ingestion service suitable for high-throughput streaming workloads. [EV-001]
- Azure Stream Analytics supports real-time stream processing patterns. [EV-002]

### Assumptions
- The team prefers managed Azure services for MVP delivery. [ASM-001: unvalidated]

### Recommendations
- Prefer Event Hubs + Stream Analytics for MVP due to lower operational burden and faster delivery. This recommendation is based on EV-001, EV-002, and ASM-001.
```

---

## 26. Evidence Use in HLD Generation

The HLD should not cite every component box in the diagram, but it should be able to explain why each major component exists.

For each major component, capture:

- Component name.
- Design role.
- Supporting claim IDs.
- Supporting evidence IDs.
- Assumptions, if any.

Example:

```json
{
  "component": "Azure Event Hubs",
  "design_role": "High-throughput transaction event ingestion",
  "supporting_claim_ids": ["clm_001", "clm_027"],
  "supporting_evidence_ids": ["ev_001", "ev_002"],
  "assumption_ids": []
}
```

---

## 27. Evidence Use in Socrates

Socrates personas may produce both evidence-backed findings and judgment-based critique.

Persona findings should classify each finding:

| Finding type | Meaning |
|---|---|
| `fact_based_risk` | Risk based on documented service behavior or constraints |
| `assumption_based_risk` | Risk based on inferred context |
| `judgment_based_risk` | Expert critique based on trade-off reasoning |
| `question` | Open item requiring validation |

Example:

```json
{
  "persona": "SRE / Ops Lead",
  "finding": "Self-managed Kafka on AKS increases operational burden for incident response and upgrades.",
  "finding_type": "judgment_based_risk",
  "supporting_claim_ids": ["clm_030"],
  "severity": "medium"
}
```

Socrates output should not pretend that every risk is a sourced fact. Some risks are legitimate expert judgment and should be labeled accordingly.

---

## 28. Evidence in Re-Reasoning

When requirements change, old evidence and claims should not be deleted.

Instead:

1. New claims and evidence are created for the new artifact version.
2. Old claims remain linked to old artifact versions.
3. ChangeEvent records explain what changed.
4. Diff artifacts show changed claims, assumptions, recommendations, and evidence.

Example:

```text
Requirement changed: 10K TPS → 100K TPS

Old recommendation:
- Event Hubs + Stream Analytics for MVP.

New recommendation:
- Re-evaluate Event Hubs Premium, Kafka/Flink, and multi-region active-active options.

Evidence changed:
- New service limit and scaling evidence retrieved.
- Cost sensitivity increased from medium to high.
```

---

## 29. Frontend Display Requirements

The frontend should make evidence visible but not overwhelming.

### 29.1 Claim badges

Use simple badges:

```text
FACT
ASSUMPTION
RECOMMENDATION
```

### 29.2 Evidence panel

For each major artifact, show:

```text
Evidence Quality: Adequate
Facts cited: 21
Warnings: 3
Assumptions requiring validation: 2
```

### 29.3 Assumption review panel

Show material assumptions separately:

```text
Assumption: Team has limited Kafka operations experience
Affects: Options ranking, Socrates review, ADR
Status: Unvalidated
Action: Confirm / Reject / Defer
```

### 29.4 Audit findings panel

Show blocking and warning findings:

```text
Blocking:
- None

Warnings:
- Cost estimate uses curated pricing data; validate before production use.
- Data residency requirement not confirmed.
```

---

## 30. Observability Events

Evidence and claims operations should emit events.

| Event | When emitted |
|---|---|
| `claim.created` | ClaimRecord stored |
| `evidence.created` | EvidenceSource stored |
| `claim.evidence_linked` | Claim references evidence |
| `evidence.audit.started` | Evidence Auditor starts |
| `evidence.audit.completed` | Evidence audit completes |
| `evidence.audit.failed` | Evidence audit fails |
| `assumption.validation_requested` | User validation needed |
| `assumption.validated` | User confirms assumption |
| `assumption.rejected` | User rejects assumption |
| `contradiction.detected` | Audit finds contradiction |

Each event should include:

- `session_id`
- `stage`
- `stage_run_id`, if applicable
- `artifact_version`, if applicable
- `claim_id` or `evidence_id`, if applicable
- `severity`, if applicable

---

## 31. MVP Implementation Checklist

For MVP, implement the following:

### Must have

- [ ] `ClaimRecord` model.
- [ ] `EvidenceSource` model.
- [ ] Claims container.
- [ ] Evidence container.
- [ ] StagePatch validation for claim/evidence references.
- [ ] Evidence capture from Foundry IQ retrieval.
- [ ] Evidence capture from function tools.
- [ ] Post-Socrates Evidence Audit artifact.
- [ ] Final Evidence Audit artifact.
- [ ] Basic unsupported claim detection.
- [ ] Basic assumption validation flagging.
- [ ] Evidence quality summary in frontend.

### Should have

- [ ] Source trust scoring.
- [ ] Freshness scoring.
- [ ] KB version display.
- [ ] Assumption review panel.
- [ ] Contradiction detection for obvious numeric/status conflicts.

### Can defer

- [ ] Advanced semantic contradiction detection.
- [ ] Full claim graph visualization.
- [ ] Enterprise policy-based source allowlist.
- [ ] Formal compliance evidence package export.
- [ ] Architecture review board approval workflow.

---

## 32. Example End-to-End Evidence Flow

User input:

```text
Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.
```

### 32.1 Requirement claim

```json
{
  "claim_id": "clm_req_001",
  "claim": "The platform must process 10K transactions per second.",
  "type": "fact",
  "confidence": 1.0,
  "stage": "requirements_extraction",
  "evidence_ids": ["ev_user_001"],
  "requires_user_validation": false
}
```

### 32.2 User input evidence

```json
{
  "evidence_id": "ev_user_001",
  "source": "User input",
  "retrieved_via": "user_input",
  "retrieved_at": "2026-06-09T10:00:00Z",
  "excerpt": "processing 10K TPS with PCI-DSS constraints and 99.95% availability",
  "trust_level": "high",
  "source_freshness": "current"
}
```

### 32.3 Recommendation claim

```json
{
  "claim_id": "clm_rec_001",
  "claim": "Prefer a managed streaming architecture for MVP to reduce operational burden and accelerate delivery.",
  "type": "recommendation",
  "confidence": 0.82,
  "stage": "socratic_review",
  "evidence_ids": ["ev_azure_001", "ev_azure_002", "ev_user_001"],
  "requires_user_validation": false
}
```

### 32.4 Assumption claim

```json
{
  "claim_id": "clm_asm_001",
  "claim": "The implementation team may prefer managed Azure services over self-managed platforms for the initial release.",
  "type": "assumption",
  "confidence": 0.6,
  "stage": "socratic_review",
  "evidence_ids": [],
  "requires_user_validation": true
}
```

### 32.5 Audit result

```json
{
  "overall_evidence_quality": "adequate",
  "recommendation": "proceed_with_warnings",
  "warnings": [
    "One material assumption requires user validation: managed-service preference.",
    "Pricing claims should be validated before production budgeting."
  ],
  "blocking_failures": []
}
```

---

## 33. Open Design Questions

| Question | Recommendation for MVP |
|---|---|
| Should every sentence in an artifact be represented as a claim? | No. Capture major claims only. |
| Should recommendations require citations? | They should link to supporting facts and assumptions, but not direct citations for every judgment. |
| Should assumptions block progression? | Only material assumptions should block or require user validation. |
| Should low-trust evidence be stored? | Yes, but mark it as low trust and avoid using it for decisions. |
| Should Evidence Auditor be deterministic or LLM-based? | Hybrid. Deterministic checks first, LLM for relevance/classification review. |
| Should old evidence be updated after KB refresh? | No. Create new evidence records with new KB version. |

---

## 34. Summary

The Archimedes evidence and claims model provides the reasoning quality layer for the architecture workbench.

The key design decisions are:

1. Claims and evidence are separate entities.
2. Claims are classified as facts, assumptions, or recommendations.
3. Factual claims require relevant trusted evidence.
4. Recommendations are allowed to be expert judgment, but must link to supporting facts and assumptions.
5. Foundry IQ evidence must carry KB/source version metadata.
6. Evidence audits run twice in the MVP pipeline.
7. Assumptions are visible and can trigger user validation.
8. Contradictions are flagged rather than hidden.
9. Evidence records are append-only to preserve historical auditability.

This model is essential for making Archimedes credible as an architecture workbench rather than a generic LLM-driven documentation generator.

# Archimedes Tool Specifications

**Document ID:** `09-tool-specifications.md`  
**Solution:** Archimedes — AI Architecture Workbench  
**Version:** v2.2  
**Status:** Implementation-ready baseline  
**Last updated:** 2026-06-09  
**Related documents:** `01-archimedes-hld.md`, `03-pydantic-schemas.md`, `06-stage-pipeline.md`, `07-agent-specifications.md`, `08-socrates-engine.md`, `10-foundry-iq-knowledge-base.md`, `11-evidence-and-claims.md`, `12-dependency-and-rereasoning.md`

---

## 1. Purpose

This document defines the tool layer for Archimedes.

The tool layer gives agents and orchestrator services access to deterministic functionality that should not be left to language-model reasoning alone. Tools are used for retrieval, rendering checks, cost estimation, ADR formatting, STRIDE mapping, quality gate evaluation, dependency impact analysis, artifact diffing, claim/evidence normalization, and state-safe patch preparation.

The key architectural principle is:

> Agents reason. Tools calculate, validate, normalize, retrieve, format, or compare. The Architecture State Manager persists state. Agents never directly mutate persisted state.

This document is implementation-facing and should guide tool function design, tool input/output models, error handling, test cases, and tool access boundaries.

---

## 2. Scope

This document covers:

- Tool categories and ownership.
- Agent-callable tools vs internal service tools.
- External tool adapters such as Foundry IQ and Foundry Web Search.
- App-local deterministic Python function tools.
- Tool input/output contracts.
- Tool error behavior.
- Tool observability.
- Tool security and approval rules.
- Tool access matrix by agent/routine.
- MVP vs later-phase tooling.

This document does not cover:

- Agent prompts in full. See `07-agent-specifications.md`.
- Socrates persona prompts and workflow internals. See `08-socrates-engine.md`.
- Pydantic model implementation in full. See `03-pydantic-schemas.md`.
- Cosmos DB persistence implementation. See `04-database-design.md`.
- Foundry IQ source curation details. See `10-foundry-iq-knowledge-base.md`.
- FastAPI route definitions. See `05-api-contracts.md`.

---

## 3. Tool Design Principles

The Archimedes tool layer follows these principles:

1. **Deterministic where possible**  
   Tools should produce predictable outputs for the same inputs. LLM-based judgement should remain in agents, not hidden inside utility tools.

2. **No direct database mutation from agents**  
   Agent-callable tools may read session context, retrieve evidence, or produce structured output, but persisted writes must flow through the Architecture State Manager.

3. **Structured inputs and outputs**  
   Tool inputs and outputs should use Pydantic models or JSON-schema-compatible structures.

4. **Explicit assumptions**  
   Tools such as cost estimators must return assumptions and warnings, not just final numbers.

5. **Fail safely**  
   Tool failures should return structured errors. They should not silently produce partial or misleading outputs.

6. **Trace every call**  
   Every tool call should be traceable by `session_id`, `stage_run_id`, `tool_name`, `duration_ms`, and result status.

7. **Keep Foundry IQ focused on retrieval**  
   Foundry IQ knowledge bases expose retrieval via `knowledge_base_retrieve`. Custom logic such as cost estimation, STRIDE, Mermaid render checks, quality gates, and diffing must remain app-local.

8. **Minimize tool approval prompts for MVP**  
   MVP tools should use non-destructive read/compute behavior and should not require human approval at runtime. User approval belongs at workflow-level decisions, not for every utility call.

9. **Separate external adapters from business logic**  
   Foundry IQ and Web Search adapters normalize retrieval results into Archimedes `EvidenceSource` records. They should not decide architecture recommendations.

10. **Tool outputs should be stage-patch friendly**  
   Tool outputs should be easy for specialist routines to embed into a `StagePatch` as artifact content, `ClaimRecord`, `EvidenceSource`, warnings, or quality gate results.

---

## 4. Tool Categories

Archimedes uses five tool categories.

| Category | Description | Examples | Agent-callable? |
|---|---|---|---|
| External retrieval adapters | Connect to external knowledge or web sources | `retrieve_from_foundry_iq`, `search_web_for_current_info` | Yes, selectively |
| Deterministic validation tools | Validate or check generated outputs | `mermaid_render_check`, `evaluate_quality_gate`, `validate_stage_patch_shape` | Some |
| Deterministic generation/formatting tools | Produce standardized artifacts from structured inputs | `format_adr`, `format_cost_table`, `format_waf_findings` | Yes |
| Analysis utilities | Compute impact, diffs, threat mappings, cost estimates | `compute_change_impact`, `generate_artifact_diff`, `run_stride_analysis`, `estimate_azure_cost` | Some |
| Internal state/service utilities | Used by orchestrator/state manager, not directly by agents | `apply_stage_patch`, `load_session_snapshot`, `persist_tool_trace` | No |

---

## 5. Tool Runtime Boundaries

### 5.1 Agent-callable tools

Agent-callable tools are exposed to MAF agents/routines. They are safe to call during reasoning and artifact generation.

Examples:

- `retrieve_from_foundry_iq`
- `search_web_for_current_info`
- `mermaid_render_check`
- `estimate_azure_cost`
- `format_adr`
- `run_stride_analysis`
- `evaluate_quality_gate`
- `compute_change_impact`
- `generate_artifact_diff`

### 5.2 Orchestrator-only tools/services

These are not exposed to specialist agents directly. They are invoked by the orchestrator, pipeline controller, or Architecture State Manager.

Examples:

- `validate_stage_patch`
- `apply_stage_patch`
- `load_architecture_session`
- `load_stage_artifacts`
- `write_changelog_event`
- `persist_tool_trace`
- `create_stage_run_id`
- `generate_idempotency_key`

### 5.3 External managed tools

These are external capabilities integrated through Foundry Agent Service, MCP, SDKs, or service APIs.

Examples:

- Foundry IQ MCP `knowledge_base_retrieve`
- Foundry Web Search / Grounding with Bing

### 5.4 Tool placement

Recommended implementation placement:

```text
src/archimedes/tools/
├── __init__.py
├── base.py
├── retrieval/
│   ├── foundry_iq.py
│   └── web_search.py
├── rendering/
│   └── mermaid.py
├── costing/
│   ├── azure_cost_estimator.py
│   └── pricing_catalog.py
├── security/
│   └── stride.py
├── adr/
│   └── formatter.py
├── quality/
│   ├── gates.py
│   └── stage_patch_validator.py
├── evidence/
│   ├── normalizer.py
│   ├── trust_scoring.py
│   └── audit_helpers.py
├── dependency/
│   ├── impact_engine.py
│   └── dependency_rules.py
├── diff/
│   └── artifact_diff.py
└── telemetry/
    └── tool_trace.py
```

---

## 6. Common Tool Models

The full Pydantic schema implementation belongs in `03-pydantic-schemas.md`. This section defines the common shapes expected by tools.

### 6.1 Tool call context

Every tool should accept or derive a tool context.

```python
class ToolCallContext(BaseModel):
    session_id: str
    stage: str | None = None
    stage_run_id: str | None = None
    requested_by: str | None = None  # agent/routine name
    correlation_id: str | None = None
    user_id: str | None = None
```

### 6.2 Standard tool result

```python
class ToolResult(BaseModel):
    tool_name: str
    status: Literal["success", "partial_success", "failed"]
    duration_ms: int | None = None
    warnings: list[str] = []
    errors: list[ToolError] = []
    data: dict[str, Any] = {}
```

### 6.3 Tool error

```python
class ToolError(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = {}
```

Common error codes:

| Code | Meaning | Retryable? |
|---|---|---|
| `INVALID_INPUT` | Input failed schema or semantic validation | No |
| `MISSING_REQUIRED_FIELD` | Required input field missing | No |
| `EXTERNAL_SERVICE_TIMEOUT` | Foundry IQ, Web Search, or another external service timed out | Yes |
| `EXTERNAL_SERVICE_ERROR` | External service returned an error | Maybe |
| `RENDER_CHECK_FAILED` | Mermaid render check failed | No, unless auto-correction is enabled |
| `PRICING_DATA_MISSING` | Cost estimator lacks price for requested SKU/region | No |
| `UNSUPPORTED_STAGE` | Tool does not support requested stage | No |
| `VERSION_CONFLICT` | Patch or diff requested from stale base version | No |
| `INSUFFICIENT_EVIDENCE` | Retrieval/audit found weak evidence | No |

### 6.4 Tool trace event

```python
class ToolTraceEvent(BaseModel):
    trace_id: str
    session_id: str
    stage: str | None
    stage_run_id: str | None
    tool_name: str
    called_by: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    status: Literal["success", "partial_success", "failed"]
    input_hash: str
    output_hash: str | None = None
    error_code: str | None = None
```

---

## 7. Tool Access Matrix

| Tool | Orchestrator | Requirements | Pattern Detector | Options | Socrates | ADR | HLD | WAF | Evidence Auditor | Re-reasoning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `retrieve_from_foundry_iq` | Yes | Yes | Yes | Yes | Optional | Optional | Yes | Yes | Optional | Yes |
| `search_web_for_current_info` | Yes | No | Optional | Optional | No | No | Optional | Optional | Optional | Optional |
| `mermaid_render_check` | Yes | No | No | No | No | No | Yes | No | No | Yes |
| `estimate_azure_cost` | Yes | No | No | Optional | Optional | No | Optional | Optional | No | Yes |
| `format_adr` | Yes | No | No | No | No | Yes | No | No | No | Yes |
| `run_stride_analysis` | Yes | No | No | Optional | Optional | No | Optional | Yes | No | Yes |
| `evaluate_quality_gate` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `compute_change_impact` | Yes | No | No | No | No | No | No | No | No | Yes |
| `generate_artifact_diff` | Yes | No | No | No | No | No | No | No | No | Yes |
| `normalize_claims_and_evidence` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `classify_source_trust` | Yes | Optional | Optional | Optional | No | No | Optional | Yes | Yes | Optional |
| `validate_stage_patch` | Yes | No | No | No | No | No | No | No | No | Yes |
| `apply_stage_patch` | Yes, internal | No | No | No | No | No | No | No | No | Yes, internal |

Notes:

- Socrates personas should not normally call tools directly in MVP. They should analyze the already-grounded options and requirements. Deep mode may allow limited retrieval later.
- Evidence Auditor may query the evidence/claim stores and may optionally retrieve source snippets if source validation requires additional context.
- `apply_stage_patch` is not a reasoning tool. It is a State Manager operation.

---

## 8. External Retrieval Tools

## 8.1 `retrieve_from_foundry_iq`

### Purpose

Retrieve grounded architecture evidence from the Archimedes Foundry IQ knowledge base.

This adapter wraps the Foundry IQ MCP tool `knowledge_base_retrieve` and normalizes results into `EvidenceSource` records.

### Used by

- Requirements Engineer
- Pattern Detector
- Options Generator
- HLD Designer
- WAF Reviewer
- Evidence Auditor, optionally
- Re-reasoning pipeline

### Inputs

```python
class FoundryIQRetrieveInput(BaseModel):
    context: ToolCallContext
    query: str
    purpose: Literal[
        "requirements_grounding",
        "pattern_grounding",
        "options_grounding",
        "hld_grounding",
        "waf_grounding",
        "evidence_validation",
        "rereasoning_grounding"
    ]
    top_k: int = 5
    filters: dict[str, Any] = {}
    min_trust_level: Literal["high", "medium", "low"] = "medium"
```

### Outputs

```python
class FoundryIQRetrieveOutput(BaseModel):
    query: str
    kb_name: str
    kb_version: str
    retrieved_at: datetime
    evidence_sources: list[EvidenceSource]
    raw_result_ref: str | None = None
    warnings: list[str] = []
```

### Behavior

1. Validate query is non-empty.
2. Call Foundry IQ MCP `knowledge_base_retrieve`.
3. Normalize retrieved chunks into `EvidenceSource` records.
4. Attach KB/source metadata:
   - `kb_name`
   - `kb_version`
   - `source_document_version`
   - `retrieved_at`
5. Classify source trust.
6. Classify freshness.
7. Return normalized evidence.

### Constraints

- This tool retrieves evidence only.
- It must not generate recommendations.
- It must not perform cost calculation, STRIDE, quality gate evaluation, or Mermaid validation.
- Custom logic remains app-local.

### Failure behavior

| Failure | Result |
|---|---|
| Foundry IQ timeout | `failed`, `EXTERNAL_SERVICE_TIMEOUT`, retryable |
| Empty results | `partial_success`, warning `NO_RESULTS_FOUND` |
| Low-trust-only results | `partial_success`, warning `LOW_TRUST_RESULTS_ONLY` |
| MCP configuration missing | `failed`, `EXTERNAL_SERVICE_ERROR`, not retryable until configured |

### Example call

```json
{
  "query": "Azure architecture guidance for real-time fraud detection event streaming PCI DSS",
  "purpose": "options_grounding",
  "top_k": 6,
  "filters": {
    "source_category": ["azure_architecture_center", "waf", "service_limits"]
  }
}
```

### Example output summary

```json
{
  "query": "Azure architecture guidance for real-time fraud detection event streaming PCI DSS",
  "kb_name": "azure-architecture-kb",
  "kb_version": "2026-06-09",
  "evidence_sources": [
    {
      "evidence_id": "ev_001",
      "source": "Azure Architecture Center - Stream processing",
      "retrieved_via": "foundry_iq",
      "trust_level": "high",
      "source_freshness": "current"
    }
  ],
  "warnings": []
}
```

---

## 8.2 `search_web_for_current_info`

### Purpose

Retrieve current public information that may not be present in the curated knowledge base.

This is used only for volatile information such as:

- Azure service updates.
- Preview/GA announcements.
- Recent deprecations.
- Current pricing notes when deterministic pricing data needs validation.

### Used by

- Orchestrator
- Options Generator, selectively
- HLD Designer, selectively
- WAF Reviewer, selectively
- Re-reasoning pipeline, selectively

### Inputs

```python
class WebSearchInput(BaseModel):
    context: ToolCallContext
    query: str
    purpose: Literal[
        "current_service_update",
        "pricing_validation",
        "deprecation_check",
        "feature_availability_check"
    ]
    allowed_domains: list[str] = [
        "learn.microsoft.com",
        "azure.microsoft.com",
        "techcommunity.microsoft.com",
        "devblogs.microsoft.com"
    ]
    recency_days: int | None = None
    max_results: int = 5
```

### Outputs

```python
class WebSearchOutput(BaseModel):
    query: str
    searched_at: datetime
    evidence_sources: list[EvidenceSource]
    warnings: list[str] = []
```

### Behavior

1. Restrict to approved domains by default.
2. Prefer Microsoft official sources.
3. Normalize result snippets into `EvidenceSource` records with `retrieved_via="web_search"`.
4. Mark freshness based on result date when available.
5. Return warnings if results are third-party or stale.

### Constraints

- Web Search should not replace Foundry IQ for stable architecture grounding.
- Web Search should not be used as the primary cost calculation engine.
- Pricing should come from the deterministic pricing catalog where possible.

---

## 9. Rendering and Diagram Tools

## 9.1 `mermaid_render_check`

### Purpose

Check whether generated Mermaid syntax is likely to render successfully.

The tool is intentionally named `mermaid_render_check`, not `validate_mermaid`, because full validation is difficult without the Mermaid renderer. The MVP may perform a basic syntax check or call Mermaid CLI/browser rendering when available.

### Used by

- HLD Designer
- Orchestrator
- Re-reasoning pipeline for HLD diffs

### Inputs

```python
class MermaidRenderCheckInput(BaseModel):
    context: ToolCallContext
    diagram_type: Literal[
        "flowchart",
        "sequence",
        "class",
        "state",
        "c4_context",
        "c4_container",
        "unknown"
    ] = "unknown"
    mermaid_source: str
    check_mode: Literal["basic", "cli", "browser"] = "basic"
    auto_fix: bool = False
```

### Outputs

```python
class MermaidRenderCheckOutput(BaseModel):
    renderable: bool
    check_mode: Literal["basic", "cli", "browser"]
    errors: list[str] = []
    warnings: list[str] = []
    corrected_source: str | None = None
```

### Behavior

MVP behavior:

1. Verify source is non-empty.
2. Check for common invalid patterns:
   - unclosed code blocks
   - unsupported diagram declaration
   - obvious quote/bracket imbalance
   - invalid arrows in common flowcharts
3. Optionally call Mermaid CLI if available in the container.
4. Return corrected syntax only if `auto_fix=true` and the fix is trivial.

Post-MVP behavior:

- Render the diagram in a browser-based sandbox and capture errors.
- Store rendered SVG/PNG in Blob Storage.
- Return artifact URI.

### Failure behavior

| Failure | Result |
|---|---|
| Empty source | `renderable=false`, `INVALID_INPUT` |
| CLI unavailable | `partial_success`, fallback to basic mode |
| Render error | `renderable=false`, errors populated |

### Example

```json
{
  "diagram_type": "flowchart",
  "mermaid_source": "flowchart LR\n  User --> API\n  API --> CosmosDB",
  "check_mode": "basic",
  "auto_fix": false
}
```

---

## 10. Costing Tools

## 10.1 `estimate_azure_cost`

### Purpose

Estimate Azure costs using a curated local pricing catalog and explicit assumptions.

This is an assumption-first estimator, not a precise billing engine.

### Used by

- Orchestrator
- Options Generator, optionally
- Socrates FinOps persona, optionally through orchestrator-prepared context
- Re-reasoning pipeline

### Inputs

```python
class CostResourceInput(BaseModel):
    service: str
    sku: str | None = None
    region: str
    quantity: float = 1
    unit: str | None = None
    hours_per_month: float | None = 730
    usage_assumptions: list[str] = []
    metadata: dict[str, Any] = {}

class AzureCostEstimateInput(BaseModel):
    context: ToolCallContext
    resources: list[CostResourceInput]
    pricing_catalog_version: str
    currency: str = "USD"
    scale_label: str = "expected"
    include_warnings: bool = True
```

### Outputs

```python
class CostRange(BaseModel):
    low: float
    expected: float
    high: float
    currency: str = "USD"

class CostDriverOutput(BaseModel):
    service: str
    percentage_of_total: float | None = None
    sensitivity: Literal["low", "medium", "high"]
    notes: list[str] = []

class AzureCostEstimateOutput(BaseModel):
    assumptions: list[str]
    resource_sizing: list[dict[str, Any]]
    pricing_source: str
    pricing_catalog_version: str
    monthly_estimate: CostRange
    annual_estimate: CostRange
    major_cost_drivers: list[CostDriverOutput]
    cost_sensitivity: Literal["low", "medium", "high"]
    warnings: list[str] = []
    missing_prices: list[dict[str, Any]] = []
```

### Behavior

1. Validate all resources include service and region.
2. Look up SKU/region prices in local pricing catalog.
3. If price is unavailable, add to `missing_prices` and continue if possible.
4. Produce low/expected/high ranges.
5. Return assumptions and major cost drivers.
6. Flag scale-sensitive services.

### Assumption rules

The tool must explicitly state assumptions such as:

- Region.
- Pay-as-you-go vs reserved pricing.
- Hours per month.
- Throughput/transaction volume assumptions.
- Egress inclusion or exclusion.
- Semantic ranker/agentic retrieval token costs inclusion or exclusion.
- Logging/monitoring costs inclusion or exclusion.

### Constraints

- Do not scrape public pricing pages inside this tool.
- Do not silently use a default price when SKU is unknown.
- Do not output a single exact number without range and assumptions.

### Example output warning

```json
{
  "warnings": [
    "Egress charges are not included.",
    "Azure AI Search semantic ranker and agentic retrieval token costs are estimated separately.",
    "Pricing catalog version is 2026-06-01; validate before production use."
  ]
}
```

---

## 11. ADR and Artifact Formatting Tools

## 11.1 `format_adr`

### Purpose

Format a structured architecture decision into a Markdown ADR using a consistent template.

This tool does not decide the architecture. It only formats a decision that was already produced by the ADR Writer routine.

### Used by

- ADR Writer
- Orchestrator
- Re-reasoning pipeline

### Inputs

```python
class ADRFormatInput(BaseModel):
    context: ToolCallContext
    adr_id: str
    title: str
    status: Literal["proposed", "accepted", "superseded", "deprecated"] = "proposed"
    date: date
    decision_context: str
    considered_options: list[dict[str, Any]]
    selected_option_id: str
    decision: str
    rationale: str
    consequences_positive: list[str] = []
    consequences_negative: list[str] = []
    assumptions: list[str] = []
    evidence_ids: list[str] = []
    supersedes_adr_id: str | None = None
```

### Outputs

```python
class ADRFormatOutput(BaseModel):
    adr_markdown: str
    title: str
    adr_id: str
    status: str
    warnings: list[str] = []
```

### Behavior

1. Validate required fields.
2. Format as Markdown.
3. Include evidence references as IDs, not raw citation text.
4. Include assumptions separately from facts.
5. Include supersession metadata if present.

### ADR template

```text
# ADR-{id}: {title}

Status: {status}
Date: {date}
Supersedes: {supersedes_adr_id}

## Context
...

## Decision
...

## Considered Options
...

## Rationale
...

## Consequences
### Positive
...
### Negative
...

## Assumptions
...

## Evidence References
...
```

---

## 11.2 `format_waf_findings`

### Purpose

Normalize Well-Architected Framework review findings into a consistent table-oriented structure for artifacts and UI.

### Used by

- WAF Reviewer
- Orchestrator

### Inputs

```python
class WAFFindingInput(BaseModel):
    pillar: Literal[
        "reliability",
        "security",
        "cost_optimization",
        "operational_excellence",
        "performance_efficiency"
    ]
    finding: str
    severity: Literal["low", "medium", "high", "critical"]
    recommendation: str
    evidence_ids: list[str] = []
    assumption_ids: list[str] = []

class WAFFormatInput(BaseModel):
    context: ToolCallContext
    findings: list[WAFFindingInput]
```

### Outputs

```python
class WAFFormatOutput(BaseModel):
    findings_by_pillar: dict[str, list[dict[str, Any]]]
    summary: dict[str, Any]
    markdown: str
```

### Behavior

- Group findings by WAF pillar.
- Sort by severity.
- Produce a concise summary and Markdown table.
- Flag missing pillars as warnings.

---

## 12. Security Analysis Tools

## 12.1 `run_stride_analysis`

### Purpose

Generate a deterministic STRIDE threat-mapping starter set from architecture components and data flows.

This tool does not replace a security review. It provides a structured baseline for the WAF Reviewer and Security Architect persona.

### Used by

- WAF Reviewer
- HLD Designer, optionally
- Options Generator, optionally
- Re-reasoning pipeline

### Inputs

```python
class ArchitectureComponentInput(BaseModel):
    component_id: str
    name: str
    component_type: str
    trust_zone: str | None = None
    handles_sensitive_data: bool = False
    internet_facing: bool = False
    identities_used: list[str] = []

class DataFlowInput(BaseModel):
    flow_id: str
    source_component_id: str
    target_component_id: str
    protocol: str | None = None
    data_classification: Literal["public", "internal", "confidential", "restricted"] = "internal"
    crosses_trust_boundary: bool = False

class STRIDEAnalysisInput(BaseModel):
    context: ToolCallContext
    components: list[ArchitectureComponentInput]
    data_flows: list[DataFlowInput]
```

### Outputs

```python
class STRIDEThreatOutput(BaseModel):
    threat_id: str
    component_id: str | None = None
    flow_id: str | None = None
    stride_category: Literal[
        "spoofing",
        "tampering",
        "repudiation",
        "information_disclosure",
        "denial_of_service",
        "elevation_of_privilege"
    ]
    threat: str
    mitigation: str
    severity: Literal["low", "medium", "high", "critical"]
    evidence_ids: list[str] = []

class STRIDEAnalysisOutput(BaseModel):
    threats: list[STRIDEThreatOutput]
    summary: dict[str, Any]
    warnings: list[str] = []
```

### Behavior

1. For each internet-facing component, map spoofing/DoS/information disclosure threats.
2. For each trust-boundary-crossing data flow, map tampering/information disclosure threats.
3. For sensitive-data components, add encryption, key management, and access-control mitigations.
4. For service-to-service flows, add managed identity/AuthN/AuthZ checks.
5. Return a baseline threat list with severity.

### Constraints

- This is a starter threat model.
- The WAF Reviewer and Security Architect must still reason over the findings.
- The tool should not invent compliance mappings.

---

## 13. Quality Gate Tools

## 13.1 `evaluate_quality_gate`

### Purpose

Evaluate whether a stage output meets its required quality gate.

### Used by

- All specialist routines
- Orchestrator
- Evidence Auditor
- Re-reasoning pipeline

### Inputs

```python
class QualityGateCheckInput(BaseModel):
    context: ToolCallContext
    stage: Literal[
        "intake",
        "requirements",
        "pattern_detection",
        "options",
        "socratic_review",
        "evidence_audit_checkpoint",
        "adr",
        "hld",
        "waf_review",
        "final_evidence_audit"
    ]
    checklist_results: dict[str, bool]
    warnings_context: dict[str, Any] = {}
```

### Outputs

```python
class QualityGateCheckOutput(BaseModel):
    status: Literal["passed", "passed_with_warnings", "failed"]
    blocking_failures: list[str] = []
    warnings: list[str] = []
    user_override_allowed: bool
    checklist_results: dict[str, bool]
```

### Behavior

1. Load static gate definition for the stage.
2. Evaluate blocking checks.
3. Evaluate warning checks.
4. Return a `QualityGateResult` compatible output.

### Example gate semantics

| Status | Meaning | Pipeline behavior |
|---|---|---|
| `passed` | All blocking and warning checks pass | Auto-advance allowed |
| `passed_with_warnings` | Blocking checks pass, warnings present | User can proceed; warnings shown |
| `failed` | One or more blocking checks failed | Auto-advance blocked |

### Constraints

- Quality gate evaluation is deterministic.
- Agents may propose checklist values, but the tool calculates status.
- Blocking failures cannot be silently overridden.

---

## 13.2 `validate_stage_patch`

### Purpose

Validate that an agent-produced `StagePatch` is well-formed before it is sent to the Architecture State Manager.

### Used by

- Orchestrator
- Internal pipeline controller

### Inputs

```python
class StagePatchValidationInput(BaseModel):
    context: ToolCallContext
    patch: dict[str, Any]
    expected_stage: str
    expected_base_version: int | None = None
```

### Outputs

```python
class StagePatchValidationOutput(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    normalized_patch: dict[str, Any] | None = None
```

### Behavior

1. Validate against Pydantic `StagePatch` model.
2. Check required metadata:
   - `session_id`
   - `stage`
   - `stage_run_id`
   - `base_version`
   - `target_version`
   - `idempotency_key`
   - `patch_hash`
3. Check stage matches expected stage or re-reasoning target.
4. Check `ClaimRecord` and `EvidenceSource` separation.
5. Check evidence IDs referenced by facts exist in `evidence_sources` or store.
6. Return normalized patch if valid.

### Constraints

- This tool does not persist the patch.
- This tool should be called before `apply_stage_patch`.

---

## 14. Dependency and Re-reasoning Tools

## 14.1 `compute_change_impact`

### Purpose

Given a requirement change, determine which stages/artifacts must be regenerated and which can remain stable.

### Used by

- Orchestrator
- Re-reasoning pipeline

### Inputs

```python
class RequirementChangeInput(BaseModel):
    requirement_id: str
    field_path: str
    old_value: Any
    new_value: Any
    category: Literal[
        "scale",
        "performance",
        "availability",
        "security",
        "compliance",
        "data_residency",
        "budget",
        "timeline",
        "region",
        "functional_scope",
        "integration",
        "unknown"
    ]
    change_reason: str | None = None

class ChangeImpactInput(BaseModel):
    context: ToolCallContext
    change: RequirementChangeInput
    dependency_map: dict[str, Any]
    current_stage_versions: dict[str, int]
```

### Outputs

```python
class ChangeImpactOutput(BaseModel):
    impacted_stages: list[str]
    stable_stages: list[str]
    recommended_rerun_order: list[str]
    requires_user_confirmation: bool = True
    rationale: list[str] = []
    warnings: list[str] = []
```

### Behavior

1. Classify change category.
2. Apply dependency rules.
3. Merge with session-specific dependency map.
4. Determine stable stages.
5. Determine safe re-run order.
6. Return rationale for UI display.

### Example

```json
{
  "change": {
    "requirement_id": "NFR-001",
    "field_path": "requirements.non_functional.scale.target_tps",
    "old_value": "10000",
    "new_value": "100000",
    "category": "scale"
  }
}
```

Example output:

```json
{
  "impacted_stages": [
    "options",
    "socratic_review",
    "adr",
    "hld",
    "waf_review",
    "final_evidence_audit"
  ],
  "stable_stages": [
    "intake",
    "requirements.functional",
    "compliance_framework_selection"
  ],
  "recommended_rerun_order": [
    "options",
    "socratic_review",
    "evidence_audit_checkpoint",
    "adr",
    "hld",
    "waf_review",
    "final_evidence_audit"
  ],
  "requires_user_confirmation": true
}
```

---

## 14.2 `generate_artifact_diff`

### Purpose

Generate human-readable and machine-readable diffs between artifact versions.

### Used by

- Re-reasoning pipeline
- Orchestrator
- Frontend diff view

### Inputs

```python
class ArtifactDiffInput(BaseModel):
    context: ToolCallContext
    session_id: str
    stage: str
    before_version: int
    after_version: int
    diff_mode: Literal["summary", "structured", "full"] = "structured"
```

### Outputs

```python
class ArtifactDiffOutput(BaseModel):
    session_id: str
    stage: str
    before_version: int
    after_version: int
    summary: str
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []
    unchanged: list[str] = []
    warnings: list[str] = []
```

### Behavior

Stage-specific diff behavior:

| Stage | Diff focus |
|---|---|
| `requirements` | changed NFRs, assumptions, open questions |
| `pattern_detection` | primary/secondary pattern changes |
| `options` | added/removed/modified architecture options |
| `socratic_review` | new risks, changed confidence, changed recommendation |
| `adr` | changed decision, supersession, changed rationale |
| `hld` | changed diagrams, added/removed components, trust-boundary changes |
| `waf_review` | new/changed findings by pillar |
| `evidence_audit` | unsupported/stale/contradictory claim changes |

### Constraints

- The tool reads artifacts through repository services.
- It does not regenerate artifacts.
- It must include version numbers and change trigger metadata.

---

## 15. Evidence and Claim Tools

## 15.1 `normalize_claims_and_evidence`

### Purpose

Normalize raw agent output into separate `ClaimRecord` and `EvidenceSource` lists.

### Used by

- All specialist routines through orchestrator post-processing
- Evidence Auditor

### Inputs

```python
class ClaimsEvidenceNormalizeInput(BaseModel):
    context: ToolCallContext
    raw_claims: list[dict[str, Any]]
    raw_evidence_sources: list[dict[str, Any]]
    stage: str
```

### Outputs

```python
class ClaimsEvidenceNormalizeOutput(BaseModel):
    claims: list[ClaimRecord]
    evidence_sources: list[EvidenceSource]
    warnings: list[str] = []
    errors: list[str] = []
```

### Behavior

1. Ensure every claim has a type: `fact`, `assumption`, or `recommendation`.
2. Ensure every fact has at least one evidence source unless intentionally flagged.
3. Ensure recommendations are linked to supporting evidence where applicable.
4. Ensure assumptions are flagged for user validation when material.
5. Deduplicate evidence sources by source URL + excerpt hash.
6. Return normalized records.

---

## 15.2 `classify_source_trust`

### Purpose

Classify evidence source trust level based on domain, source type, and source metadata.

### Inputs

```python
class SourceTrustInput(BaseModel):
    source: str
    source_url: str | None = None
    source_category: str | None = None
    retrieved_via: Literal["foundry_iq", "web_search", "function_tool"]
```

### Outputs

```python
class SourceTrustOutput(BaseModel):
    trust_level: Literal["high", "medium", "low"]
    reason: str
    warnings: list[str] = []
```

### Trust rules

| Source | Trust level |
|---|---|
| Microsoft Learn official docs | High |
| Azure Architecture Center | High |
| Azure Well-Architected Framework docs | High |
| Azure service SLA/limits/pricing docs | High |
| Microsoft Tech Community / DevBlogs | Medium to high, depending on topic |
| Third-party blogs | Medium or low |
| Forums / social posts | Low |
| Unknown source | Low |

---

## 15.3 `classify_source_freshness`

### Purpose

Classify source freshness for evidence records.

### Inputs

```python
class SourceFreshnessInput(BaseModel):
    source_url: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime
    claim_category: Literal[
        "pricing",
        "service_limit",
        "feature_availability",
        "architecture_pattern",
        "waf_guidance",
        "security_baseline",
        "general"
    ]
```

### Outputs

```python
class SourceFreshnessOutput(BaseModel):
    source_freshness: Literal["current", "recent", "stale", "unknown"]
    reason: str
    warnings: list[str] = []
```

### Freshness rules

| Claim category | Current | Recent | Stale |
|---|---:|---:|---:|
| Pricing | <= 30 days | <= 90 days | > 90 days |
| Service limits | <= 90 days | <= 180 days | > 180 days |
| Feature availability | <= 90 days | <= 180 days | > 180 days |
| WAF guidance | <= 12 months | <= 24 months | > 24 months |
| Architecture patterns | <= 24 months | <= 48 months | > 48 months |
| Security baseline | <= 12 months | <= 24 months | > 24 months |

---

## 15.4 `detect_evidence_contradictions`

### Purpose

Detect possible contradictions across evidence sources and claims.

### Inputs

```python
class EvidenceContradictionInput(BaseModel):
    context: ToolCallContext
    claims: list[ClaimRecord]
    evidence_sources: list[EvidenceSource]
```

### Outputs

```python
class EvidenceContradictionOutput(BaseModel):
    contradictions: list[dict[str, Any]]
    warnings: list[str] = []
```

### Behavior

MVP implementation:

- Detect exact or obvious numeric conflicts for the same service/attribute.
- Detect conflicting status claims such as `preview` vs `GA`.
- Detect conflicting recommendation rationales only as warnings, not hard failures.

Post-MVP implementation:

- Use an LLM-based contradiction review step, constrained to retrieved evidence only.

---

## 16. Pattern and Requirements Utility Tools

## 16.1 `detect_pattern_signals`

### Purpose

Perform deterministic keyword/signal detection before the Pattern Detector agent confirms the architecture pattern.

### Used by

- Pattern Detector
- Orchestrator

### Inputs

```python
class PatternSignalInput(BaseModel):
    context: ToolCallContext
    business_need: str
    requirements_summary: str | None = None
```

### Outputs

```python
class PatternSignalOutput(BaseModel):
    candidate_patterns: list[dict[str, Any]]
    matched_signals: list[str]
    warnings: list[str] = []
```

### Behavior

- Match configured signal words against known architecture patterns.
- Return candidate patterns with confidence-like scores.
- Do not make final pattern recommendation.
- Feed output to Pattern Detector routine.

---

## 16.2 `extract_requirement_change`

### Purpose

Extract structured change candidates from a user message during an existing architecture session.

### Used by

- Orchestrator
- Re-reasoning pipeline

### Inputs

```python
class RequirementChangeExtractionInput(BaseModel):
    context: ToolCallContext
    user_message: str
    current_requirements: dict[str, Any]
```

### Outputs

```python
class RequirementChangeExtractionOutput(BaseModel):
    changes_detected: bool
    changes: list[RequirementChangeInput]
    confidence: float
    requires_user_confirmation: bool
```

### Behavior

- Detect changes such as scale, region, availability, compliance, budget, or timeline.
- Link changes to existing requirement IDs where possible.
- If uncertain, return `requires_user_confirmation=true`.

---

## 17. State and Persistence Service Operations

These operations are internal services, not agent-callable tools.

## 17.1 `load_architecture_session`

### Purpose

Load the current `ArchitectureSession` summary for orchestration.

### Inputs

```python
class LoadSessionInput(BaseModel):
    session_id: str
```

### Outputs

```python
class LoadSessionOutput(BaseModel):
    session: ArchitectureSession
    etag: str | None = None
```

---

## 17.2 `load_stage_artifacts`

### Purpose

Load one or more `VersionedArtifact` records for context packaging, diffing, or re-reasoning.

### Inputs

```python
class LoadArtifactsInput(BaseModel):
    session_id: str
    stages: list[str] | None = None
    version: int | Literal["latest"] = "latest"
```

### Outputs

```python
class LoadArtifactsOutput(BaseModel):
    artifacts: list[VersionedArtifact]
```

---

## 17.3 `apply_stage_patch`

### Purpose

Persist a validated `StagePatch` using the Architecture State Manager.

### Inputs

```python
class ApplyStagePatchInput(BaseModel):
    patch: StagePatch
    expected_session_etag: str | None = None
```

### Outputs

```python
class ApplyStagePatchOutput(BaseModel):
    applied: bool
    reason: str | None = None
    stage: str | None = None
    version: int | None = None
    current_version: int | None = None
    action: str | None = None
```

### Behavior

1. Check idempotency key.
2. Check base version.
3. Check quality gate blocking failures.
4. Upsert `VersionedArtifact`.
5. Append `ClaimRecord` records.
6. Append `EvidenceSource` records.
7. Update `ArchitectureSession`.
8. Append `ChangeEvent` if applicable.

### Constraints

- This is not exposed directly to agents.
- All writes must be traceable.
- Version conflict returns a structured failure, not an overwrite.

---

## 17.4 `persist_tool_trace`

### Purpose

Persist tool execution metadata for observability.

### Inputs

```python
class PersistToolTraceInput(BaseModel):
    trace_event: ToolTraceEvent
```

### Outputs

```python
class PersistToolTraceOutput(BaseModel):
    persisted: bool
```

---

## 18. Tool Registration

### 18.1 App-local tools

App-local tools should be registered with the agent framework using explicit names and docstrings.

Example conceptual registration:

```python
TOOLS = [
    retrieve_from_foundry_iq,
    search_web_for_current_info,
    mermaid_render_check,
    estimate_azure_cost,
    format_adr,
    run_stride_analysis,
    evaluate_quality_gate,
    compute_change_impact,
    generate_artifact_diff,
]
```

### 18.2 Tool naming conventions

Use verb-first names:

- `retrieve_from_foundry_iq`
- `search_web_for_current_info`
- `check_mermaid_renderability`
- `estimate_azure_cost`
- `format_adr`
- `run_stride_analysis`
- `evaluate_quality_gate`
- `compute_change_impact`
- `generate_artifact_diff`

Avoid ambiguous names:

- `do_search`
- `validate`
- `generate`
- `analyze`
- `process`

### 18.3 Approval mode

MVP app-local tools should be non-destructive and may be registered with no approval required.

However, workflow-level confirmation is still required for:

- Applying requirement changes.
- Accepting regenerated artifact versions.
- Superseding ADRs.
- Proceeding past quality-gate warnings.

---

## 19. Tool Error Handling and Retries

### 19.1 Retry policy

| Tool type | Retry policy |
|---|---|
| Foundry IQ retrieval | Retry up to 2 times with exponential backoff |
| Web Search | Retry once; if unavailable, proceed with warning if not critical |
| Mermaid render check | No retry unless auto-fix is enabled |
| Cost estimator | No retry; missing catalog data is deterministic |
| STRIDE analysis | No retry |
| Quality gate evaluation | No retry |
| Patch validation | No retry |
| State Manager apply | Retry only on transient Cosmos errors, not version conflicts |

### 19.2 Partial success

Tools may return `partial_success` when useful output exists but with warnings.

Examples:

- Foundry IQ returns results but all are stale.
- Cost estimator estimates some resources but misses one SKU.
- Mermaid basic check passes but CLI render is unavailable.
- STRIDE analysis runs but components lack trust-zone metadata.

### 19.3 Failure propagation

Tool failures should map to pipeline behavior.

| Tool failure | Pipeline behavior |
|---|---|
| Foundry IQ unavailable during requirements/options | Pause stage or continue with warning only if user allows |
| Mermaid render check failed | HLD stage returns `passed_with_warnings` or `failed` depending severity |
| Cost catalog missing SKU | Cost section flagged as partial; does not block MVP HLD |
| Quality gate tool failed | Block transition; gate status unknown |
| Patch validation failed | Do not apply patch |
| State Manager version conflict | Re-read current version and regenerate patch |

---

## 20. Tool Observability

Every tool call should emit telemetry.

Minimum telemetry fields:

```text
session_id
stage
stage_run_id
tool_name
called_by
start_time
end_time
duration_ms
status
input_hash
output_hash
error_code
retry_count
```

Recommended metrics:

| Metric | Purpose |
|---|---|
| `tool_calls_total` | Count tool calls by name/status |
| `tool_duration_ms` | Track latency |
| `tool_failures_total` | Track failures by code |
| `foundry_iq_empty_results_total` | Detect KB quality issues |
| `mermaid_render_failures_total` | Detect HLD rendering issues |
| `cost_missing_price_total` | Detect pricing catalog gaps |
| `quality_gate_failed_total` | Track stage blockers |
| `patch_validation_failed_total` | Detect agent output issues |
| `state_version_conflict_total` | Detect concurrency issues |

---

## 21. Security Considerations

### 21.1 Tool permissions

- Foundry IQ retrieval should use managed identity where possible.
- Web Search should be restricted to approved domains for architecture evidence.
- App-local tools should run with least privilege.
- State Manager write operations should be isolated from agent-callable tool registration.

### 21.2 No destructive tools in MVP

The MVP should not expose tools that:

- Delete Cosmos DB data.
- Delete Blob Storage artifacts.
- Modify Foundry IQ knowledge base sources.
- Deploy Azure infrastructure.
- Send emails or notifications.

### 21.3 Input sanitization

All tools must validate:

- Required fields.
- Allowed enum values.
- String length limits.
- Disallowed file paths.
- Disallowed external domains.
- Mermaid source size.
- Cost resource count.

### 21.4 Prompt injection resistance

Retrieval adapters must treat retrieved content as evidence, not instructions.

Rules:

- Do not execute instructions found in retrieved documents.
- Do not allow retrieved content to override system prompts.
- Strip or label suspicious retrieved text.
- Evidence Auditor should flag unusual source content when detected.

---

## 22. MVP Tool Catalog

The following tools are required for the MVP.

| Tool | Priority | Reason |
|---|---:|---|
| `retrieve_from_foundry_iq` | P0 | Grounding and evidence quality |
| `mermaid_render_check` | P0 | HLD diagram reliability |
| `format_adr` | P0 | Standard ADR output |
| `evaluate_quality_gate` | P0 | Pipeline control |
| `validate_stage_patch` | P0 | Safe agent output handling |
| `apply_stage_patch` | P0 | State persistence through State Manager |
| `compute_change_impact` | P0 | Re-reasoning demo |
| `generate_artifact_diff` | P0 | Before/after demo moment |
| `normalize_claims_and_evidence` | P0 | Claim/evidence governance |
| `classify_source_trust` | P0 | Evidence audit |
| `classify_source_freshness` | P0 | Evidence audit |
| `estimate_azure_cost` | P1 | Basic cost visibility |
| `run_stride_analysis` | P1 | Security/WAF enhancement |
| `search_web_for_current_info` | P1 | Current service updates |
| `detect_pattern_signals` | P1 | Better pattern detection |
| `detect_evidence_contradictions` | P1 | Stronger audit quality |

---

## 23. Post-MVP Tool Candidates

| Tool | Purpose |
|---|---|
| `generate_implementation_backlog` | Convert artifacts into epics/features/stories |
| `map_compliance_controls` | Map architecture to PCI-DSS, ISO 27001, SOC 2, HIPAA |
| `render_mermaid_to_svg` | Produce downloadable diagram images |
| `export_artifact_bundle` | Generate ZIP/Markdown/PDF architecture pack |
| `validate_openapi_contract` | Validate generated API contracts |
| `estimate_carbon_impact` | Sustainability review |
| `compare_cloud_service_options` | Multi-cloud extension |
| `simulate_scale_sensitivity` | Cost/performance sensitivity analysis |
| `run_architecture_lint` | Check common architecture anti-patterns |
| `generate_c4_model` | Generate C4 context/container/component diagrams |

---

## 24. Tool Test Strategy

### 24.1 Unit tests

Each deterministic tool should have unit tests for:

- Valid input.
- Missing required fields.
- Invalid enum values.
- Empty input.
- Partial success conditions.
- Failure conditions.
- Boundary values.

### 24.2 Golden test cases

Maintain golden inputs/outputs for:

- Fraud detection scenario at 10K TPS.
- Fraud detection scenario after 100K TPS change.
- Mermaid diagram render check.
- ADR formatting.
- Cost estimation with missing SKU.
- STRIDE analysis for internet-facing API.
- Evidence trust/freshness classification.
- Change impact from scale/performance change.

### 24.3 Integration tests

Integration tests should verify:

1. Foundry IQ retrieval returns normalized `EvidenceSource` records.
2. Agent output can be normalized into `ClaimRecord` and `EvidenceSource` records.
3. Quality gate outputs map to stage transition behavior.
4. Invalid StagePatch is rejected.
5. Valid StagePatch is applied once only.
6. Duplicate idempotency key does not create a duplicate artifact.
7. Version conflict returns structured error.
8. Re-reasoning produces a new artifact version and diff.

---

## 25. Implementation Checklist

### 25.1 P0 checklist

- [ ] Create `src/archimedes/tools/base.py`.
- [ ] Define `ToolCallContext`, `ToolResult`, `ToolError`, and `ToolTraceEvent`.
- [ ] Implement `retrieve_from_foundry_iq` adapter.
- [ ] Implement `mermaid_render_check` in basic mode.
- [ ] Implement `format_adr`.
- [ ] Implement `evaluate_quality_gate`.
- [ ] Implement `validate_stage_patch`.
- [ ] Implement State Manager `apply_stage_patch` operation.
- [ ] Implement `compute_change_impact`.
- [ ] Implement `generate_artifact_diff` for options/HLD/ADR.
- [ ] Implement `normalize_claims_and_evidence`.
- [ ] Implement `classify_source_trust`.
- [ ] Implement `classify_source_freshness`.
- [ ] Add tool telemetry wrapper.
- [ ] Add unit tests for each P0 tool.

### 25.2 P1 checklist

- [ ] Implement `estimate_azure_cost` with local pricing catalog.
- [ ] Implement `run_stride_analysis`.
- [ ] Implement `search_web_for_current_info`.
- [ ] Implement `detect_pattern_signals`.
- [ ] Implement `detect_evidence_contradictions`.
- [ ] Add integration tests for tool usage inside stage pipeline.

### 25.3 P2 checklist

- [ ] Add Mermaid CLI/browser render mode.
- [ ] Add Blob Storage rendered artifact outputs.
- [ ] Add advanced cost sensitivity analysis.
- [ ] Add compliance control mapping.
- [ ] Add artifact bundle export.

---

## 26. Acceptance Criteria

`09-tool-specifications.md` is considered implemented when:

1. All P0 tools are implemented with typed input/output models.
2. Agents can access only their permitted tools.
3. Foundry IQ retrieval results are normalized into `EvidenceSource` records.
4. Quality gate evaluation produces `passed`, `passed_with_warnings`, or `failed`.
5. StagePatch validation catches malformed patches before persistence.
6. State Manager applies valid patches once and rejects duplicate idempotency keys.
7. Version conflicts are detected and returned as structured errors.
8. Mermaid HLD output is checked before display.
9. Re-reasoning produces a structured impact plan and artifact diff.
10. Tool telemetry is emitted for every tool call.
11. Unit tests exist for all P0 tools.
12. The fraud detection demo can run using the tool layer without manual intervention except workflow-level user confirmation.

---

## 27. Summary

The Archimedes tool layer keeps the system reliable and auditable.

The most important MVP tools are:

- Foundry IQ retrieval adapter.
- Mermaid render check.
- ADR formatter.
- Quality gate evaluator.
- StagePatch validator.
- Architecture State Manager patch application.
- Change impact engine.
- Artifact diff generator.
- Claim/evidence normalizer.
- Source trust and freshness classifiers.

These tools ensure that Archimedes behaves like an architecture workbench rather than a free-form chatbot. The agents produce reasoning and structured outputs; tools enforce consistency, traceability, and safe progression through the architecture lifecycle.

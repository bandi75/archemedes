# Archimedes API Contracts

**Document ID:** `05-api-contracts.md`  
**Solution:** Archimedes — AI Architecture Workbench  
**Version:** v2.2  
**Status:** Implementation-ready baseline  
**Last updated:** 2026-06-09  
**Related documents:** `01-archimedes-hld.md`, `02-domain-models.md`, `03-pydantic-schemas.md`, `04-database-design.md`, `06-stage-pipeline.md`, `07-agent-specifications.md`, `08-socrates-engine.md`, `09-tool-specifications.md`, `10-foundry-iq-knowledge-base.md`, `11-evidence-and-claims.md`, `12-dependency-and-rereasoning.md`

---

## 1. Purpose

This document defines the external and internal API contracts for Archimedes.

Archimedes is implemented as a FastAPI backend that exposes session, pipeline, artifact, evidence, Socrates, re-reasoning, and frontend-support APIs. The APIs sit above the orchestrator, agent routines, Socrates workflow, Architecture State Manager, Cosmos DB repositories, Blob Storage, and Foundry IQ retrieval layer.

The API layer is responsible for:

- Creating and managing architecture sessions.
- Driving the 11-stage architecture pipeline.
- Exposing stage execution status to the frontend.
- Returning versioned artifacts such as requirements, options, ADRs, HLDs, WAF reviews, Socrates outputs, and evidence audit reports.
- Accepting requirement changes and triggering selective re-reasoning.
- Returning before/after diffs between artifact versions.
- Exposing claims, evidence, and audit status.
- Supporting frontend timeline, debate view, artifact viewer, Mermaid rendering view, and diff view.

This document does **not** define the full Pydantic implementation. See `03-pydantic-schemas.md` for concrete model definitions.

---

## 2. API Design Principles

1. **Session-centric API**  
   Most resources are scoped under an `architecture_session` identified by `session_id`.

2. **Asynchronous stage execution**  
   Long-running stage operations return a `stage_run_id` and update status asynchronously.

3. **Validated state changes only**  
   No API writes agent output directly to the database. Stage output must become a validated `StagePatch`, then flow through the Architecture State Manager.

4. **Idempotency-first mutations**  
   Mutating APIs accept an `Idempotency-Key` header or generate a deterministic idempotency key when a stage execution is created.

5. **Versioned artifacts**  
   Meaningful outputs are retrieved by `stage`, `version`, or `latest`.

6. **Clear quality gate semantics**  
   API responses distinguish `passed`, `passed_with_warnings`, and `failed`.

7. **Evidence transparency**  
   Claims and evidence are exposed as first-class API resources.

8. **Selective re-reasoning**  
   Requirement changes are handled through an impact plan before selective re-run.

9. **Frontend-friendly status APIs**  
   The UI should not reconstruct pipeline state by querying many raw collections. It should use dedicated timeline, status, and artifact APIs.

10. **Internal tools are not public APIs by default**  
    Tools such as Mermaid render check, quality gate evaluation, STRIDE mapping, cost estimation, and diff generation are called by the orchestrator. They are not public endpoints unless explicitly exposed for debugging.

---

## 3. API Base URL and Versioning

### 3.1 Base URL

For local development:

```text
http://localhost:8000/api/v1
```

For Azure deployment:

```text
https://<archimedes-api-host>/api/v1
```

### 3.2 Versioning Strategy

API versioning is path-based for MVP:

```text
/api/v1/...
```

Breaking changes should be introduced under `/api/v2`. Non-breaking changes may add optional fields to response DTOs.

### 3.3 OpenAPI

FastAPI automatically exposes:

```text
GET /openapi.json
GET /docs
GET /redoc
```

For production, `/docs` and `/redoc` should be protected or disabled.

---

## 4. Authentication and Authorization

### 4.1 MVP Mode

For MVP/demo:

- Authentication may be disabled locally.
- A static demo API key may be used when deployed.
- Session IDs are treated as unguessable UUID-style identifiers.

### 4.2 Production Direction

Production should use:

- Microsoft Entra ID for user authentication.
- Managed Identity for Azure service access.
- Role-based access control at session level.
- Audit logging for all mutating operations.

### 4.3 Headers

| Header | Required | Purpose |
|---|---:|---|
| `Authorization: Bearer <token>` | Production | User authentication |
| `X-Request-Id` | Optional | Client-provided trace ID |
| `Idempotency-Key` | Recommended for mutations | Prevent duplicate writes/executions |
| `Accept: application/json` | Yes | JSON responses |
| `Content-Type: application/json` | For request bodies | JSON request payloads |

---

## 5. Common API Conventions

### 5.1 Resource Identifiers

| Resource | ID format example |
|---|---|
| Session | `sess_01jxyzabc123` |
| Stage run | `run_req_01jxyzabc123` |
| Artifact | `art_hld_01jxyzabc123` |
| Claim | `claim_01jxyzabc123` |
| Evidence | `ev_01jxyzabc123` |
| Change event | `chg_01jxyzabc123` |
| Diff | `diff_01jxyzabc123` |

Implementation may use UUID/ULID internally. Prefixes are recommended for readability.

### 5.2 Timestamp Format

All timestamps use ISO 8601 with timezone.

```json
"2026-06-09T12:45:00Z"
```

### 5.3 Response Envelope

Most responses use a consistent envelope.

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-06-09T12:45:00Z"
  }
}
```

For streaming endpoints, the envelope is replaced by event payloads.

### 5.4 Error Envelope

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "quality_gate_failed",
    "message": "Requirements stage failed blocking quality checks.",
    "details": {
      "blocking_failures": [
        "Scale target must be defined",
        "Security requirements must be identified"
      ]
    }
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-06-09T12:45:00Z"
  }
}
```

### 5.5 Pagination

Collection endpoints use cursor pagination.

Request:

```text
GET /api/v1/sessions?limit=20&cursor=<cursor>
```

Response:

```json
{
  "items": [],
  "next_cursor": "cursor_abc",
  "has_more": true
}
```

### 5.6 Idempotency

All mutating operations should support `Idempotency-Key`.

If an idempotency key was already processed successfully, the API returns the original outcome.

```http
Idempotency-Key: sess_123-stage_requirements-run_456
```

---

## 6. Core Status Enums

### 6.1 Stage Status

```text
pending | running | completed | failed | skipped
```

### 6.2 Quality Gate Status

```text
passed | passed_with_warnings | failed
```

### 6.3 Stage IDs

```text
intake
requirements
pattern_detection
options
socratic_review
evidence_audit_checkpoint
adr
hld
waf_review
final_evidence_audit
rereasoning
```

### 6.4 Artifact Types

```text
intake_summary
requirements_spec
pattern_analysis
options_matrix
socratic_review
adr
hld
waf_review
evidence_audit_report
cost_estimate
security_review
change_impact_plan
artifact_diff
```

---

## 7. API Surface Overview

| Group | Purpose |
|---|---|
| `/sessions` | Create, retrieve, list, and update architecture sessions |
| `/sessions/{session_id}/pipeline` | Run stages, inspect pipeline timeline, pause/resume/retry |
| `/sessions/{session_id}/stages` | Stage status and stage-run details |
| `/sessions/{session_id}/artifacts` | Retrieve versioned stage artifacts |
| `/sessions/{session_id}/claims` | Retrieve and filter claims |
| `/sessions/{session_id}/evidence` | Retrieve evidence sources |
| `/sessions/{session_id}/audits` | Trigger and retrieve evidence audits |
| `/sessions/{session_id}/socrates` | Run/retrieve Socrates debate outputs |
| `/sessions/{session_id}/changes` | Submit requirement changes and compute impact |
| `/sessions/{session_id}/diffs` | Retrieve artifact diffs |
| `/health` | Health and readiness |
| `/admin` | Optional dev/admin endpoints |

---

## 8. Session APIs

### 8.1 Create Architecture Session

```http
POST /api/v1/sessions
```

Creates a new architecture session from a raw business need.

#### Request

```json
{
  "business_need": "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.",
  "title": "Fintech real-time fraud detection",
  "domain": "fintech",
  "created_by": "demo-user",
  "metadata": {
    "demo_scenario": true,
    "preferred_cloud": "azure"
  }
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "title": "Fintech real-time fraud detection",
  "business_need": "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.",
  "current_stage": "intake",
  "active_version": 1,
  "stage_executions": {},
  "created_at": "2026-06-09T12:45:00Z",
  "updated_at": "2026-06-09T12:45:00Z"
}
```

#### Behavior

- Creates an `ArchitectureSession` record.
- Initializes pipeline status.
- Does not automatically run the full pipeline unless `auto_start=true` is passed.

---

### 8.2 Create and Auto-Start Session

```http
POST /api/v1/sessions?auto_start=true
```

Same request body as session creation, but automatically triggers the intake stage.

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "current_stage": "intake",
  "stage_run_id": "run_intake_01jxyzabc123",
  "stage_status": "running",
  "message": "Session created and intake stage started."
}
```

---

### 8.3 Get Session

```http
GET /api/v1/sessions/{session_id}
```

Returns the current session summary.

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "title": "Fintech real-time fraud detection",
  "business_need": "...",
  "current_stage": "options",
  "last_successful_stage": "pattern_detection",
  "active_version": 1,
  "detected_patterns": ["real_time_streaming"],
  "quality_gates": {
    "requirements": {
      "status": "passed_with_warnings",
      "blocking_failures": [],
      "warnings": ["Data residency requirements not checked"],
      "user_override_allowed": true
    }
  },
  "created_at": "2026-06-09T12:45:00Z",
  "updated_at": "2026-06-09T13:10:00Z"
}
```

---

### 8.4 List Sessions

```http
GET /api/v1/sessions?limit=20&cursor=<cursor>&status=active
```

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `limit` | integer | No | Default `20`, max `100` |
| `cursor` | string | No | Pagination cursor |
| `status` | string | No | `active`, `completed`, `failed`, `archived` |
| `created_by` | string | No | Filter by creator |

#### Response

```json
{
  "items": [
    {
      "session_id": "sess_01jxyzabc123",
      "title": "Fintech real-time fraud detection",
      "current_stage": "hld",
      "last_successful_stage": "adr",
      "active_version": 1,
      "updated_at": "2026-06-09T13:10:00Z"
    }
  ],
  "next_cursor": null,
  "has_more": false
}
```

---

### 8.5 Update Session Metadata

```http
PATCH /api/v1/sessions/{session_id}
```

Updates non-pipeline session metadata only.

#### Request

```json
{
  "title": "Fraud detection architecture v1",
  "metadata": {
    "owner": "architecture-team",
    "priority": "demo"
  }
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "title": "Fraud detection architecture v1",
  "updated_at": "2026-06-09T13:15:00Z"
}
```

---

## 9. Pipeline APIs

### 9.1 Get Pipeline Timeline

```http
GET /api/v1/sessions/{session_id}/pipeline
```

Returns frontend-ready pipeline state.

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "current_stage": "socratic_review",
  "last_successful_stage": "options",
  "stages": [
    {
      "stage": "intake",
      "label": "Intake",
      "status": "completed",
      "stage_run_id": "run_intake_001",
      "version": 1,
      "quality_gate": null,
      "started_at": "2026-06-09T12:45:00Z",
      "completed_at": "2026-06-09T12:46:00Z"
    },
    {
      "stage": "requirements",
      "label": "Requirements Extraction",
      "status": "completed",
      "stage_run_id": "run_req_001",
      "version": 1,
      "quality_gate": {
        "status": "passed_with_warnings",
        "blocking_failures": [],
        "warnings": ["Data residency requirements not checked"],
        "user_override_allowed": true
      }
    },
    {
      "stage": "socratic_review",
      "label": "Socratic Review",
      "status": "running",
      "stage_run_id": "run_soc_001",
      "version": null,
      "quality_gate": null
    }
  ]
}
```

---

### 9.2 Run Next Stage

```http
POST /api/v1/sessions/{session_id}/pipeline/run-next
```

Runs the next eligible stage based on current session state.

#### Request

```json
{
  "mode": "standard",
  "allow_warning_override": false,
  "context_overrides": {}
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage": "requirements",
  "stage_run_id": "run_req_01jxyzabc123",
  "status": "running",
  "message": "Requirements Extraction started."
}
```

#### Behavior

- Determines next stage from pipeline state.
- Creates a `StageExecution` record with `running` status.
- Invokes the orchestrator asynchronously.
- Returns immediately.

---

### 9.3 Run Specific Stage

```http
POST /api/v1/sessions/{session_id}/pipeline/stages/{stage_id}/run
```

Runs a specific stage when allowed by pipeline transition rules.

#### Request

```json
{
  "base_version": 1,
  "force": false,
  "reason": "Manual retry after fixing missing requirement",
  "allow_warning_override": true,
  "stage_options": {
    "socrates_depth": "standard"
  }
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage": "options",
  "stage_run_id": "run_options_01jxyzabc123",
  "base_version": 1,
  "target_version": 2,
  "status": "running"
}
```

#### Rules

- Cannot run a downstream stage if required upstream blocking gates failed.
- `force=true` is allowed only for admin/dev mode.
- Re-runs create new artifact versions.

---

### 9.4 Run Full Pipeline Until Stop

```http
POST /api/v1/sessions/{session_id}/pipeline/run
```

Runs the pipeline from current stage until completion, failure, or user input requirement.

#### Request

```json
{
  "stop_on_warning": false,
  "stop_on_user_input_required": true,
  "socrates_depth": "standard",
  "max_stages": 10
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "pipeline_run_id": "pipe_01jxyzabc123",
  "status": "running",
  "started_from_stage": "intake",
  "planned_stages": [
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
}
```

---

### 9.5 Pause Pipeline

```http
POST /api/v1/sessions/{session_id}/pipeline/pause
```

#### Request

```json
{
  "reason": "User wants to review options before Socrates review."
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "status": "paused",
  "current_stage": "options"
}
```

---

### 9.6 Resume Pipeline

```http
POST /api/v1/sessions/{session_id}/pipeline/resume
```

#### Request

```json
{
  "resume_from": "last_successful_stage",
  "stop_on_warning": false
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "status": "running",
  "resumed_from_stage": "options"
}
```

---

### 9.7 Retry Failed Stage

```http
POST /api/v1/sessions/{session_id}/pipeline/stages/{stage_id}/retry
```

#### Request

```json
{
  "reason": "Transient Foundry IQ retrieval failure",
  "use_same_inputs": true
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage": "hld",
  "stage_run_id": "run_hld_retry_001",
  "retry_count": 1,
  "status": "running"
}
```

---

### 9.8 Cancel Stage Run

```http
POST /api/v1/sessions/{session_id}/pipeline/stage-runs/{stage_run_id}/cancel
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage_run_id": "run_soc_001",
  "status": "cancel_requested"
}
```

#### Note

Cancellation is cooperative. If an LLM call is already in progress and cannot be cancelled immediately, the state manager should ignore late patches from cancelled runs.

---

## 10. Stage Run APIs

### 10.1 Get Stage Run

```http
GET /api/v1/sessions/{session_id}/stages/{stage_id}/runs/{stage_run_id}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage": "socratic_review",
  "stage_run_id": "run_soc_001",
  "status": "running",
  "started_at": "2026-06-09T13:00:00Z",
  "completed_at": null,
  "retry_count": 0,
  "failure_reason": null,
  "base_version": 1,
  "target_version": 1,
  "progress": {
    "message": "Running Security Architect and FinOps personas",
    "percent": 60
  }
}
```

---

### 10.2 List Stage Runs

```http
GET /api/v1/sessions/{session_id}/stages/{stage_id}/runs
```

#### Response

```json
{
  "items": [
    {
      "stage_run_id": "run_options_001",
      "stage": "options",
      "status": "completed",
      "base_version": 0,
      "target_version": 1,
      "started_at": "2026-06-09T12:50:00Z",
      "completed_at": "2026-06-09T12:52:00Z"
    }
  ]
}
```

---

## 11. Streaming APIs

The frontend needs live updates for stage progress, Socrates debate, and pipeline state. MVP can use Server-Sent Events. WebSocket may be added later.

### 11.1 Stream Session Events

```http
GET /api/v1/sessions/{session_id}/events
```

Content type:

```text
text/event-stream
```

#### Event: `stage_started`

```json
{
  "event_type": "stage_started",
  "session_id": "sess_01jxyzabc123",
  "stage": "socratic_review",
  "stage_run_id": "run_soc_001",
  "timestamp": "2026-06-09T13:00:00Z"
}
```

#### Event: `stage_progress`

```json
{
  "event_type": "stage_progress",
  "session_id": "sess_01jxyzabc123",
  "stage": "socratic_review",
  "stage_run_id": "run_soc_001",
  "message": "FinOps Lead analysis completed",
  "percent": 70,
  "timestamp": "2026-06-09T13:01:00Z"
}
```

#### Event: `stage_completed`

```json
{
  "event_type": "stage_completed",
  "session_id": "sess_01jxyzabc123",
  "stage": "socratic_review",
  "stage_run_id": "run_soc_001",
  "artifact_id": "art_soc_001",
  "version": 1,
  "quality_gate_status": "passed",
  "timestamp": "2026-06-09T13:02:00Z"
}
```

#### Event: `stage_failed`

```json
{
  "event_type": "stage_failed",
  "session_id": "sess_01jxyzabc123",
  "stage": "hld",
  "stage_run_id": "run_hld_001",
  "error_code": "mermaid_render_check_failed",
  "message": "Mermaid diagram could not be rendered after retries.",
  "timestamp": "2026-06-09T13:05:00Z"
}
```

#### Event: `socrates_persona_completed`

```json
{
  "event_type": "socrates_persona_completed",
  "session_id": "sess_01jxyzabc123",
  "stage_run_id": "run_soc_001",
  "persona": "Security Architect",
  "summary": "Identified key concerns around identity, PCI-DSS logging, and network isolation.",
  "timestamp": "2026-06-09T13:01:30Z"
}
```

---

## 12. Artifact APIs

### 12.1 List Artifacts

```http
GET /api/v1/sessions/{session_id}/artifacts?stage=hld&type=hld
```

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `stage` | string | No | Filter by stage |
| `type` | string | No | Filter by artifact type |
| `latest_only` | boolean | No | Return only latest version per stage/type |

#### Response

```json
{
  "items": [
    {
      "artifact_id": "art_hld_001",
      "session_id": "sess_01jxyzabc123",
      "stage": "hld",
      "artifact_type": "hld",
      "version": 1,
      "stage_run_id": "run_hld_001",
      "title": "High-Level Design",
      "quality_gate_status": "passed_with_warnings",
      "created_at": "2026-06-09T13:10:00Z"
    }
  ]
}
```

---

### 12.2 Get Latest Artifact for Stage

```http
GET /api/v1/sessions/{session_id}/artifacts/{stage_id}/latest
```

#### Response

```json
{
  "artifact_id": "art_hld_001",
  "session_id": "sess_01jxyzabc123",
  "stage": "hld",
  "artifact_type": "hld",
  "version": 1,
  "content": {
    "title": "High-Level Design",
    "diagrams": {
      "system_context": "flowchart TD\n...",
      "container": "flowchart TD\n..."
    },
    "narrative": "..."
  },
  "claims": ["claim_001", "claim_002"],
  "quality_gate": {
    "status": "passed_with_warnings",
    "blocking_failures": [],
    "warnings": ["Trust boundaries need manual review"],
    "user_override_allowed": true
  },
  "created_at": "2026-06-09T13:10:00Z"
}
```

---

### 12.3 Get Artifact by Version

```http
GET /api/v1/sessions/{session_id}/artifacts/{stage_id}/versions/{version}
```

#### Response

Same as latest artifact response, but returns the requested version.

---

### 12.4 Get Artifact Markdown

```http
GET /api/v1/sessions/{session_id}/artifacts/{stage_id}/versions/{version}/markdown
```

Returns a markdown rendering of the artifact.

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage": "adr",
  "version": 1,
  "markdown": "# ADR-001: Use Event Hubs and Stream Analytics\n\n..."
}
```

---

### 12.5 Export Artifact Bundle

```http
POST /api/v1/sessions/{session_id}/artifacts/export
```

Exports selected artifacts into a downloadable bundle.

#### Request

```json
{
  "format": "markdown_zip",
  "stages": ["requirements", "options", "socratic_review", "adr", "hld", "waf_review"],
  "include_claims": true,
  "include_evidence": true
}
```

#### Response

```json
{
  "export_id": "exp_01jxyzabc123",
  "status": "completed",
  "download_url": "https://<storage>/exports/sess_01jxyzabc123/archimedes-export.zip",
  "expires_at": "2026-06-10T13:10:00Z"
}
```

---

## 13. Claims and Evidence APIs

### 13.1 List Claims

```http
GET /api/v1/sessions/{session_id}/claims?stage=options&type=recommendation
```

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `stage` | string | No | Filter by stage |
| `type` | string | No | `fact`, `assumption`, `recommendation` |
| `requires_user_validation` | boolean | No | Filter unvalidated assumptions |
| `min_confidence` | number | No | Filter by confidence |

#### Response

```json
{
  "items": [
    {
      "claim_id": "claim_001",
      "claim": "Event Hubs is a viable ingestion option for high-throughput event streaming on Azure.",
      "type": "fact",
      "confidence": 0.87,
      "stage": "options",
      "evidence_ids": ["ev_001"],
      "requires_user_validation": false,
      "created_at": "2026-06-09T12:55:00Z"
    }
  ]
}
```

---

### 13.2 Get Claim

```http
GET /api/v1/sessions/{session_id}/claims/{claim_id}
```

#### Response

```json
{
  "claim_id": "claim_001",
  "claim": "Event Hubs is a viable ingestion option for high-throughput event streaming on Azure.",
  "type": "fact",
  "confidence": 0.87,
  "stage": "options",
  "evidence_ids": ["ev_001"],
  "evidence": [
    {
      "evidence_id": "ev_001",
      "source": "Azure Event Hubs documentation",
      "source_url": "https://learn.microsoft.com/...",
      "retrieved_via": "foundry_iq",
      "kb_name": "azure-architecture-kb",
      "kb_version": "2026-06-09",
      "trust_level": "high",
      "source_freshness": "current"
    }
  ]
}
```

---

### 13.3 List Evidence Sources

```http
GET /api/v1/sessions/{session_id}/evidence?retrieved_via=foundry_iq&trust_level=high
```

#### Response

```json
{
  "items": [
    {
      "evidence_id": "ev_001",
      "source": "Azure Event Hubs documentation",
      "source_url": "https://learn.microsoft.com/...",
      "retrieved_via": "foundry_iq",
      "retrieved_at": "2026-06-09T12:55:00Z",
      "kb_name": "azure-architecture-kb",
      "kb_version": "2026-06-09",
      "source_document_version": "2026-06-01",
      "source_freshness": "current",
      "trust_level": "high",
      "used_by_claims": ["claim_001"]
    }
  ]
}
```

---

### 13.4 Validate User Assumption

```http
POST /api/v1/sessions/{session_id}/claims/{claim_id}/validate
```

Marks an assumption as validated or rejected by the user.

#### Request

```json
{
  "validation_status": "validated",
  "validated_by": "demo-user",
  "comment": "The customer confirmed that the team has limited Kafka operational experience."
}
```

#### Response

```json
{
  "claim_id": "claim_010",
  "requires_user_validation": false,
  "validation_status": "validated",
  "updated_at": "2026-06-09T13:20:00Z"
}
```

---

## 14. Evidence Audit APIs

### 14.1 Trigger Evidence Audit

```http
POST /api/v1/sessions/{session_id}/audits/evidence
```

Runs an evidence audit for the current session or selected stages.

#### Request

```json
{
  "audit_type": "checkpoint",
  "stages": ["options", "socratic_review"],
  "strictness": "standard"
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage_run_id": "run_audit_001",
  "audit_type": "checkpoint",
  "status": "running"
}
```

---

### 14.2 Get Latest Evidence Audit

```http
GET /api/v1/sessions/{session_id}/audits/evidence/latest
```

#### Response

```json
{
  "audit_id": "audit_001",
  "session_id": "sess_01jxyzabc123",
  "audit_type": "checkpoint",
  "stages": ["options", "socratic_review"],
  "overall_evidence_quality": "adequate",
  "recommendation": "proceed",
  "total_claims": 22,
  "facts_cited": 10,
  "recommendations_with_evidence": 7,
  "assumptions_unvalidated": 3,
  "unsupported_claims": [],
  "irrelevant_citations": [],
  "low_trust_sources": [],
  "stale_citations": [],
  "contradictions": [],
  "requires_user_validation": ["claim_010", "claim_011"],
  "created_at": "2026-06-09T13:20:00Z"
}
```

---

## 15. Socrates APIs

Socrates is usually invoked by the stage pipeline. These endpoints support direct execution and frontend retrieval.

### 15.1 Run Socrates Review

```http
POST /api/v1/sessions/{session_id}/socrates/run
```

#### Request

```json
{
  "depth": "standard",
  "base_version": 1,
  "focus_areas": ["security", "operability", "cost"],
  "include_cross_examination": false
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage": "socratic_review",
  "stage_run_id": "run_soc_001",
  "depth": "standard",
  "status": "running",
  "personas": [
    "Devil's Advocate",
    "SRE / Ops Lead",
    "Security Architect",
    "FinOps Lead",
    "Delivery Lead"
  ]
}
```

---

### 15.2 Get Socrates Output

```http
GET /api/v1/sessions/{session_id}/socrates/latest
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage_run_id": "run_soc_001",
  "version": 1,
  "depth": "standard",
  "persona_findings": [
    {
      "persona": "SRE / Ops Lead",
      "summary": "Option B has higher operational burden because the team must operate Kafka/Flink style infrastructure.",
      "findings": [
        {
          "finding": "Operational complexity may slow incident recovery.",
          "severity": "high",
          "claim_ids": ["claim_020"]
        }
      ]
    }
  ],
  "synthesis": {
    "recommended_option_id": "OPT-A",
    "confidence": 0.82,
    "blind_spots": ["Peak-season burst profile is not yet modeled"],
    "premortem": ["Unexpected throughput spikes cause throttling or delayed fraud decisions"],
    "assumptions_to_validate": ["claim_010"]
  },
  "quality_gate": {
    "status": "passed",
    "blocking_failures": [],
    "warnings": [],
    "user_override_allowed": true
  }
}
```

---

## 16. Requirement Change and Re-Reasoning APIs

### 16.1 Submit Requirement Change

```http
POST /api/v1/sessions/{session_id}/changes
```

Registers a material change and computes initial impact.

#### Request

```json
{
  "change_type": "requirement_update",
  "changed_field": "requirements.non_functional.scale",
  "old_value_summary": "10K TPS, single-region acceptable",
  "new_value_summary": "100K TPS, multi-region active-active",
  "reason": "Updated business scale target for future growth"
}
```

#### Response

```json
{
  "change_event_id": "chg_001",
  "session_id": "sess_01jxyzabc123",
  "change_type": "requirement_update",
  "changed_field": "requirements.non_functional.scale",
  "impact_status": "computed",
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
    "requirements",
    "pattern_detection"
  ],
  "created_at": "2026-06-09T13:30:00Z"
}
```

---

### 16.2 Preview Change Impact

```http
POST /api/v1/sessions/{session_id}/changes/preview-impact
```

Computes impact without persisting the change.

#### Request

```json
{
  "changed_field": "requirements.non_functional.scale",
  "new_value_summary": "100K TPS, multi-region active-active"
}
```

#### Response

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
  "stable_stages": ["intake", "requirements", "pattern_detection"],
  "rationale": {
    "options": "Scale and topology affect viable architecture options.",
    "hld": "Multi-region topology changes component and deployment diagrams."
  }
}
```

---

### 16.3 Execute Selective Re-Reasoning

```http
POST /api/v1/sessions/{session_id}/changes/{change_event_id}/rereason
```

#### Request

```json
{
  "confirm": true,
  "socrates_depth": "standard",
  "generate_diffs": true,
  "stop_on_warning": false
}
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "change_event_id": "chg_001",
  "rereasoning_run_id": "rerun_001",
  "status": "running",
  "planned_stage_runs": [
    {
      "stage": "options",
      "stage_run_id": "run_options_v2_001",
      "base_version": 1,
      "target_version": 2
    },
    {
      "stage": "socratic_review",
      "stage_run_id": "run_soc_v2_001",
      "base_version": 1,
      "target_version": 2
    }
  ]
}
```

---

### 16.4 Get Change Event

```http
GET /api/v1/sessions/{session_id}/changes/{change_event_id}
```

#### Response

```json
{
  "change_event_id": "chg_001",
  "session_id": "sess_01jxyzabc123",
  "change_type": "requirement_update",
  "changed_field": "requirements.non_functional.scale",
  "old_value_summary": "10K TPS, single-region acceptable",
  "new_value_summary": "100K TPS, multi-region active-active",
  "impacted_stages": ["options", "socratic_review", "adr", "hld", "waf_review"],
  "stable_stages": ["intake", "requirements", "pattern_detection"],
  "regeneration_status": {
    "options": "completed",
    "socratic_review": "completed",
    "adr": "running",
    "hld": "pending",
    "waf_review": "pending"
  },
  "created_at": "2026-06-09T13:30:00Z"
}
```

---

## 17. Diff APIs

### 17.1 Generate Artifact Diff

```http
POST /api/v1/sessions/{session_id}/diffs
```

#### Request

```json
{
  "stage": "hld",
  "before_version": 1,
  "after_version": 2,
  "diff_type": "semantic"
}
```

#### Response

```json
{
  "diff_id": "diff_001",
  "session_id": "sess_01jxyzabc123",
  "stage": "hld",
  "before_version": 1,
  "after_version": 2,
  "diff_type": "semantic",
  "summary": "The HLD changed from single-region streaming to multi-region active-active streaming with global traffic routing and replicated data stores.",
  "added": ["Azure Front Door", "Secondary region Event Hubs", "Cross-region replication path"],
  "removed": [],
  "modified": [
    {
      "item": "Event Hubs topology",
      "before": "Single namespace in one region",
      "after": "Partitioned multi-region ingestion topology"
    }
  ],
  "created_at": "2026-06-09T13:45:00Z"
}
```

---

### 17.2 Get Diff

```http
GET /api/v1/sessions/{session_id}/diffs/{diff_id}
```

#### Response

Same as generated diff response.

---

### 17.3 List Diffs

```http
GET /api/v1/sessions/{session_id}/diffs?stage=hld
```

#### Response

```json
{
  "items": [
    {
      "diff_id": "diff_001",
      "stage": "hld",
      "before_version": 1,
      "after_version": 2,
      "summary": "Single-region to multi-region active-active topology",
      "created_at": "2026-06-09T13:45:00Z"
    }
  ]
}
```

---

## 18. Frontend Support APIs

These endpoints are optimized for the Streamlit MVP frontend.

### 18.1 Get Session Dashboard

```http
GET /api/v1/sessions/{session_id}/dashboard
```

Returns a combined view of session, pipeline, latest artifacts, quality gates, warnings, and open assumptions.

#### Response

```json
{
  "session": {
    "session_id": "sess_01jxyzabc123",
    "title": "Fintech real-time fraud detection",
    "current_stage": "hld",
    "active_version": 1
  },
  "pipeline": {
    "completed": 7,
    "total": 10,
    "current_stage": "hld"
  },
  "quality_summary": {
    "passed": 5,
    "warnings": 2,
    "failed": 0
  },
  "latest_artifacts": [
    {
      "stage": "adr",
      "version": 1,
      "title": "ADR-001: Real-time streaming architecture choice"
    }
  ],
  "open_assumptions": [
    {
      "claim_id": "claim_010",
      "claim": "The delivery team has limited Kafka operational experience."
    }
  ],
  "recent_events": [
    {
      "event_type": "stage_completed",
      "stage": "adr",
      "timestamp": "2026-06-09T13:15:00Z"
    }
  ]
}
```

---

### 18.2 Get Artifact Viewer Model

```http
GET /api/v1/sessions/{session_id}/viewer/artifacts
```

Returns frontend-ready artifact tabs and display metadata.

#### Response

```json
{
  "tabs": [
    {
      "key": "requirements",
      "label": "Requirements",
      "stage": "requirements",
      "artifact_id": "art_req_001",
      "version": 1,
      "display_type": "markdown"
    },
    {
      "key": "hld",
      "label": "HLD",
      "stage": "hld",
      "artifact_id": "art_hld_001",
      "version": 1,
      "display_type": "markdown_with_mermaid"
    },
    {
      "key": "socrates",
      "label": "Socrates",
      "stage": "socratic_review",
      "artifact_id": "art_soc_001",
      "version": 1,
      "display_type": "debate_view"
    }
  ]
}
```

---

### 18.3 Get Mermaid Diagrams

```http
GET /api/v1/sessions/{session_id}/viewer/diagrams?stage=hld&version=latest
```

#### Response

```json
{
  "session_id": "sess_01jxyzabc123",
  "stage": "hld",
  "version": 1,
  "diagrams": [
    {
      "diagram_id": "system_context",
      "title": "System Context",
      "syntax": "flowchart TD\n...",
      "render_check_status": "passed"
    },
    {
      "diagram_id": "container",
      "title": "Container View",
      "syntax": "flowchart TD\n...",
      "render_check_status": "passed_with_warnings"
    }
  ]
}
```

---

## 19. Admin and Diagnostic APIs

These endpoints should be disabled or protected in production.

### 19.1 Health Check

```http
GET /api/v1/health
```

#### Response

```json
{
  "status": "ok",
  "service": "archimedes-api",
  "version": "0.1.0",
  "timestamp": "2026-06-09T13:00:00Z"
}
```

---

### 19.2 Readiness Check

```http
GET /api/v1/health/ready
```

Checks dependent services.

#### Response

```json
{
  "status": "ready",
  "dependencies": {
    "cosmos_db": "ok",
    "blob_storage": "ok",
    "foundry_model": "ok",
    "foundry_iq_kb": "ok"
  }
}
```

---

### 19.3 Debug Retrieval

```http
POST /api/v1/admin/debug/retrieval
```

Runs a test retrieval against Foundry IQ. This is for development only.

#### Request

```json
{
  "query": "Azure architecture patterns for real-time fraud detection streaming ingestion",
  "top_k": 5
}
```

#### Response

```json
{
  "query": "Azure architecture patterns for real-time fraud detection streaming ingestion",
  "results": [
    {
      "source": "Azure Architecture Center",
      "source_url": "https://learn.microsoft.com/...",
      "excerpt": "...",
      "trust_level": "high",
      "source_freshness": "current"
    }
  ]
}
```

---

## 20. Error Codes

| Code | HTTP status | Meaning |
|---|---:|---|
| `session_not_found` | 404 | Session ID does not exist |
| `stage_not_found` | 404 | Invalid stage ID |
| `artifact_not_found` | 404 | Artifact/version not found |
| `invalid_stage_transition` | 409 | Requested stage cannot run from current state |
| `stage_already_running` | 409 | Another run is active for the same stage/session |
| `quality_gate_failed` | 422 | Stage output failed blocking quality gate |
| `version_conflict` | 409 | `base_version` does not match current artifact version |
| `idempotency_conflict` | 409 | Same idempotency key used with different payload |
| `foundry_iq_retrieval_failed` | 502 | Knowledge base retrieval failed |
| `llm_call_failed` | 502 | Model call failed |
| `tool_execution_failed` | 500 | App-local tool failed |
| `mermaid_render_check_failed` | 422 | Diagram render check failed |
| `permission_denied` | 403 | User cannot access session |
| `validation_error` | 422 | Request body validation failed |

---

## 21. HTTP Status Guidance

| Situation | Status |
|---|---:|
| Successful synchronous read | `200 OK` |
| Resource created | `201 Created` |
| Stage execution accepted | `202 Accepted` |
| Invalid request body | `422 Unprocessable Entity` |
| Auth failure | `401 Unauthorized` |
| Permission failure | `403 Forbidden` |
| Not found | `404 Not Found` |
| Version conflict | `409 Conflict` |
| Upstream service failure | `502 Bad Gateway` |
| Unexpected server failure | `500 Internal Server Error` |

---

## 22. FastAPI Route Skeleton

Suggested route module structure:

```text
src/archimedes/api/
├── __init__.py
├── main.py
├── deps.py
├── errors.py
├── response.py
├── routers/
│   ├── sessions.py
│   ├── pipeline.py
│   ├── stages.py
│   ├── artifacts.py
│   ├── claims.py
│   ├── evidence.py
│   ├── audits.py
│   ├── socrates.py
│   ├── changes.py
│   ├── diffs.py
│   ├── viewer.py
│   ├── health.py
│   └── admin.py
└── schemas/
    ├── requests.py
    └── responses.py
```

Example router skeleton:

```python
from fastapi import APIRouter, BackgroundTasks, Depends, Header

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", status_code=201)
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """Create a new architecture session."""
    ...


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get session summary."""
    ...
```

---

## 23. Request/Response DTO Placement

The API DTOs should reference the model package from `03-pydantic-schemas.md` where possible.

Suggested DTO files:

```text
src/archimedes/models/api.py
src/archimedes/api/schemas/requests.py
src/archimedes/api/schemas/responses.py
```

DTOs should avoid leaking internal Cosmos DB fields such as `_etag`, `_rid`, `_self`, and `_ts`.

---

## 24. Demo Scenario API Flow

### 24.1 Create Session

```http
POST /api/v1/sessions?auto_start=true
```

Body:

```json
{
  "business_need": "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.",
  "title": "Fintech fraud detection demo",
  "domain": "fintech"
}
```

### 24.2 Stream Progress

```http
GET /api/v1/sessions/{session_id}/events
```

### 24.3 Run Pipeline

```http
POST /api/v1/sessions/{session_id}/pipeline/run
```

Body:

```json
{
  "stop_on_warning": false,
  "socrates_depth": "standard"
}
```

### 24.4 Review Artifacts

```http
GET /api/v1/sessions/{session_id}/dashboard
GET /api/v1/sessions/{session_id}/viewer/artifacts
GET /api/v1/sessions/{session_id}/artifacts/hld/latest
```

### 24.5 Submit Change

```http
POST /api/v1/sessions/{session_id}/changes
```

Body:

```json
{
  "change_type": "requirement_update",
  "changed_field": "requirements.non_functional.scale",
  "old_value_summary": "10K TPS",
  "new_value_summary": "100K TPS and multi-region active-active",
  "reason": "Updated demo scale requirement"
}
```

### 24.6 Execute Re-Reasoning

```http
POST /api/v1/sessions/{session_id}/changes/{change_event_id}/rereason
```

Body:

```json
{
  "confirm": true,
  "socrates_depth": "standard",
  "generate_diffs": true
}
```

### 24.7 View Diff

```http
GET /api/v1/sessions/{session_id}/diffs?stage=hld
```

---

## 25. Non-Functional API Requirements

### 25.1 Latency Targets

| API type | Target |
|---|---:|
| Simple read APIs | `< 300 ms` locally / low data volume |
| Session dashboard | `< 700 ms` locally / low data volume |
| Stage start APIs | `< 1 s` to return accepted response |
| Stage execution | Async; may take seconds to minutes |
| SSE event delivery | Near-real-time, best effort |

### 25.2 Reliability

- Stage run creation must be idempotent.
- Stage patch application must use optimistic concurrency.
- Late patches from cancelled/stale stage runs must be rejected.
- If streaming disconnects, the frontend can recover by polling `/pipeline` and `/stage-runs`.

### 25.3 Security

- Never expose raw secrets or connection strings.
- Never expose full internal LLM prompts in public APIs.
- Never expose raw Cosmos DB system fields.
- Admin/debug endpoints must be disabled or protected outside development.

### 25.4 Observability

Every API request should emit:

- `request_id`
- `session_id` where applicable
- `stage_run_id` where applicable
- HTTP method and path
- latency
- result status
- error code if failed

---

## 26. MVP Endpoint Checklist

The following endpoints are required for the MVP demo.

| Endpoint | Required |
|---|---:|
| `POST /sessions` | Yes |
| `GET /sessions/{session_id}` | Yes |
| `GET /sessions/{session_id}/dashboard` | Yes |
| `GET /sessions/{session_id}/pipeline` | Yes |
| `POST /sessions/{session_id}/pipeline/run` | Yes |
| `POST /sessions/{session_id}/pipeline/run-next` | Yes |
| `GET /sessions/{session_id}/events` | Recommended |
| `GET /sessions/{session_id}/artifacts` | Yes |
| `GET /sessions/{session_id}/artifacts/{stage_id}/latest` | Yes |
| `GET /sessions/{session_id}/viewer/artifacts` | Yes |
| `GET /sessions/{session_id}/viewer/diagrams` | Yes |
| `GET /sessions/{session_id}/claims` | Recommended |
| `GET /sessions/{session_id}/evidence` | Recommended |
| `POST /sessions/{session_id}/changes` | Yes |
| `POST /sessions/{session_id}/changes/{change_event_id}/rereason` | Yes |
| `GET /sessions/{session_id}/diffs` | Yes |
| `GET /health` | Yes |
| `GET /health/ready` | Yes |

---

## 27. Open Questions

| Question | Recommendation |
|---|---|
| Should APIs expose raw StagePatch objects? | No for normal frontend. Expose only in admin/debug mode. |
| Should users be able to edit artifacts manually? | Defer. For MVP, changes should come through requirement updates or reruns. |
| Should the frontend use WebSockets instead of SSE? | Use SSE for MVP. WebSockets can be added later. |
| Should deep Socrates mode be exposed in UI? | Expose but mark as slower/costlier. Default to standard. |
| Should admin debug endpoints be included? | Yes locally, disabled in deployed demo unless protected. |

---

## 28. Implementation Acceptance Criteria

The API layer is ready for MVP when:

1. A user can create a session from a business need.
2. The frontend can retrieve session dashboard and stage timeline.
3. The pipeline can run from intake through final evidence audit.
4. Each long-running stage returns a `stage_run_id` immediately.
5. Stage status is visible through polling and/or SSE.
6. Artifacts can be retrieved by stage and latest version.
7. Claims and evidence can be listed and linked.
8. Evidence audit output is retrievable.
9. A requirement change can be submitted.
10. Impacted and stable stages are returned.
11. Selective re-reasoning creates new artifact versions.
12. Before/after diffs can be retrieved.
13. Version conflicts and idempotency conflicts return clear errors.
14. Health and readiness endpoints work.

---

## 29. Summary

The Archimedes API layer is the control surface for the architecture workbench.

It does not implement the reasoning itself. Instead, it coordinates the session lifecycle, invokes the orchestrator, exposes pipeline status, retrieves artifacts, provides evidence transparency, and supports the key demo feature: requirement-change-driven selective re-reasoning with before/after diffs.

For the MVP, prioritize stable session creation, pipeline execution, artifact retrieval, evidence visibility, and re-reasoning APIs. More advanced APIs such as artifact export, admin retrieval debugging, full RBAC, and manual artifact editing can be added later.

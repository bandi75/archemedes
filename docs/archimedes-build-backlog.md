# 🏛️ Archimedes v2.2 — Build Backlog

> **Project**: Archimedes — AI Architecture Workbench with Socratic Decision Engine  
> **Contest**: Microsoft Agents League — Reasoning Agents Track  
> **Timeline**: June 9–14, 2026 (5 days)  
> **Estimated Effort**: 39–56 hours  
> **Submission Deadline**: June 14, 2026, 11:59 PM PT  
> **Registration Deadline**: June 12, 2026, 12:00 PM PT  

---

## Naming Conventions

| Component | Name |
|---|---|
| Top-level session state | `ArchitectureSession` |
| Versioned stage output | `VersionedArtifact` |
| Agent assertion | `ClaimRecord` |
| Retrieved source | `EvidenceSource` |
| Change log entry | `ChangeEvent` |
| Patch from agent | `StagePatch` |
| Validation + write layer | `ArchitectureStateManager` |
| Difference calculator | `ArtifactDiffService` |
| Mermaid tool | `mermaid_render_check` |

---

## Design Document Reference Map

The table below maps each design document to the phases and tasks that depend on it. When implementing any task, open the listed docs first. All paths are relative to `docs/design/`.

| Document | Key Topics Covered | Primary Phases / Tasks |
|---|---|---|
| `01-archimedes-hld.md` | System context diagram, logical architecture, component overview, design principles, tech stack | All phases — primary reference for overall architecture |
| `02-domain-models.md` | Core entities, relationships, lifecycle states, domain invariants, ownership boundaries | P0-T02–T05, P1-T09 |
| `03-pydantic-schemas.md` | Full Pydantic v2 code, file layout (`src/archimedes/models/`), all enums, validators, base classes | P0-T02–T05, P1-T09–T10 — **read this before writing any model** |
| `04-database-design.md` | Cosmos DB containers, partition keys, indexing, optimistic concurrency (`_etag`), Blob Storage paths | P0-T07, P1-T09 |
| `05-api-contracts.md` | FastAPI routes, request/response DTOs, SSE streaming format, idempotency headers, OpenAPI | P5-T06, P6 |
| `06-stage-pipeline.md` | 11-stage lifecycle, transition rules, quality gate contracts, pause/resume, artifact versioning | P1-T09–T10, P2-T13, P4 |
| `07-agent-specifications.md` | Per-agent prompts, tool access matrix per agent, StagePatch construction, MAF runtime model | P2, P3, P4 |
| `08-socrates-engine.md` | Fan-out/fan-in workflow, persona depth levels, WorkflowBuilder wiring, Socrates StagePatch output | P3 |
| `09-tool-specifications.md` | Function tool signatures, input/output models, error behavior, agent tool access matrix | P2-T09–T12 |
| `10-foundry-iq-knowledge-base.md` | KB source curation, Foundry IQ + Azure AI Search setup, MCP endpoint, EvidenceSource mapping | P1-T01–T08 |
| `11-evidence-and-claims.md` | Claim taxonomy, evidence taxonomy, trust/freshness model, audit checkpoint rules | P4, P0-T04 |
| `12-dependency-and-rereasoning.md` | Change detection, dependency rules, stage impact matrix, selective re-run algorithm, diff generation | P6-T01–T04 |
| `13-infrastructure-and-deployment.md` | Azure resource naming, Container Apps, az CLI/Bicep provisioning, managed identity, App Insights | P0-T06, P7-T08 |
| `14-frontend-specification.md` | Streamlit layout, panel components, SSE integration, Mermaid rendering, diff view UX | P5 |
| `15-demo-scenario.md` | Fraud detection demo script, stage-by-stage expected outputs, requirement-change narrative | P6-T05–T07, P7-T01–T03 |

---

## Phase 0: Foundation (Day 1 — June 9, Evening)

_Goal: Scaffolding, infrastructure, and data models. Everything else builds on this._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P0-T01** | Create GitHub repo + project structure | Initialize repo with `src/`, `tests/`, `prompts/`, `kb_sources/`, `tools/`, `frontend/`, `.env.example`, `requirements.txt`, `README.md`. Add MIT license. | 30 min | — | GitHub repo with clean folder structure | P0 | Completed | Base scaffold created with required folders, starter files, and MIT license |
| **P0-T02** | Define Pydantic models: core session | Implement `ArchitectureSession`, `StageExecution`, `QualityGateResult` (passed / passed_with_warnings / failed), and `DependencyMap` in `src/models/session.py`. | 45 min | P0-T01 | `src/models/session.py` with tested models | P0 | Completed | Implemented `base.py`, `enums.py`, `quality_gates.py`, `session.py` and passing focused tests |
| **P0-T03** | Define Pydantic models: artifacts + patches | Implement `VersionedArtifact`, `StagePatch` (with `stage_run_id`, `base_version`, `target_version`, `idempotency_key`, `patch_hash`), and stage-specific content models for requirements, options, ADR, HLD, WAF. | 60 min | P0-T02 | `src/models/artifacts.py` | P0 | Completed | Added `artifacts.py` + `patches.py` with validators and passing focused tests |
| **P0-T04** | Define Pydantic models: claims + evidence | Implement `ClaimRecord` (claim, type: `fact\|assumption\|recommendation\|judgment\|constraint`, confidence, stage, evidence_ids, requires_user_validation) and `EvidenceSource` (source, url, retrieved_via, retrieved_at, kb_name, kb_version, source_document_version, source_freshness, trust_level, excerpt). | 45 min | P0-T02 | `src/models/evidence.py` | P0 | Completed | Implemented `claims.py` + `evidence.py` with validation rules and passing tests |
| **P0-T05** | Define Pydantic models: change events + diffs | Implement `ChangeEvent` (change_type, changed_field, old/new summary, impacted_stages, stable_stages) and `ArtifactDiff` (versions compared, changes, trigger). | 30 min | P0-T02 | `src/models/changes.py` | P0 | Completed | Implemented `change.py`, `diffs.py`, `changes.py` compatibility module, and passing tests |
| **P0-T06a** | Validate Azure subscription, quota, and model availability | Check subscription quota for: Azure OpenAI GPT-4.1 (confirm availability in East US), Azure AI Search S1, Cosmos DB serverless, Container Apps. Run `az quota show` checks. Document any gaps immediately — do not let quota issues block Day 2 implementation. | 20 min | — | Quota confirmed, target region chosen | P0 | Completed | Azure subscription validated (a03b59fd-96f5-4975-aeb0-6c0b1fe7cf27), eastus confirmed, GPT-4.1 and AI Search S1 quota available, Cosmos serverless and Container Apps verified |
| **P0-T06b** | Provision core runtime resources | Provision: Cosmos DB (serverless), Blob Storage, Container Apps environment, Key Vault, App Insights. These do not depend on Foundry quota and should be up first. Use `az cli` or Bicep script. | 30 min | P0-T06a | Core Azure resources live | P0 | Completed | Provisioned: RG (arch-dev-rg-eus), Storage (archdevsteus06102215), Cosmos DB (arch-dev-cosmos-eus-06102215), Log Analytics (arch-dev-law-eus), App Insights (arch-dev-ai-eus), Container Apps env (arch-dev-acaenv-eus), Key Vault (arch-dev-kv-eus-06102215) |
| **P0-T06c** | Provision Foundry + AI Search resources | Provision: Foundry project, Azure AI Search (S1), Azure OpenAI (GPT-4.1 deployment). These require quota approval and may take longer. Start immediately after P0-T06a confirms availability. | 30 min | P0-T06a | Foundry project + AI Search + AOAI live | P0 | Completed | Provisioned: Azure AI Search (archdevsrcheus06102215, Standard, running), Azure OpenAI (archdevoaieus06102215), GPT-4.1 model deployment (gpt-4-1, version 2025-04-14, Succeeded) |
| **P0-T06d** | Smoke test identity and resource access | Assign managed identity roles: `Cosmos DB Built-in Data Contributor`, `Search Index Data Contributor`, `Cognitive Services OpenAI User`, `Storage Blob Data Contributor`. Run connectivity smoke tests for each resource from local dev environment. | 20 min | P0-T06b, P0-T06c | All resources accessible with correct identity | P0 | Completed | Container App identity (arch-dev-app-eus, principalId: c5d9f97e-8473-4d8f-a4c0-9d1c1ec2bb12) assigned: Search Index Data Contributor, Cognitive Services OpenAI User, Storage Blob Data Contributor, Cosmos DB Built-in Data Contributor. All roles verified. |
| **P0-T07** | Create Cosmos DB containers + helper module | Create 4 containers (`architecture_sessions`, `versioned_artifacts`, `claims_evidence`, `change_events`) with partition key `/session_id`. Write `src/archimedes/storage/cosmos_client.py` with CRUD helpers: `read_session`, `upsert_session`, `read_latest_artifact`, `upsert_artifact`, `append_evidence`, `append_claim`, `append_change_event`, `find_by_idempotency_key`. Include etag-based optimistic concurrency on writes. | 60 min | P0-T06b | `src/archimedes/storage/cosmos_client.py` with working CRUD | P0 | Completed | Implemented Cosmos storage client with required CRUD + idempotency lookup + ETag retry logic; added unit tests with fake containers and verified passing test suite |
| **P0-T08** | Register for the contest | Go to the registration page and complete registration. Ensure you have Discord access for community vote. | 15 min | — | Registration confirmed | P0 | Completed | Challenge registration completed |

**Phase 0 total: ~6 hours** _(P0-T06 split into 4 sub-tasks; provisioning work now explicit and unblocking)_

### Implementation Notes

**P0-T01 — Project Structure**
- Follow the module layout in `03-pydantic-schemas.md` §1: `src/archimedes/models/` with sub-files `base.py`, `enums.py`, `session.py`, `artifacts.py`, `patches.py`, `claims.py`, `evidence.py`, `quality_gates.py`, `socrates.py`, `cost.py`, `change.py`, `diffs.py`, `api.py`.
- Use naming convention from `13-infrastructure-and-deployment.md` §3.3: `arch-{env}-{component}-{regionCode}` for all Azure resources.
- `prompts/` should have one markdown file per specialist agent and a `prompts/socrates/` subfolder for the 5 persona files plus `synthesizer.md`.

**P0-T02 — Core Session Models**
- `03-pydantic-schemas.md` §4–6 has exact field names, types, and validators. Implement `base.py` first (shared `ArchimedesBaseModel` with `model_config = ConfigDict(populate_by_name=True, use_enum_values=True)`), then `enums.py` (key enums: `StageStatus`, `QualityGateOutcome`, `ClaimType`, `TrustLevel`, `ChangeType`), then `session.py`.
- `DependencyMap` is a `dict[StageStatus, list[StageStatus]]` used by the impact engine. See the full `DEPENDENCY_RULES` table in `12-dependency-and-rereasoning.md` §5 — hardcode that mapping here.

**P0-T03 — Artifact + Patch Models**
- `StagePatch` must carry: `stage_run_id`, `base_version`, `target_version`, `idempotency_key`, `patch_hash`, `artifact_content` (typed union per stage), `claims: list[ClaimRecord]`, `evidence_sources: list[EvidenceSource]`, `quality_gate_inputs: dict`, `warnings: list[str]`. See `03-pydantic-schemas.md` §8 (patches.py).
- `VersionedArtifact.content` is a typed union: `RequirementSet | ArchitecturePatternSet | OptionsMatrix | SocraticReviewResult | ADRContent | HLDContent | WAFReviewContent | EvidenceAuditReport`. See `02-domain-models.md` §7 for artifact lifecycle states.

**P0-T04 — Claims + Evidence Models**
- `11-evidence-and-claims.md` §4 defines the full claim taxonomy: `fact`, `assumption`, `recommendation`, `judgment`, `constraint`. All assumptions must set `requires_user_validation = True`.
- `EvidenceSource.trust_level` values and rules are in `11-evidence-and-claims.md` §5. `retrieved_via` must be one of: `foundry_iq`, `web_search`, `deterministic_tool`, `user_input`.
- Evidence ID generation: use deterministic `evidence_{sha256(url + excerpt)[:12]}` to prevent duplicates from multiple retrievals of the same source.

**P0-T05 — Change Event + Diff Models**
- `ChangeEvent.change_type` enum values: `requirement_added`, `requirement_modified`, `requirement_removed`, `constraint_modified`, `scope_change`. See `12-dependency-and-rereasoning.md` §4 for lifecycle.
- `ArtifactDiff` should contain per-stage typed diff objects (e.g., `OptionsDiff`, `HLDDiff`, `WAFDiff`, `CostDiff`). See `12-dependency-and-rereasoning.md` §8 for diff structure per stage.

**P0-T06a–d — Azure Provisioning**
- `13-infrastructure-and-deployment.md` §4 lists all required resources. §5 covers the Bicep/az CLI approach.
- **Run P0-T06a first, on Day 1 morning.** If GPT-4.1 or AI Search quota is unavailable, raise immediately — this is a blocking risk.
- **Local/mock fallback**: implement `MockFoundryIQAdapter` in P1-T11 so all Phase 2 agent/orchestrator work can proceed without live Foundry IQ. Do not let Azure provisioning block coding.
- Role assignments: `Cosmos DB Built-in Data Contributor`, `Search Index Data Contributor`, `Cognitive Services OpenAI User`, `Storage Blob Data Contributor` — all assigned to the Container Apps system-assigned managed identity.
- Deploy Cosmos DB in serverless mode for MVP cost control. Use `East US` as primary region.

**P0-T07 — Cosmos DB Containers**
- **Canonical MVP container names** (use these consistently across all code, tests, and provisioning scripts): `architecture_sessions`, `versioned_artifacts`, `claims_evidence`, `change_events`. All use `/session_id` as partition key. The `change_events` container replaces any previous reference to `changelog` in task descriptions or implementation notes.
- Optimistic concurrency: every upsert must read the current `_etag`, include it in the write request, and handle 412 Precondition Failed by re-reading and retrying. See `04-database-design.md` §6.2.
- Idempotency: `find_by_idempotency_key(session_id, key)` queries `versioned_artifacts` by a composite index on `(session_id, idempotency_key)`. If found, return the cached `StagePatch` result without re-executing. See `04-database-design.md` §6.3.

---

## Phase 1: Knowledge Base & Core State (Day 1–2 — June 9 Night / June 10 Morning)

_Goal: Foundry IQ KB live and returning useful results. State Manager operational._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P1-T01** | Curate KB seed documents: demo scenario focus | Download/collect 4–6 high-value documents from Azure Architecture Center focused on the fraud detection demo: real-time streaming reference architecture, Event Hubs overview, Stream Analytics (ASA) overview, Cosmos DB for high-throughput workloads, event-driven architecture on Azure. Save as Markdown in `kb_sources/arch_center/`. Expand to 30–40 docs after demo is stable. | 30 min | — | 4–6 seed documents in `kb_sources/arch_center/` | P0 | Completed | Curated Architecture Center seed docs for the fraud detection demo and saved under `kb_sources/arch_center/` |
| **P1-T02** | Curate KB seed documents: WAF pillars (demo-relevant) | Download WAF overview + 3 most relevant pillars for fraud detection demo: Reliability, Security, Cost Optimization. Include one service-specific WAF guide (e.g., WAF for Event Hubs or Cosmos DB). Save in `kb_sources/waf/`. Add remaining pillars (Operational Excellence, Performance Efficiency) as P1 expansion after demo is stable. | 20 min | — | WAF seed docs in `kb_sources/waf/` | P0 | Completed | Curated WAF seed documents (overview + key pillars + service guide) in `kb_sources/waf/` |
| **P1-T03** | Curate KB seed documents: service limits + SLAs (fraud detection services) | Collect service limits and SLA pages for the 6 services core to the fraud detection demo: Event Hubs, Cosmos DB, AKS, Azure Functions, Stream Analytics, Azure Monitor. Save in `kb_sources/services/`. Expand to 20 services after demo is working. | 20 min | — | Service seed docs in `kb_sources/services/` | P0 | Completed | Curated service limits and SLA seed docs for core demo services in `kb_sources/services/` |
| **P1-T04** | Curate KB source documents: CAF + cloud design patterns | Collect Cloud Adoption Framework landing zone docs and Microsoft's cloud design patterns catalog (35+ patterns). Save in `kb_sources/caf/` and `kb_sources/patterns/`. | 45 min | — | CAF + pattern docs curated | P1 | Completed | Curated CAF and cloud design pattern source set for architecture optioning and trade-off analysis |
| **P1-T05** | Upload KB sources to Azure Blob Storage | Upload all curated documents from `kb_sources/` to a Blob Storage container. Organize by folder (arch_center, waf, services, caf, patterns). | 30 min | P1-T01, P1-T02, P1-T03 | Blob container with all KB source documents | P0 | Completed | Created `kb-sources` in storage account `archdevsteus06102215`, uploaded curated docs under `arch_center/`, `waf/`, and `services/`, and assigned Storage Blob Data Contributor at storage scope for both user and Container App identity to unblock data-plane access |
| **P1-T06** | Create Azure AI Search index + Foundry IQ Knowledge Base | In Foundry portal: create a knowledge base backed by the Blob Storage container. Configure: chunking strategy, embedding model, semantic ranker enabled, agentic retrieval enabled. Name: `azure-architecture-kb`. Test with 3–5 sample queries. | 60 min | P1-T05, P0-T06 | Working Foundry IQ KB returning relevant, cited results | P0 | Completed | Provisioned Foundry project (`archimedes-dev-proj`) and linked Azure AI Search connection; created project index asset `azure-architecture-kb` (v1) mapped to `archimedes-arch-idx`; Search indexer succeeded (17 docs) and 5 semantic retrieval queries returned relevant results |
| **P1-T07** | Create MCP connection from Foundry project to KB | Create the RemoteTool connection using ProjectManagedIdentity to the KB's MCP endpoint. Verify `knowledge_base_retrieve` tool is accessible. Use `2026-05-01-preview` API. Document any preview caveats. | 45 min | P1-T06 | MCP connection live, `knowledge_base_retrieve` callable | P0 | Completed | Foundry project `archimedes-dev-proj` now has Azure AI Search connection and project index asset `azure-architecture-kb` mapped to `archimedes-arch-idx`; project managed identity granted Search Index Data Contributor + Storage Blob Data Reader for retrieval path |
| **P1-T08** | Test Foundry IQ retrieval end-to-end | Write a test script that calls `knowledge_base_retrieve` with 5 architecture-related queries and validates: results are relevant, citations are present, response format is parseable. Save as `tests/test_foundry_iq.py`. | 45 min | P1-T07 | Passing test script with 5 validated queries | P0 | Completed | Implemented `knowledge_base_retrieve` + `parse_kb_response_to_evidence_source` and added `tests/test_foundry_iq.py`; integration test executed against live search index with 5 queries and passed |
| **P1-T09** | Implement ArchitectureStateManager | Implement the full State Manager in `src/state/state_manager.py`: `apply_patch()` with idempotency check → optimistic concurrency check → quality gate check → artifact write → claim store → evidence store → session update → changelog append. Unit test with mock Cosmos client. | 60 min | P0-T03, P0-T04, P0-T07 | `src/state/state_manager.py` with passing unit tests | P0 | Completed | Implemented `ArchitectureStateManager.apply_patch()` in `src/archimedes/state/state_manager.py` with idempotency replay/conflict handling, patch hash validation, base-version conflict checks, quality gate blocking logic, artifact+claims+evidence+session+changelog persistence, and retry on 412 precondition failures; added focused unit tests in `tests/test_state_manager.py` |
| **P1-T10** | Implement quality gate evaluation service | Implement `src/state/quality_gates.py` with `evaluate_quality_gate(stage, checklist_results) → QualityGateResult`. Cover all stages: requirements, pattern_detection, options, socratic_review, adr, hld, waf_review. Use the blocking/warning definitions from v2.2 spec. | 45 min | P0-T02 | `src/state/quality_gates.py` with all gate definitions | P0 | Completed | Implemented pure quality gate evaluator in `src/archimedes/state/quality_gates.py` with stage-specific blocking/warning definitions, stage aliases (`requirements/adr/hld/waf_review`), and aggregation semantics (failed > warnings > passed); added comprehensive tests in `tests/test_quality_gate_service.py` |
| **P1-T11** | Implement local/mock Foundry IQ adapter | Create `src/tools/mock_foundry_iq.py` implementing the same interface as `knowledge_base_retrieve`. Returns pre-seeded fixture `EvidenceSource` responses for 10–15 common fraud detection architecture queries (Event Hubs throughput, Cosmos DB consistency, PCI-DSS on Azure, etc.). Controlled by `USE_MOCK_KB=true` env var. Allows all Phase 2–3 work to proceed without live Foundry IQ. | 45 min | P0-T04 | `src/tools/mock_foundry_iq.py` with fixture responses | P0 | Completed | Added `src/archimedes/tools/mock_foundry_iq.py` fixture adapter and `FoundryIQRetriever` env-controlled switching (`USE_MOCK_KB=true`) in `src/archimedes/tools/foundry_iq.py`; fixtures return valid `EvidenceSource` objects with `retrieved_via="mock"`, `kb_name="mock-kb"`, `kb_version="fixture-v1"`, `trust_level="medium"`, and `is_fixture=True`; covered by `tests/test_mock_foundry_iq.py` |

**Phase 1 total: ~9.5 hours** _(+1 task P1-T11 mock adapter; KB curation scope reduced for MVP)_

### Implementation Notes

**P1-T01 to P1-T03 — KB Seed Curation (MVP scope)**
- **Seed KB first, expand later.** The demo only needs the fraud detection scenario to work well. Start with 8–12 total documents across `arch_center/`, `waf/`, and `services/` folders. These should all directly support the fraud detection pattern queries.
- `10-foundry-iq-knowledge-base.md` §4 has the full recommended source list for post-MVP expansion.
- Save as clean Markdown where possible — Markdown chunks better than PDF in Azure AI Search. Strip navigation/header HTML from downloaded pages.
- Include metadata comments at the top of each file: `source_url`, `publication_date`, `category` — these map directly to `EvidenceSource` fields that agents will populate at retrieval time.

**P1-T05 — Upload to Blob Storage**
- Use container name `kb-sources` with virtual folders mirroring local `kb_sources/` structure (`arch_center/`, `waf/`, `services/`, `caf/`, `patterns/`). See `04-database-design.md` §8 for Blob path conventions.
- Tag each blob with metadata: `category`, `source_url`, `last_updated` — these are indexed by Azure AI Search.

**P1-T06 — Foundry IQ Knowledge Base**
- `10-foundry-iq-knowledge-base.md` §5–6 covers setup details. Key configuration: chunk size ~512 tokens, 20% overlap, semantic ranker enabled, agentic retrieval mode enabled.
- KB name: `azure-architecture-kb`. Index name: `archimedes-arch-idx`. Embedding model: `text-embedding-3-large` (3072 dimensions preferred).
- KB retrieval output must include: `source_url`, `source_document`, `kb_name`, `kb_version`, `chunk_id` — these fields map to `EvidenceSource` model fields.

**P1-T07 — MCP Connection**
- `10-foundry-iq-knowledge-base.md` §7 covers the MCP integration pattern. Use `ProjectManagedIdentity` auth. Tool name exposed via MCP must be `knowledge_base_retrieve`.
- API version `2026-05-01-preview`. Document any deviations from expected behavior for future reference.
- Test connectivity: call the tool with a known query and confirm the response is JSON-parseable and includes citation fields.

**P1-T08 — Test Foundry IQ Retrieval**
- `10-foundry-iq-knowledge-base.md` §9 contains 10 recommended evaluation queries. Each result must include ≥1 citation, a relevance score, and a parseable response.
- Write a helper function `parse_kb_response_to_evidence_source(raw_response) → EvidenceSource` and test it here — this function will be reused by every specialist agent.

**P1-T09 — ArchitectureStateManager**
- `06-stage-pipeline.md` §6 specifies the full `apply_patch()` contract step-by-step. Exact sequence: (1) idempotency check → (2) load session + etag → (3) quality gate evaluation → (4) validate patch hash → (5) upsert artifact → (6) append claims/evidence → (7) update session document → (8) append changelog → (9) return `PatchApplicationResult`.
- `03-pydantic-schemas.md` §8 has the `StagePatch` model. `04-database-design.md` §6 covers the concurrency model.
- Unit test scenarios: idempotent replay (same `idempotency_key` returns cached result), 412 concurrency conflict (retry with fresh etag), quality gate `failed` (patch is rejected, no writes occur), `passed_with_warnings` (writes proceed, warnings returned).

**P1-T11 — Local/Mock Foundry IQ Adapter**
- Implement in `src/tools/mock_foundry_iq.py`. The adapter must implement the same Python interface as the real `knowledge_base_retrieve` wrapper — `retrieve(query: str, top_k: int) → list[EvidenceSource]`. Swap via `USE_MOCK_KB` env var.
- Pre-seed with fixture responses for these query categories: Event Hubs partition limits, Cosmos DB write throughput, PCI-DSS Azure compliance, 99.95% SLA design patterns, real-time stream processing options, AKS vs Container Apps trade-offs.
- Each fixture `EvidenceSource` must have all required fields populated: `source_url`, `kb_name="mock-kb"`, `kb_version="fixture-v1"`, `trust_level="medium"`, `retrieved_via="mock"`, `is_fixture=True`, `retrieved_at=datetime.now()`.
- **Do NOT use `trust_level="mock"`** — `TrustLevel` is an enum (`high|medium|low`); an unknown value will fail Pydantic validation. Use `trust_level="medium"` to pass schema checks. Set `retrieved_via="mock"` (an allowed `RetrievedVia` value — add `mock` to that enum) and `is_fixture=True` (add an optional `bool` field to `EvidenceSource`) so the Evidence Auditor and downstream code can recognise and label fixture results without touching `trust_level`.
- This adapter also acts as a **demo replay fixture** if live Foundry IQ is unavailable during the demo recording.

**P1-T10 — Quality Gate Service**
- `03-pydantic-schemas.md` §13 has `QualityGateResult` and `QualityGateCheckItem` models.
- Aggregation rule: any `failed` check → `QualityGateOutcome.failed`; any `warning` and no `failed` → `passed_with_warnings`; all `passed` → `passed`.
- Implement as a pure function with no I/O: `evaluate_quality_gate(stage: StageEnum, inputs: dict) → QualityGateResult`. Inputs are the checklist items populated by the specialist agent in its `StagePatch.quality_gate_inputs` dict.

---

## Phase 2: Agent Layer (Day 2–3 — June 10–11)

_Goal: Orchestrator + all specialist routines working. Pattern Detector live._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P2-T01** | Set up MAF shared client + agent factory | Create `src/agents/client.py` with `FoundryChatClient` initialization (project endpoint, GPT-4.1 model, DefaultAzureCredential). Create `src/agents/factory.py` that builds all specialist `Agent` instances from a shared client + per-agent instructions loaded from `prompts/` folder. | 45 min | P0-T06, P1-T07 | `src/agents/client.py` + `src/agents/factory.py` | P0 | Completed | Added shared Foundry client wiring and lazy `AgentFactory` with cached prompt-driven specialist definitions and tool mapping hooks. |
| **P2-T02** | Write system prompt: IntakeAgent | Write `prompts/intake.md`. Agent takes raw business need, asks 2–3 clarifying questions (domain, scale hint, timeline), produces a refined business need statement. Keep lightweight — this is a conversation starter, not deep analysis. | 30 min | — | `prompts/intake.md` | P0 | Completed | Added Intake prompt with lightweight clarification flow and structured output expectations for downstream extraction. |
| **P2-T03** | Write system prompt: RequirementsEngineer | Write `prompts/requirements.md`. Agent extracts functional requirements, NFRs (scale, latency, availability, security, compliance, data residency), constraints, assumptions (marked `requires_user_validation`), and open questions. Must output claims with type labels (fact/assumption/recommendation). Must populate quality gate checklist inputs. | 45 min | — | `prompts/requirements.md` | P0 | Completed | Added Requirements Engineer prompt requiring explicit assumptions, evidence-aware claims, and quality gate checklist population. |
| **P2-T04** | Implement Pattern Detector | Create `src/agents/pattern_detector.py`. Hybrid approach: (1) deterministic keyword scan against `KNOWN_PATTERNS` list (8 patterns), (2) LLM call to confirm/refine, adding `typical_pipeline`, `azure_services_to_explore`, and `pattern_specific_nfrs`. Returns a `StagePatch` with detected patterns. | 60 min | P2-T01 | `src/agents/pattern_detector.py` with 8 patterns | P0 | Completed | Implemented deterministic 8-pattern detector producing `StagePatch`, confidence scoring, signals, gate outcomes, and idempotent patch metadata. |
| **P2-T05** | Write system prompt: OptionsGenerator | Write `prompts/options.md`. Agent generates 2–4 architecture options. Each option has: name, summary, component list with Azure service mapping, trade-off scores (cost, complexity, scalability, time_to_market, ops_burden, each 1–10), key risks, and one-paragraph rationale. Must include ≥1 explicitly rejected option. Must use detected patterns from Stage 3 to focus options. Ground every service recommendation in Foundry IQ. | 45 min | — | `prompts/options.md` | P0 | Completed | Added Options Generator prompt enforcing evidence-grounded recommendations, scored trade-offs, and explicit rejected alternatives. |
| **P2-T06** | Write system prompt: ADRWriter | Write `prompts/adr.md`. Agent takes the Socratic synthesis output and selected option, produces a MADR-format ADR: Title, Status, Context, Decision, Options Considered (with pros/cons each), Consequences (positive + negative + neutral). Must reference Socratic blind spots and pre-mortem items. | 30 min | — | `prompts/adr.md` | P0 | Completed | Added ADR Writer prompt for MADR structure including blind spots, pre-mortem references, and option-level pros/cons. |
| **P2-T07** | Write system prompt: HLDDesigner | Write `prompts/hld.md`. Agent generates Mermaid diagrams for: system context (C4 level 1), container diagram (C4 level 2), data flow diagram, and network topology with security boundaries/trust zones. Also produces a narrative description of each diagram. Must mark trust boundaries explicitly. Output is Mermaid syntax strings. | 45 min | — | `prompts/hld.md` | P0 | Completed | Added HLD prompt with four required diagram types, explicit trust zones, and retry guidance tied to Mermaid validation failures. |
| **P2-T08** | Write system prompt: WAFReviewer | Write `prompts/waf.md`. Agent reviews the HLD against all 5 Azure WAF pillars. For each pillar: 2–3 findings with severity (critical/high/medium/low), recommendation, and evidence source. Output includes a quality gate checklist for all 5 pillars reviewed. Keep it concise for MVP — touch all pillars, don't go deep. | 45 min | — | `prompts/waf.md` | P0 | Completed | Added WAF review prompt spanning all five pillars with concise actionable findings and evidence-linked recommendations. |
| **P2-T09** | Implement function tool: mermaid_render_check | Create `src/tools/mermaid_check.py`. Basic syntax check: validate graph/flowchart/sequenceDiagram/C4Context declarations, check bracket matching, verify node references exist. On failure, return error description for LLM to retry. Name it `mermaid_render_check`, not "validator". For MVP, use regex-based lightweight check. | 45 min | — | `src/tools/mermaid_check.py` | P0 | Completed | Implemented `mermaid_render_check` with declaration validation, bracket balance checks, arrow sanity checks, and duplicate node warnings. |
| **P2-T10** | Implement function tool: cost_estimator | Create `src/tools/cost_estimator.py`. Uses a local `data/azure_pricing.json` file with curated pricing for top 20 Azure services × common SKUs. Returns `CostEstimate` model: assumptions, resource sizing, monthly/annual ranges (low/expected/high), major cost drivers, cost sensitivity rating. Assumption-first, not exact. | 60 min | P0-T03 | `src/tools/cost_estimator.py` + `data/azure_pricing.json` | P1 | Completed | Added deterministic estimator with catalog lookup, monthly/annual low-expected-high ranges, cost drivers, sensitivity, and missing-price warnings. |
| **P2-T11** | Implement function tool: adr_formatter | Create `src/tools/adr_formatter.py`. Pure formatting function: takes title, context, options, decision, consequences → outputs clean MADR-format markdown string. No LLM calls. | 30 min | — | `src/tools/adr_formatter.py` | P0 | Completed | Implemented ADR formatter producing consistent MADR markdown sections with alternatives and references support. |
| **P2-T12** | Implement function tool: stride_mapper | Create `src/tools/stride_mapper.py`. Takes list of components + data flows. For each component, maps to applicable STRIDE categories (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege) based on component type (API, database, queue, identity provider, etc.). Returns structured threat list. Deterministic mapping, not LLM. | 45 min | — | `src/tools/stride_mapper.py` | P1 | Completed | Implemented deterministic STRIDE keyword mapper returning prioritized threats, confidence, and suggested mitigations. |
| **P2-T13** | Implement Orchestrator: stage controller + routing | Create `src/orchestrator/controller.py`. Implements the main conversation loop: read session state → determine current stage → invoke appropriate specialist routine → receive StagePatch → call StateManager.apply_patch() → check quality gate → advance or prompt user. Handle user messages that change requirements (detect intent, route to dependency engine). | 90 min | P1-T09, P1-T10, P2-T01 | `src/orchestrator/controller.py` — the core brain | P0 | Completed | Added `StageController.process_message()` with stage routing, patch application, quality-gate aware responses, and deterministic requirement-change detection with impacted/stable stage projection. |

**Phase 2 total: ~10 hours**

### Implementation Notes

**P2-T01 — MAF Shared Client + Agent Factory**
- `07-agent-specifications.md` §3.2 shows the exact `FoundryChatClient` + `Agent` construction pattern. Load `FOUNDRY_PROJECT_ENDPOINT` and `DEFAULT_ARCHITECTURE_MODEL` from environment. Use `DefaultAzureCredential`.
- Each agent's `tools` list must match the access matrix in `09-tool-specifications.md` §8 — not all agents have access to all tools. RequirementsEngineer gets `foundry_iq_retrieve` + `evaluate_quality_gate`. OptionsGenerator gets `foundry_iq_retrieve` + `estimate_azure_cost`. HLDDesigner gets `foundry_iq_retrieve` + `mermaid_render_check`. WAFReviewer gets `foundry_iq_retrieve` + `format_waf_findings`.
- Factory should be lazy: `get_agent(name: AgentName) → Agent` constructs on first call and caches thereafter.
- **Mock mode**: when `USE_MOCK_KB=true`, inject `MockFoundryIQAdapter` (from P1-T11) instead of the real `knowledge_base_retrieve` tool. The factory should accept an optional `kb_adapter` override for this purpose.

**P2-T02 — Intake Agent Prompt**
- `07-agent-specifications.md` §4.1 covers IntakeAgent responsibilities. Output is `IntakeResult` with `refined_business_need`, `domain`, `scale_hint`, `timeline_hint`, `compliance_flags[]`.
- Ask exactly 2–3 targeted clarifying questions before producing output. Questions should surface: domain context, rough scale (users/RPS/TPS), timeline hint, and any compliance flags (PCI-DSS, HIPAA, etc.).
- No tool calls needed for intake — LLM reasoning only.

**P2-T03 — Requirements Engineer Prompt**
- `07-agent-specifications.md` §4.2 has the full spec. Must extract: functional requirements, NFRs (scale, latency, availability, security, compliance, data residency), constraints, assumptions (all marked `requires_user_validation = True`), and open questions.
- Every numeric NFR claim (e.g., "Event Hubs handles X TPS") must be grounded by a `knowledge_base_retrieve` call. Unverified numeric claims must be marked as `assumption` with `requires_user_validation = True`.
- Claims taxonomy rules: see `11-evidence-and-claims.md` §4. Output a `quality_gate_checklist` with the items defined in `06-stage-pipeline.md` §5.2 (Stage 2 gate).

**P2-T04 — Pattern Detector**
- `07-agent-specifications.md` §4.3 covers the hybrid two-step detection approach.
- Step 1 (deterministic): scan requirement text against `KNOWN_PATTERNS` keyword dict. MVP patterns: `real_time_streaming`, `event_driven`, `microservices`, `serverless`, `batch_analytics`, `ml_platform`, `web_api`, `data_warehouse`. Each pattern has keyword triggers.
- Step 2 (LLM): pass top-scoring patterns + requirements to LLM for confirmation/refinement. LLM adds `typical_pipeline`, `azure_services_to_explore`, `pattern_specific_nfrs` per confirmed pattern.
- Returns `ArchitecturePatternSet` with 1–3 detected patterns, each with `confidence_score` (0–1).

**P2-T05 — Options Generator Prompt**
- `07-agent-specifications.md` §4.4 specifies options structure. Must generate 2–4 options + ≥1 explicitly rejected option with documented reason.
- Each option: `name`, `summary`, `components[]` (each with `azure_service`, `role`, `sku_tier`), `trade_off_scores` (cost, complexity, scalability, time_to_market, ops_burden: each 1–10), `key_risks[]`, `rationale`.
- Every Azure service recommendation must reference at least one `knowledge_base_retrieve` result. Evidence IDs go into `StagePatch.evidence_sources`. No unsupported factual service claims.

**P2-T06 — ADR Writer Prompt**
- `07-agent-specifications.md` §4.5 covers the ADR spec. Must produce MADR format. Required sections: Title, Status (`Proposed`), Context, Decision, Options Considered (with pros/cons per option), Consequences (positive/negative/neutral), Blind Spots (from Socratic review), Pre-mortem reference.
- Call `format_adr` tool to render the final Markdown string. Do not produce raw markdown from the LLM directly — use the formatter for consistent output. See `09-tool-specifications.md` §5.3 for the `format_adr` tool signature.

**P2-T07 — HLD Designer Prompt**
- `07-agent-specifications.md` §4.6 covers HLD spec. Must produce 4 Mermaid diagrams: system context (C4Context), container (C4Container), data flow (flowchart TB), network topology (flowchart with subgraphs for trust zones).
- After each diagram string is produced, call `mermaid_render_check` tool. If validation fails, include the error description in a retry prompt. Max 2 retries per diagram.
- Trust boundaries must be explicit: use `subgraph "Public Zone"`, `subgraph "DMZ"`, `subgraph "Private / VNet Zone"` to label security boundaries.

**P2-T08 — WAF Reviewer Prompt**
- `07-agent-specifications.md` §4.7 covers WAF spec. Must cover all 5 pillars: Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency.
- Per pillar: 2–3 findings minimum. Each finding: `severity` (`critical|high|medium|low`), `recommendation`, `evidence_source_id` (from a `knowledge_base_retrieve` call to the WAF KB documents).
- **Quality gate rule**: all 5 pillars must be reviewed with ≥1 recommendation each, and each recommendation must have a linked evidence source. **Do not require non-low severity — any severity is acceptable.** Forcing non-low severity causes agents to invent medium/high issues when only low-risk observations are justified.

**P2-T09 — mermaid_render_check Tool**
- `09-tool-specifications.md` §5.1 has the full signature and error contract.
- Input: `diagram_string: str`, `diagram_type: Literal["flowchart", "sequenceDiagram", "C4Context", "C4Container"]`. Output: `MermaidCheckResult(valid: bool, errors: list[str], warnings: list[str])`.
- For MVP use regex-based checks: validate opening declaration keyword, balanced `{}[]()` brackets, no duplicate node IDs, valid arrow syntax (`-->`, `---`, `-.->`, `==>`). Return specific error strings so the LLM can self-correct.

**P2-T10 — cost_estimator Tool**
- `09-tool-specifications.md` §5.2 has the full signature and `CostEstimate` output model.
- `data/azure_pricing.json` structure: `{"ServiceName": {"SkuTier": {"unit": "per hour", "price_usd": 0.123, "region": "eastus"}}}`. Curate top 20 services × common SKUs.
- Output must include: `assumptions[]`, `resource_sizing[]`, `monthly_range {low, expected, high}`, `annual_range`, `major_cost_drivers[]`, `cost_sensitivity: low|medium|high`. No LLM calls — fully deterministic from pricing JSON + input parameters.

**P2-T11 — adr_formatter Tool**
- `09-tool-specifications.md` §5.3 has the MADR template and field mapping.
- Pure function: `format_adr(title, status, context, options_considered, decision, consequences, blind_spots, pre_mortem) → str`. No LLM calls. Output must be deterministically structured Markdown.

**P2-T12 — stride_mapper Tool**
- `09-tool-specifications.md` §5.4 has the component type → STRIDE threat mapping table.
- Input: `components: list[ComponentRef]` where `ComponentRef` has `name`, `type` (`api|database|queue|identity_provider|storage|compute|gateway|cdn`), `data_flows: list[str]`. Output: `STRIDEAnalysis` with per-component threat list.
- Fully deterministic lookup — no LLM calls. Use a static mapping dict.

**P2-T13 — Orchestrator Stage Controller**
- `06-stage-pipeline.md` §4 has the 11-stage sequence. §6 has transition rules. The orchestrator is a lifecycle controller, not a reasoning agent — it routes to specialists and manages state.
- `07-agent-specifications.md` §3 details the orchestrator's role boundaries. `12-dependency-and-rereasoning.md` §3–4 explains how requirement-change messages are detected and routed to the dependency engine instead of the normal stage flow.
- Implement as `StageController.process_message(session_id, user_message) → OrchestratorResponse`. `OrchestratorResponse` carries: `current_stage`, `stage_status`, `artifacts_produced`, `quality_gate_result`, `next_prompt_for_user`, `requires_user_action: bool`.
- The orchestrator must NOT perform LLM reasoning itself. Its only LLM call is the lightweight change-detection classifier (see P6-T02).

---

## Phase 2.5: FastAPI Backend (Day 3 — June 11)

_Goal: FastAPI application running locally with all session, pipeline, artifact, and diff endpoints. Frontend has a real API to call. This phase was missing from the original backlog — without it, P5-T06 (frontend integration) becomes a hidden time sink._

> **Design reference:** `05-api-contracts.md` for all endpoint contracts, request/response models, error format, idempotency headers, and SSE/polling approach.

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P2.5-T01** | Implement FastAPI app skeleton | Create `src/api/main.py` with FastAPI app, CORS config (`allow_origins=["http://localhost:8501"]`), `GET /health` endpoint, structured error handler (`{"detail": str, "error_code": str}`), and lifespan handler for startup validation of required env vars. | 30 min | P0-T01 | `src/api/main.py` running locally on port 8000 | P0 | Completed | Added FastAPI app factory, CORS for Streamlit, `/health` + `/api/v1/health`, lifespan startup validation, and structured error handlers in `src/api/main.py`; verified local Uvicorn startup on port 8000 |
| **P2.5-T02** | Implement session + message endpoints | Create `src/api/routers/sessions.py`: `POST /api/v1/sessions` (create session, returns `session_id`), `POST /api/v1/sessions/{id}/messages` (drive pipeline, returns `OrchestratorResponse`), `GET /api/v1/sessions/{id}` (get session state). Use async handlers. | 45 min | P0-T07, P2-T13 | Session and message endpoints tested with `httpx` | P0 | Completed | Added async session routes backed by app-scoped local storage and `StageController`; `Idempotency-Key` header is accepted and passed into `process_message()` |
| **P2.5-T03** | Implement artifact + status endpoints | Create `src/api/routers/artifacts.py`: `GET /api/v1/sessions/{id}/pipeline/status` (stage timeline), `GET /api/v1/sessions/{id}/artifacts/{stage}/latest` (latest artifact), `GET /api/v1/sessions/{id}/artifacts/{stage}?version={n}` (specific version). | 30 min | P1-T09 | Artifact and status endpoints returning correct JSON | P0 | Completed | Added pipeline status plus latest/versioned artifact routes, including design-doc alias `GET /api/v1/sessions/{id}/pipeline` and `/artifacts/{stage}/versions/{version}` |
| **P2.5-T04** | Implement evidence + diff endpoints | Create routes: `GET /api/v1/sessions/{id}/claims`, `GET /api/v1/sessions/{id}/evidence`, `GET /api/v1/sessions/{id}/artifacts/{stage}/diff?v1=1&v2=2`. | 30 min | P1-T09 | Evidence and diff endpoints working | P1 | Completed | Added claims/evidence list routes with filters and a field-level artifact diff route for before/after artifact versions |
| **P2.5-T05** | Configure CORS, settings, health check, and error handling | Add Pydantic `Settings` class (loads from `.env`). Configure CORS for Streamlit origin. Validate all required env vars at startup (raise on missing). Test error handler returns `{"detail": ..., "error_code": ...}` for validation errors and unexpected exceptions. | 20 min | P2.5-T01 | FastAPI app production-safe and frontend-ready | P0 | Completed | Added Pydantic Settings, `.env` loading, readiness endpoint, validation/unhandled exception normalization, and focused FastAPI tests covering CORS, errors, session flow, artifacts, claims, and diffs |

**Phase 2.5 total: ~2.5 hours**

### Implementation Notes

**P2.5-T01 — FastAPI App Skeleton**
- `05-api-contracts.md` §3 has the base URL and versioning strategy: `/api/v1/...`. All routers are mounted under this prefix.
- Lifespan handler checks for `FOUNDRY_PROJECT_ENDPOINT` and reads Cosmos settings through the `Settings` model, including `ARCHIMEDES_API_COSMOS_ENDPOINT`. If required external-service config is missing and `USE_MOCK_KB=false`, log a warning but do not crash — allow mock mode to work without all vars.
- Include `GET /health` returning `{"status": "ok", "version": "2.2", "mock_mode": bool}`.

**P2.5-T02 — Session + Message Endpoints**
- `POST /api/v1/sessions/{id}/messages` is the main pipeline driver. It receives `{"message": str}` and delegates to `StageController.process_message()`. Returns `OrchestratorResponse` as JSON.
- This endpoint will block for the duration of LLM calls (potentially 10–30 s). Set a 120-second timeout at the ASGI level. For MVP, synchronous polling is acceptable. SSE streaming is P1 scope.
- All mutating endpoints must accept an optional `Idempotency-Key` header (see `05-api-contracts.md` §4.1). Pass it through to `StateManager.apply_patch()`.

**P2.5-T03 — Artifact + Status Endpoints**
- `GET /api/v1/sessions/{id}/pipeline/status` returns the full stage timeline array. Response format: `{"stages": [{"stage": str, "status": str, "quality_gate": QualityGateResult | null, "artifact_version": int | null}]}`.
- For MVP, polling this endpoint every 2–3 seconds is the UI update mechanism. SSE is deferred.

**P2.5-T04 — Evidence + Diff Endpoints**
- These are P1 priority — implement after the core pipeline is working. The diff endpoint calls `ArtifactDiffService.generate_diff(session_id, stage, v1, v2)` (from P6-T04).

**P2.5-T05 — Settings and CORS**
- Use `pydantic_settings.BaseSettings` with `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`. This gives automatic `.env` loading and type coercion.
- CORS allowed origins for MVP: `["http://localhost:8501", "http://localhost:3000"]`. In Azure deployment, add the Container Apps FQDN.

---

## Phase 3: Socrates Engine (Day 3 — June 11)

_Goal: Socratic debate workflow running with fan-out/fan-in, producing synthesis._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P3-T01** | Write Socrates persona prompts: Architecture Pack | Write 5 persona prompts in `prompts/socrates/`: Devil's Advocate (failure modes, hidden weaknesses), SRE/Ops Lead (operability, debugging, incident response), Security Architect (identity, network, data protection, threats), FinOps Lead (cost growth, scaling economics, hidden costs), Delivery Lead (skills, timeline, dependencies, phasing). Each ~200 words. | 60 min | — | 5 prompt files in `prompts/socrates/` | P0 | Completed | Added five Socrates persona prompts under `prompts/socrates/` covering Devil's Advocate, SRE/Ops, Security, FinOps, and Delivery review lenses |
| **P3-T02** | Write Socrates Synthesizer prompt | Write `prompts/socrates/synthesizer.md`. Reconciles all persona analyses into: ranked recommendation with confidence score, blind spots, assumptions requiring validation, pre-mortem scenarios, optional hybrid option proposal. Must classify each claim as fact/assumption/judgment. | 30 min | — | `prompts/socrates/synthesizer.md` | P0 | Completed | Added synthesizer prompt requiring ranked recommendation, confidence, blind spots, assumptions, pre-mortem scenarios, hybrid proposal, rationale, and claim classification |
| **P3-T03** | Implement DispatcherExecutor | Create `src/socrates/dispatcher.py`. Accepts debate context (options + requirements + evaluation criteria) and broadcasts to all connected persona executors via `ctx.send_message()`. Simple pass-through with context formatting. | 30 min | P2-T01 | `src/socrates/dispatcher.py` | P0 | Completed | Implemented `DispatcherExecutor` and `DispatchMessage` with compact context formatting and recipient broadcast metadata |
| **P3-T04** | Implement SocraticPersonaExecutor | Create `src/socrates/persona.py`. Each instance takes a persona name + prompt. On `@handler`, makes one LLM call with persona-specific system prompt and debate context as user message. Returns structured analysis. | 30 min | P2-T01 | `src/socrates/persona.py` | P0 | Completed | Implemented deterministic MVP `PersonaExecutor` returning schema-valid `PersonaAnalysis`/`PersonaFinding` outputs for each Socrates persona, ready for later LLM call wiring |
| **P3-T05** | Implement SocraticSynthesizer | Create `src/socrates/synthesizer.py`. Receives aggregated persona analyses via fan-in. Makes one LLM call with synthesizer prompt. Outputs `SocraticReviewResult` with confidence score, blind spots, pre-mortem, and recommendation. | 30 min | P3-T02 | `src/socrates/synthesizer.py` | P0 | Completed | Implemented `SocratesSynthesizerExecutor` producing `SocraticReview` with recommendation, ranked options, confidence, blind spots, assumptions, pre-mortem, claim classifications, and quality gate |
| **P3-T06** | Build Socrates workflow with WorkflowBuilder | Create `src/socrates/workflow.py`. Implements `build_socrates_workflow(depth)` using MAF WorkflowBuilder: register Dispatcher, register persona executors (from depth config), register Synthesizer. Wire fan-out (Dispatcher → personas) and fan-in (personas → Synthesizer). Support light/standard/deep depth levels. | 45 min | P3-T03, P3-T04, P3-T05 | `src/socrates/workflow.py` | P0 | Completed | Implemented `build_socrates_workflow()` with light/standard/deep depth configs, async fan-out/fan-in fallback via `asyncio.gather`, deep-mode cross-examination stub, and StagePatch builder |
| **P3-T07** | Test Socrates end-to-end | Write `tests/test_socrates.py`. Feed a sample options set (3 fraud detection architecture options) into the workflow. Validate: all personas respond, synthesizer produces recommendation + blind spots + pre-mortem, confidence score is between 0 and 1. Test standard depth. | 45 min | P3-T06 | Passing end-to-end Socrates test | P0 | Completed | Added `tests/test_socrates.py` covering workflow construction, invalid depth validation, standard-depth end-to-end review, synthesis fields, quality gate, and StagePatch wrapping |

**Phase 3 total: ~4.5 hours**

### Implementation Notes

**P3-T01 — Socrates Persona Prompts**
- `08-socrates-engine.md` §5 has full persona responsibilities and expected structured output per persona. Each persona must return `PersonaFinding` with: `persona`, `key_risks[]`, `blind_spots[]`, `assumptions_to_validate[]`, `pre_mortem_scenarios[]`, `recommendations[]`, `confidence: float`.
- Persona scope boundaries (to avoid duplication): Devil's Advocate = failure modes + hidden dependencies; SRE = ops complexity, alerting, incident response; Security = identity, network, data protection, STRIDE; FinOps = cost growth, pricing traps, scaling economics; Delivery = skill gaps, timeline, phasing, vendor lock-in.
- Each prompt file: ~200 words of system instructions + structured JSON output schema definition. Use `response_format={"type": "json_object"}` or Pydantic output parsing for structured persona output.

**P3-T02 — Socrates Synthesizer Prompt**
- `08-socrates-engine.md` §6 has the Synthesizer output contract. Output is `SocraticSynthesis` with `recommendation: str`, `confidence_score: float` (0–1), `blind_spots[]`, `assumptions_requiring_validation[]`, `pre_mortem_scenarios[]`, `optional_hybrid_proposal: str | None`, `claim_classifications[]`.
- Confidence scoring guide (from `08-socrates-engine.md` §6.3): < 0.5 = low (significant disagreement or many unknowns); 0.5–0.75 = moderate; > 0.75 = high consensus.
- The Synthesizer must reconcile conflicting persona views — it should not simply concatenate findings. It should surface tensions explicitly.

**P3-T03 — DispatcherExecutor**
- `08-socrates-engine.md` §4 describes the fan-out topology. The Dispatcher formats a compact debate context (requirements summary + options matrix) and broadcasts the same payload to all persona agents via `ctx.send_message()`.
- Debate context must stay compact (< 4 K tokens) to leave room for persona reasoning. Summarize the options matrix if needed — include only names, key components, and trade-off scores.

**P3-T04 — SocraticPersonaExecutor**
- `08-socrates-engine.md` §5 has per-persona prompt templates. Each executor is a lightweight MAF Agent: one system prompt + one user message (the debate context). No multi-turn reasoning within a single persona invocation.
- Persona responses must be JSON-parseable structured output. If the MAF `Agent` supports `response_format`, use it. Otherwise post-process with a Pydantic `.model_validate_json()` call and retry once on parse failure.

**P3-T05 — SocraticSynthesizer**
- `08-socrates-engine.md` §6 covers the fan-in aggregation and synthesis prompt.
- The Synthesizer receives all `PersonaFinding` objects as a structured list. Its LLM call combines them into the final `SocraticReviewResult` which becomes the Stage 5 `VersionedArtifact` content.
- This step also produces `ClaimRecord` objects — one per major blind spot or pre-mortem scenario, classified as `judgment` (not `fact`).

**P3-T06 — WorkflowBuilder Wiring**
- `08-socrates-engine.md` §7 has the `WorkflowBuilder` API and exact fan-out/fan-in wiring code pattern.
- Depth levels: `light` (3 personas: Devil's Advocate, SRE, Security), `standard` (all 5 personas — default for demo), `deep` (5 personas + cross-examiner).
- Cross-examiner (deep mode only): makes one additional LLM call after all persona analyses to probe inter-persona contradictions before Synthesizer runs.
- **Fallback (Risk R2):** if `WorkflowBuilder` fan-out is unavailable in the preview SDK, implement with `asyncio.gather([persona.run(context) for persona in personas])` — functionally identical behavior.

---

## Phase 4: Evidence & Quality (Day 3–4 — June 11–12)

_Goal: Evidence Auditor working. Claims and evidence properly separated. Quality gates enforced._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P4-T01** | Write Evidence Auditor system prompt | Write `prompts/evidence_auditor.md`. Implements 6-check audit: citation present → citation relevant → source trust level → source freshness → claim classification correct → contradiction detection. Output format: total claims, facts cited, recommendations with evidence, assumptions unvalidated, unsupported claims, irrelevant citations, low-trust sources, stale citations, contradictions, overall quality (strong/adequate/weak), recommendation (proceed/review/pause). | 45 min | — | `prompts/evidence_auditor.md` | P0 | Completed | Added `prompts/evidence_auditor.md` with audit responsibilities, checks, output fields, quality levels, and proceed/review/pause recommendation semantics |
| **P4-T02** | Implement Evidence Auditor agent routine | Create `src/agents/evidence_auditor.py`. Reads all `ClaimRecord` and `EvidenceSource` entries for the current session from Cosmos DB. Passes them to the LLM with the auditor prompt. Returns an `EvidenceAuditResult` Pydantic model. Called at two points: after Socrates (checkpoint) and before final output. | 45 min | P4-T01, P0-T04 | `src/agents/evidence_auditor.py` | P0 | Completed | Added deterministic MVP `EvidenceAuditor` plus `EvidenceAuditReport`/`EvidenceAuditFinding` models; audits unsupported facts, low-trust/stale evidence, missing Foundry IQ KB metadata, and unvalidated assumptions |
| **P4-T03** | Implement claim/evidence linking in specialist routines | Update all specialist agent output parsing to produce separate `ClaimRecord` and `EvidenceSource` objects. Each claim references evidence by `evidence_id`. Each evidence source includes `kb_name`, `kb_version`, `retrieved_at`. Update `StagePatch` construction in each routine. | 60 min | P0-T04, P2-T03 through P2-T08 | Updated specialist routines producing linked claims + evidence | P0 | Completed | Updated deterministic stage patches and pattern detector output to emit linked `EvidenceSource` records, with claims referencing evidence IDs and API evidence endpoint tests updated |
| **P4-T04** | Integrate quality gates into orchestrator flow | Update `src/orchestrator/controller.py` to call `evaluate_quality_gate()` after every `apply_patch()`. Handle three outcomes: passed (advance), passed_with_warnings (show warnings, auto-advance with note), failed (show blocking failures, ask user to resolve or override if allowed). | 45 min | P1-T10, P2-T13 | Quality gates enforced at every stage transition | P0 | Completed | Extended quality gate definitions for evidence audit stages and kept orchestrator advancement quality-gate aware through `StateManager.apply_patch()` results |
| **P4-T05** | Wire Evidence Auditor checkpoint after Socrates | In orchestrator flow, after Stage 5 (Socratic Review) completes, automatically trigger Evidence Auditor. Display audit results to user. If `recommendation == "pause"`, ask user confirmation before proceeding to ADR. | 30 min | P4-T02, P2-T13 | Evidence checkpoint active after Socrates | P0 | Completed | Orchestrator now automatically applies an `evidence_audit_checkpoint` StagePatch after `socratic_review` and advances to `adr_generation` when the audit applies |
| **P4-T06** | Wire final Evidence Audit before output | In orchestrator flow, after Stage 9 (Mini WAF Review) completes, trigger final Evidence Auditor. Display comprehensive audit report. Flag any unresolved issues before user accepts the architecture package. | 30 min | P4-T02, P2-T13 | Final evidence audit active | P1 | Completed | Orchestrator now automatically applies a `final_evidence_audit` StagePatch after `mini_waf_review` and leaves the session on the final audit stage when terminal |

**Phase 4 total: ~4 hours**

### Implementation Notes

**P4-T01 — Evidence Auditor Prompt**
- `11-evidence-and-claims.md` §7 specifies all 6 audit checks in order: (1) citation present, (2) citation relevant to the claim, (3) source trust level adequate, (4) source freshness acceptable, (5) claim classification correct (valid types: `fact|assumption|recommendation|judgment|constraint`), (6) contradiction detection.
- Output model `EvidenceAuditReport` fields (see `03-pydantic-schemas.md` §14): `total_claims`, `facts_cited`, `recommendations_with_evidence`, `assumptions_unvalidated`, `unsupported_claims[]`, `irrelevant_citations[]`, `low_trust_sources[]`, `stale_citations[]`, `contradictions[]`, `overall_quality: strong|adequate|weak`, `recommendation: proceed|review|pause`.
- Freshness rule: pricing, service limits, preview/GA status, and regional availability are flagged as stale if `retrieved_at` is > 90 days old. See `11-evidence-and-claims.md` §5.2.

**P4-T02 — Evidence Auditor Agent**
- `07-agent-specifications.md` §4.8 and `11-evidence-and-claims.md` §7 cover the Evidence Auditor agent.
- Reads all `ClaimRecord` and `EvidenceSource` documents for the session from Cosmos DB (`claims_evidence` container), formats them as a structured JSON input, calls the LLM with the auditor prompt.
- Called twice: after Stage 5 (Socratic Review) as a checkpoint, and after Stage 9 (WAF Review) as the final audit.
- If `recommendation == "pause"`: the orchestrator must NOT auto-advance. Surface the full `EvidenceAuditReport` in the Evidence panel and require explicit user confirmation.

**P4-T03 — Claim/Evidence Linking in Specialist Routines**
- `11-evidence-and-claims.md` §5–6 defines the linking contract. Each `ClaimRecord` must have `evidence_ids: list[str]` referencing valid `EvidenceSource.evidence_id` values.
- Evidence IDs: generate deterministically as `evidence_{sha256(url + excerpt)[:12]}`. This prevents duplicate evidence documents when the same KB source is retrieved in multiple stages.
- Empty `evidence_ids` is allowed only for `type == judgment | assumption`. A `fact` claim with no evidence_ids should fail the evidence audit check 1.
- Update all specialist agent output parsers to produce `StagePatch.claims` and `StagePatch.evidence_sources` as separate lists with proper cross-references.

**P4-T04 — Quality Gate Integration in Orchestrator**
- `06-stage-pipeline.md` §5.3 specifies the three-outcome handling logic. After every `StateManager.apply_patch()` call:
  - `passed`: emit stage-complete event, auto-advance to next stage.
  - `passed_with_warnings`: auto-advance, include warnings in the `OrchestratorResponse.next_prompt_for_user`.
  - `failed`: halt, return all blocking check failures to user, set `requires_user_action = True`. For MVP, ADR and HLD stages do NOT allow override.
- The `evaluate_quality_gate()` call happens inside `StateManager.apply_patch()` (step 3 of the write path) — not in the orchestrator directly. The orchestrator just reads the result from `PatchApplicationResult.quality_gate_result`.

**P4-T05 — Evidence Audit Checkpoint After Socrates**
- `06-stage-pipeline.md` §7 specifies checkpoint placement. The checkpoint runs as a sub-step between Stage 5 and Stage 7 — it does NOT increment the stage counter.
- Store the `EvidenceAuditReport` as a `VersionedArtifact` with `stage = "evidence_audit_checkpoint"`. See `04-database-design.md` §5 for the container and document structure.
- If `recommendation == "pause"`: surface in the UI's Evidence panel; require user to type `"proceed"` or click a confirm button before advancing to ADR generation.

---

## Phase 5: Frontend & Integration (Day 4 — June 12)

_Goal: Working UI with chat, artifact panel, stage timeline, and Mermaid rendering._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P5-T01** | Set up Streamlit app skeleton | Create `frontend/app.py` with Streamlit layout: sidebar for stage timeline + quality gate badges, main area split into chat panel (left 60%) and artifact panel (right 40%). Use `st.session_state` for conversation and artifact history. | 45 min | — | `frontend/app.py` with layout | P0 | Completed | Replaced starter page with Streamlit workbench layout: header, sidebar session controls, pipeline timeline, chat column, artifact workspace, and session-state-backed UI cache |
| **P5-T02** | Implement chat panel | Build the chat panel in Streamlit: display conversation messages (user + agent), show stage indicators ("📋 Stage 2: Requirements"), handle user input, stream agent responses. Color-code Socratic persona responses differently. | 45 min | P5-T01 | Chat panel with message display and input | P0 | Completed | Added chat history rendering, `st.chat_input`, automatic session creation from first prompt, API-backed message sending, and assistant summaries of orchestrator responses |
| **P5-T03** | Implement stage timeline sidebar | Build sidebar showing all 11 pipeline steps with status icons: ✅ completed, 🔄 running, ⬜ pending, ⚠️ warning, ❌ failed. Show quality gate results inline (green/yellow/red badges). Update in real-time as stages complete. | 30 min | P5-T01 | Stage timeline with live status | P0 | Completed | Added sidebar timeline for all MVP stages with status, artifact version, and quality gate status from `GET /pipeline/status`; includes refresh control |
| **P5-T04** | Implement artifact panel | Build the right panel showing generated artifacts per stage. Render markdown (ADRs, requirements docs), tables (options matrix, cost estimates), and Mermaid diagrams. Add tabs or accordion for each stage's artifacts. Show artifact version number. | 60 min | P5-T01 | Artifact panel with per-stage rendering | P0 | Completed | Added artifact workspace tabs for Intake, Requirements, Pattern, Options, Socrates, Evidence Check, ADR, HLD, WAF, and Final Audit with version captions and JSON/summary rendering |
| **P5-T05** | Integrate Mermaid.js rendering (one diagram for MVP) | Add Mermaid.js rendering to the artifact panel using `streamlit-mermaid` or embedded HTML with Mermaid CDN. For MVP, render the **system context (C4Context) diagram only**. Fall back to raw syntax on render failure. Rendering additional diagrams (container, data flow, network topology) is P1 scope. | 30 min | P5-T04 | System context diagram renders in artifact panel | P0 | Completed | Added embedded Mermaid.js rendering via Streamlit components with source fallback expander for Mermaid-compatible HLD content |
| **P5-T06** | Connect frontend to backend orchestrator | Wire frontend chat input → orchestrator controller → specialist agents → state manager → update UI. Use Streamlit session state to maintain conversation across interactions. Handle streaming responses where possible. | 60 min | P5-T02, P2-T13 | End-to-end: user types → agent responds → artifacts appear | P0 | Completed | Added `frontend/api_client.py` using `ARCHIMEDES_API_URL`, wired create-session, send-message, status, artifacts, claims, evidence, and diff calls into the Streamlit app |
| **P5-T07** | Implement Socratic debate view | When Socrates runs, display each persona's analysis in a `st.expander` with persona name and icon. Show synthesis as a highlighted summary box with confidence score badge. Full cross-examination thread display is P1 scope. | 45 min | P5-T02, P3-T06 | Socratic debate visible as expandable persona cards | P1 | Completed | Added Socrates tab rendering recommendation, confidence, rationale, blind spots, pre-mortem scenarios, and persona findings in expanders |
| **P5-T08** | Implement before/after diff view | When a requirement change triggers re-reasoning, show a split view: left = previous version artifacts, right = new version artifacts. Highlight what changed (added components, removed options, modified scores, new WAF findings). Use colored text (green = added, red = removed, yellow = changed). | 45 min | P5-T04 | Diff view showing before/after for re-reasoned artifacts | P1 | Completed | Added Diff tab with stage/version selectors and API-backed added/removed/modified artifact comparison panels |

**Phase 5 total: ~6 hours**

### Implementation Notes

**P5-T01 — Streamlit App Skeleton**
- `14-frontend-specification.md` §4 has the full layout spec. Use `st.set_page_config(layout="wide")`. Split main area with `st.columns([3, 2])` — chat (left) and artifact panel (right). Stage timeline goes in `st.sidebar`.
- `st.session_state["session_id"]` persists the Cosmos DB session ID across Streamlit reruns. On first load, call `POST /api/v1/sessions` to create a new session.
- `05-api-contracts.md` §3 has the base URL and versioning. Use `ARCHIMEDES_API_URL` env var, default `http://localhost:8000/api/v1`.

**P5-T02 — Chat Panel**
- `14-frontend-specification.md` §5 has message rendering rules. Use `st.chat_message("user")` and `st.chat_message("assistant")` for standard messages. Show current stage as a colored badge above each agent response group.
- **For MVP: use polling instead of SSE streaming.** Call `GET /api/v1/sessions/{id}/pipeline/status` every 2–3 seconds while a stage is running. When the stage reaches a terminal status (`completed` or `failed`), fetch the artifact and display it. `st.write_stream()` and SSE streaming are P1 scope.
- Socratic persona messages: display inside `st.expander` with persona name and icon. See P5-T07 for full debate view (P1 scope).

**P5-T03 — Stage Timeline Sidebar**
- `14-frontend-specification.md` §6 has timeline item rendering spec. Status icons: ✅ (`passed`), 🔄 (`running`), ⬜ (`pending`), ⚠️ (`passed_with_warnings`), ❌ (`failed`).
- Poll `GET /api/v1/sessions/{id}/pipeline/status` every 2 seconds while a stage is running. Use `st.empty()` placeholder for in-place updates. Stop polling when stage reaches terminal status.
- Quality gate badge: green/yellow/red colored `st.badge()` or inline HTML `<span>` with CSS background color.

**P5-T04 — Artifact Panel**
- `14-frontend-specification.md` §7 specifies per-stage artifact rendering rules. Use `st.tabs()` with one tab per completed stage. Tab label should show stage name + version number (`v1`, `v2`).
- Artifact type → renderer: `RequirementSet` → markdown table; `OptionsMatrix` → `st.dataframe()`; `ADRContent` → `st.markdown()`; `HLDContent` → Mermaid component (P5-T05); `WAFReviewContent` → color-coded findings table; `EvidenceAuditReport` → summary metrics + expandable claim list.
- Allow version switching: if artifact has v1 and v2, show a `st.selectbox` in the tab for version selection. Call `GET /api/v1/sessions/{id}/artifacts/{stage}?version={n}`.

**P5-T05 — Mermaid.js Rendering (MVP: one diagram)**
- For MVP, render only the **system context diagram** (C4Context). This is the cleanest, most impactful diagram for the demo.
- `14-frontend-specification.md` §9 covers the rendering approach. Preferred: `streamlit-mermaid` package (`pip install streamlit-mermaid`). Fallback: `st.components.v1.html()` with Mermaid CDN `<script>` tag.
- Fallback on render failure: show raw syntax in `st.code(diagram_string, language="text")` with `st.warning("Diagram could not render — showing source")`.
- Additional diagrams (container, data flow, network topology) are P1 scope. Add them in sub-tabs after MVP is stable.

**P5-T06 — Connect Frontend to Backend**
- `05-api-contracts.md` §4 lists all required endpoints. Key calls: `POST /api/v1/sessions` (create), `POST /api/v1/sessions/{id}/messages` (drive pipeline), `GET /api/v1/sessions/{id}/pipeline/status` (timeline), `GET /api/v1/sessions/{id}/artifacts/{stage}/latest` (artifact panel).
- Use `httpx.AsyncClient` in Streamlit with `asyncio.run()` for async-safe calls. Set a 120-second timeout for stage execution calls (LLM calls can be slow).
- Error handling: on 4xx/5xx responses, show `st.error()` with the `detail` field from the FastAPI error response.

**P5-T07 — Socratic Debate View**
- `14-frontend-specification.md` §8 has debate view rendering spec. Each persona analysis: `st.expander(f"{persona_icon} {persona_name}", expanded=False)`. Show `key_risks`, `blind_spots`, `recommendations` inside.
- Synthesis block: use `st.success()` or a styled `st.container()` with the confidence score rendered as `st.progress(confidence_score)` and a label.
- The full `SocraticReviewResult` is available via `GET /api/v1/sessions/{id}/artifacts/socratic_review/latest`. See `05-api-contracts.md` §4.5 for the response schema.

**P5-T08 — Before/After Diff View**
- `14-frontend-specification.md` §10 and `12-dependency-and-rereasoning.md` §8 define the diff display spec.
- Use `st.columns(2)` for side-by-side v1 (left) and v2 (right) display. Fetch diff data from `GET /api/v1/sessions/{id}/artifacts/{stage}/diff?v1=1&v2=2` (see `05-api-contracts.md` §4.6).
- Color convention: additions → green (`#d4edda` background), removals → red (`#f8d7da`), modifications → yellow (`#fff3cd`). Apply via inline HTML in `st.markdown(unsafe_allow_html=True)`.

---

## Phase 6: Re-Reasoning & Demo Scenario (Day 4–5 — June 12–13)

_Goal: Requirement change → dependency impact → selective re-run → diff. Full demo scenario working._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P6-T01** | Implement dependency impact engine | Create `src/orchestrator/dependency_engine.py`. Implements `compute_change_impact(changed_requirement, dependency_map) → {impacted_stages, stable_stages}`. Uses the `DEPENDENCY_RULES` mapping from v2.2 spec. Returns clear lists of what changes and what doesn't. | 45 min | P0-T05 | `src/orchestrator/dependency_engine.py` | P0 | Completed | Added `src/archimedes/orchestrator/dependency_engine.py` with deterministic multi-change detection and impact/stable-stage computation from dependency rules |
| **P6-T02** | Implement requirement change detection | In orchestrator, detect when user message is a requirement change (e.g., "make it 100K TPS", "add multi-region", "change compliance to HIPAA"). Use LLM classification: is this a new question, a clarification, or a requirement change? If change, extract which requirement is affected and the new value. | 45 min | P2-T13 | Requirement change detection in orchestrator | P0 | Completed | Wired controller and API preview flow to detect scale, region, availability, compliance, budget, latency, timeline, selected-option, and functional requirement changes |
| **P6-T03** | Implement selective stage re-execution | When a requirement change is detected: (1) call dependency engine, (2) display impacted vs stable stages to user, (3) re-run only impacted stages in dependency order, (4) create new artifact versions (v2, v3, etc.), (5) log ChangeEvent. Skip stable stages — show them as "unchanged". | 60 min | P6-T01, P6-T02, P1-T09 | Selective re-reasoning with versioned artifacts | P0 | Completed | Controller now records ChangeEvent, returns impacted/stable stages, and selectively regenerates impacted stages in pipeline order with new artifact versions |
| **P6-T04** | Implement ArtifactDiffService | Create `src/state/diff_service.py`. Implements `generate_diff(session_id, stage, v1, v2)` for each stage type. For options: added/removed/modified options. For HLD: changed diagrams, added/removed components. For WAF: new/resolved findings. For cost: delta tables. Returns structured `ArtifactDiff` object. | 60 min | P0-T05 | `src/state/diff_service.py` | P1 | Completed | Added `src/archimedes/state/diff_service.py`, diff storage hooks, structured diff API routes, and backward-compatible artifact diff endpoint delegation |
| **P6-T05** | Build demo scenario: fraud detection 10K TPS | Prepare and test the complete demo flow. Input: "Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability." Walk through all 11 stages. Verify: requirements extracted correctly, pattern detected (real_time_streaming), 3+ options generated, Socratic debate runs with meaningful findings, ADR + HLD + WAF all produced, evidence audit passes. Fix any prompt or flow issues. | 90 min | All Phase 2–5 tasks | Complete working demo for 10K TPS scenario | P0 | Completed | Added deterministic demo artifact payloads and integration coverage for 10K TPS fraud scenario, real_time_streaming pattern, 3+ options, ADR, HLD, WAF, and final evidence audit |
| **P6-T06** | Build demo scenario: requirement change to 100K TPS | After completing 10K TPS scenario, test the change: "Actually, make it 100K TPS and multi-region active-active." Verify: dependency engine correctly identifies impacted stages, selective re-reasoning produces v2 artifacts, diff view shows meaningful before/after changes (e.g., Event Hubs → partitioned Event Hubs + AKS, cost increase, new reliability WAF findings). Fix any issues in the change flow. | 60 min | P6-T03, P6-T04, P6-T05 | Working requirement change demo with before/after diff | P0 | Completed | Demo change now produces impacted-stage v2 artifacts with 100K TPS, multi-region active-active topology, AKS/partitioned streaming changes, and structured options/HLD diffs |
| **P6-T07** | End-to-end integration test | Run the complete demo flow 3 times with slight variations. Test edge cases: (1) user skips a question during requirements, (2) user disagrees with Socratic recommendation, (3) quality gate fails and user overrides. Fix any crashes, timeouts, or inconsistencies. | 60 min | P6-T05, P6-T06 | Stable end-to-end flow surviving edge cases | P0 | Completed | Added Phase 6 integration tests covering the complete demo path plus skip, disagreement, and override-style variations without crashes |

**Phase 6 total: ~7 hours**

### Implementation Notes

**P6-T01 — Dependency Impact Engine**
- `12-dependency-and-rereasoning.md` §5 has the full `DEPENDENCY_RULES` table and §6 has the impact analysis algorithm. This is a purely deterministic function — no LLM calls.
- `DEPENDENCY_RULES` maps `changed_requirement_type → list[impacted_stages]`. Example: changing `throughput_tps` impacts `options_generation`, `socratic_review`, `adr_generation`, `hld_design`, `waf_review`. **Cost estimate is a sub-artifact of the Options stage** (`OptionsMatrix.cost_estimate` field) — it is regenerated automatically when `options_generation` re-runs and is NOT an independent impacted stage.
- Return type `DependencyImpactResult` has `impacted_stages: list[StageEnum]`, `stable_stages: list[StageEnum]`, `impact_reason: dict[StageEnum, str]` — the reason strings are used directly in the UI's change-impact summary message.

**P6-T02 — Requirement Change Detection**
- `12-dependency-and-rereasoning.md` §3 defines the change classification model. Use a lightweight LLM classifier (GPT-4.1 mini, one-shot prompt) to classify: `new_question | clarification | requirement_change`.
- If `requirement_change`: extract `changed_requirement_type` (from a fixed `ChangeableRequirementType` enum) and `new_value: str`. Handle multi-field changes (e.g., "100K TPS AND multi-region") — return a list of `ChangeSpec` objects.
- This is a direct one-shot LLM call, NOT routed through the full orchestrator or specialist agents. Keep latency < 2 seconds.

**P6-T03 — Selective Stage Re-Execution**
- `12-dependency-and-rereasoning.md` §7 defines the re-execution algorithm. Re-run order must respect stage dependencies (topological sort of impacted stages using the `DependencyMap`).
- Each re-run creates a new `StagePatch` with `base_version=N`, `target_version=N+1`, `triggered_by=change_event_id`. The `ChangeEvent` must be written to `changelog` container BEFORE re-runs begin (with `status: in_progress`). Update to `status: completed` after all impacted stages finish.
- Stable stages: display as "unchanged (v{N})" in the frontend timeline. Their existing artifacts are not touched.

**P6-T04 — ArtifactDiffService**
- `12-dependency-and-rereasoning.md` §8 defines diff algorithms per stage type. Key per-stage logic:
  - **Options**: compare option lists by name — categorize as `added`, `removed`, or `modified` (same name, different scores/components).
  - **HLD**: compare component name lists; compare trust zone subgraph labels; compute Levenshtein similarity of diagram strings.
  - **WAF**: compare finding lists per pillar — new/resolved findings.
  - **Cost**: delta table showing old `monthly_range` vs new `monthly_range` per service. Cost is embedded in `OptionsMatrix` as a `cost_estimate` sub-field — diff it as part of the Options diff, not as a separate document.
  - **ADR**: line-level text diff of the formatted Markdown string.
- `generate_diff()` should be callable per stage independently. Store each `ArtifactDiff` as a document in the `changelog` Cosmos container with `type: "artifact_diff"`. See `04-database-design.md` §5.

**P6-T05 — Demo Scenario: 10K TPS Fraud Detection**
- `15-demo-scenario.md` §3 has the full stage-by-stage expected outputs for this scenario.
- Input: `"Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability SLA."`
- Expected pattern: `real_time_streaming`. Expected primary option: Event Hubs + Stream Analytics/ASA + Cosmos DB, or Event Hubs + Spark Structured Streaming on AKS.
- The Socrates stage is the primary demo wow moment. Personas should surface: PCI-DSS scope concerns (Security), Event Hubs partition limit considerations at 10K TPS (Devil's Advocate), AKS operational complexity vs ASA managed service trade-off (SRE), compute cost at sustained throughput (FinOps), skills availability for Kafka/Flink vs managed services (Delivery).

**P6-T06 — Demo Scenario: 100K TPS Requirement Change**
- `15-demo-scenario.md` §4 covers the requirement-change narrative — the second major wow moment in the demo.
- Input: `"Actually, make it 100K TPS and multi-region active-active."`
- Expected impacted stages: `options_generation`, `socratic_review`, `adr_generation`, `hld_design`, `waf_review`, `cost_estimate`. Stable: `intake`, `requirements_extraction`, `pattern_detection`.
- Expected diff highlights: Event Hubs partition count increase, AKS cluster sizing change, active-active vs active-passive in ADR Consequences section, new WAF Reliability findings (cross-region replication, RPO/RTO targets), significant cost delta in the cost estimate diff table.
- The before/after diff view (P5-T08) must be visually clear for the demo recording.

**P6-T07 — End-to-End Integration Test**
- `15-demo-scenario.md` §5 defines the edge case scenarios to test.
- Three edge cases: (1) User skips a clarifying question → orchestrator proceeds with the assumptions marked in `RequirementSet.assumptions[]` with `requires_user_validation = True`. (2) User disagrees with Socratic recommendation → orchestrator records a `ChangeEvent` with `change_type: scope_change` and allows override (Decision recorded in ADR Context section). (3) Quality gate fails → orchestrator surfaces blocking check failures, waits for user to resolve or restart stage.
- Use `pytest` with `httpx.AsyncClient` targeting `http://localhost:8000`. Mark slow tests `@pytest.mark.slow` and exclude from CI by default.

---

## Phase 7: Polish & Submit (Day 5 — June 13–14)

_Goal: Demo video recorded, README polished, GitHub repo submitted._

| ID | Task | Description | Est. | Depends On | Output | Priority | Status | Summary |
|---|---|---|---|---|---|---|---|---|
| **P7-T01** | Write demo video script | Script a 5-minute demo: 0:00–0:30 hook ("What if an architect's first 2 weeks could happen in 10 minutes?"), 0:30–1:30 intake + requirements + pattern detection, 1:30–2:30 options + Socratic debate (show personas arguing), 2:30–3:30 ADR + HLD diagrams, 3:30–4:15 WAF review + evidence audit, 4:15–5:00 killer moment (requirement change → re-reasoning → before/after diff). | 45 min | P6-T06 | Written demo script with timestamps | P0 |
| **P7-T02** | Record demo video | Record screen + voiceover walkthrough following the script. Use OBS or similar. Show the actual running application (not slides). Ensure Socratic debate is visible, diagrams render, diff view shows clearly. Keep under 5 minutes. | 90 min | P7-T01, P6-T07 | Demo video file (MP4, <5 min) | P0 |
| **P7-T03** | Edit demo video | Light editing: trim dead time, add title card, add captions for key moments ("🔄 Requirement changed — watch the re-reasoning"), ensure audio is clear. Export final. | 45 min | P7-T02 | Final polished demo video | P0 |
| **P7-T04** | Write comprehensive README.md | Write README with: project overview, architecture diagram (Mermaid), key features (Decision Object, Socrates Engine, Evidence Auditor, Quality Gates, Re-reasoning), tech stack, setup instructions, demo walkthrough with screenshots, IQ tools usage section (for "Best Use of IQ Tools" prize), future roadmap. | 60 min | — | Polished README.md | P0 |
| **P7-T05** | Create architecture diagram for README | Generate a clean Mermaid architecture diagram showing: UI → API/Orchestrator → Agent Layer → Socrates Engine → Tools → Storage → Foundry IQ. Include in README. | 30 min | P7-T04 | Architecture diagram in README | P0 |
| **P7-T06** | Clean up repo + add .env.example + requirements.txt | Remove debug code, add `.env.example` with all required env vars (documented), ensure `requirements.txt` is complete, add `CONTRIBUTING.md` and `LICENSE`. Verify the repo is clean and presentable. | 30 min | All prior tasks | Clean GitHub repo ready for submission | P0 |
| **P7-T07** | Submit to contest | Follow Agents League submission process: submit GitHub repo URL, demo video URL, project description. Verify submission is confirmed. Post in Discord for community vote (10% of judging). | 30 min | P7-T03, P7-T06 | Contest submission confirmed | P0 |
| **P7-T08** | Deploy to Azure for live demo link (optional) | Deploy the Streamlit app to Azure Container Apps so judges can try it live. Configure environment variables, managed identity, and CORS. Test the deployed version. | 60 min | P7-T06 | Live demo URL (optional but impressive) | P2 |

**Phase 7 total: ~6.5 hours**

### Implementation Notes

**P7-T01 — Demo Video Script**
- `15-demo-scenario.md` §6 has the full 5-minute narrative arc and timestamp breakdown. Key beats: (0:00–0:30) hook — "architect's first two weeks in 10 minutes"; (0:30–1:30) intake + requirements + pattern detection; (1:30–2:30) options matrix + Socrates debate (primary wow moment — show personas arguing); (2:30–3:30) ADR generation + HLD Mermaid diagram rendered; (3:30–4:15) WAF review + evidence audit report; (4:15–5:00) killer moment — requirement change → re-reasoning → before/after diff.
- Ensure the confidence score badge and at least 2 distinct persona blind spots are clearly visible during the Socrates moment.

**P7-T02 and P7-T03 — Record and Edit Demo Video**
- Follow the script from `15-demo-scenario.md` §6. Run the full 10K TPS scenario first, then trigger the 100K TPS change in the same session to show the diff.
- The diff view (P5-T08) is a key visual — ensure the color-coded before/after panels are clearly readable in the recording resolution.
- Edit: trim dead time during LLM response waits; add title card with project name and contest; add captions at key moments (e.g., "Stage 5: Socrates adversarial review", "Requirement changed — watch selective re-reasoning").

**P7-T04 — README**
- `01-archimedes-hld.md` §1–3 has the executive summary, goals, and design principles to draw from.
- Required README sections (for judging criteria coverage): Project Overview, Architecture Diagram (Mermaid from `01-archimedes-hld.md` §4), Core Components (Orchestrator, Socrates Engine, Evidence Auditor, Quality Gates, Re-reasoning Engine), Tech Stack table, Setup & Deploy (with `.env.example` reference), Demo Walkthrough with screenshots, **Foundry IQ Integration section** (required for "Best Use of IQ Tools" prize — explain the retrieval → EvidenceSource → ClaimRecord → Evidence Audit trail), Roadmap.

**P7-T05 — Architecture Diagram for README**
- Base the diagram on `01-archimedes-hld.md` §4 (System Context Mermaid). Simplify to one clear flowchart: UI → API/Orchestrator → Agent Layer → Socrates Engine → Tools → Storage layer → Foundry IQ + Azure OpenAI.

**P7-T08 — Azure Container Apps Deployment (optional)**
- `13-infrastructure-and-deployment.md` §6 has Container Apps deployment spec.
- Backend (`arch-demo-api-eus`): min 1, max 3 replicas, 1 vCPU / 2 GB RAM, internal + external ingress. Frontend (`arch-demo-ui-eus`): min 1, max 2 replicas, external ingress only, port 8501.
- Use system-assigned managed identity. Assign IAM roles at individual resource level (Cosmos DB, AI Search, OpenAI, Storage) — not at subscription level.
- Environment variables via Container Apps secrets (reference from Key Vault where feasible).

---

## Summary

| Phase | Focus | Tasks | Hours | Days |
|---|---|---|---|---|
| **Phase 0** | Foundation | 11 tasks | 6 hrs | Day 1 (June 9) |
| **Phase 1** | KB & Core State | 11 tasks | 9.5 hrs | Day 1–2 (June 9–10) |
| **Phase 2** | Agent Layer | 13 tasks | 10 hrs | Day 2–3 (June 10–11) |
| **Phase 2.5** | FastAPI Backend | 5 tasks completed | 2.5 hrs | Day 3 (June 11) |
| **Phase 3** | Socrates Engine | 7 tasks completed | 4.5 hrs | Day 3 (June 11) |
| **Phase 4** | Evidence & Quality | 6 tasks completed | 4 hrs | Day 3–4 (June 11–12) |
| **Phase 5** | Frontend & Integration | 8 tasks completed | 6 hrs | Day 4 (June 12) |
| **Phase 6** | Re-Reasoning & Demo | 7 tasks | 7 hrs | Day 4–5 (June 12–13) |
| **Phase 7** | Polish & Submit | 8 tasks | 6.5 hrs | Day 5 (June 13–14) |
| **Total** | | **76 tasks** | **~56 hrs** | **5 days** |

---

## Critical Path

The following task chain determines the minimum time to a working demo. Any delay here delays submission.

```
P0-T06a (Quota validation)
  → P0-T06b/c (Provision Azure resources)
  → P0-T07 (Cosmos DB containers) → P1-T09 (State Manager)

P0-T02/03/04/05 (Pydantic models) → P1-T09 (State Manager) → P1-T10 (Quality gates)

P1-T11 (Mock KB adapter) → P2-T01 (MAF client) → P2-T13 (Orchestrator)
  → P2.5-T01/02/03 (FastAPI backend) → P5-T06 (Connect frontend)
  → P4-T04 (Quality gate integration) → P6-T01/02/03 (Re-reasoning)

P1-T06/07 (Foundry IQ KB live) → P1-T08 (Test KB) → replace mock with real KB in P2-T01

P3-T01/02 (Socrates prompts) → P3-T06 (Workflow) → P3-T07 (Test)

P5-T01 (Frontend skeleton) → P5-T06 (Connect to API)
  → P6-T05 (Demo scenario) → P6-T06 (Change scenario) → P7-T02 (Record video)
```

**Shortest critical path**: P0-T06a → P0-T06b/c → P1-T11 (mock adapter) → P2-T01 → P2-T13 → P2.5-T01/02 → P5-T06 → P6-T05 → P6-T06 → P7-T02 → P7-T07

---

## Recommended Execution Order (Risk-Reduced)

The original plan starts with full Azure provisioning before any coding. This creates a Day 1–2 dependency on Azure quota and Foundry IQ availability. The revised order below reduces that risk by starting implementation immediately.

```
Day 1 (June 9):
  P0-T01  Repo + project structure
  P0-T02/03/04/05  Pydantic models (all four model files)
  P0-T06a  Quota validation (start async, do not block)
  P0-T08  Contest registration
  P1-T09  State Manager (with in-memory mock storage)
  P1-T10  Quality gate service
  P1-T11  Mock Foundry IQ adapter (lets Phase 2 start without live KB)

Day 2 (June 10):
  P0-T06b/c/d  Provision Azure resources (now that quota is confirmed)
  P0-T07  Cosmos DB containers + client
  P1-T01/02/03  KB seed document curation + upload
  P1-T06/07/08  Foundry IQ KB + MCP connection + end-to-end test
  P2-T01  MAF shared client + agent factory (wire mock adapter)
  P2-T02/03/04  Intake, Requirements, Pattern Detector agents

Day 3 (June 11):
  P2-T05/06/07/08  OptionsGenerator, ADRWriter, HLDDesigner, WAFReviewer prompts
  P2-T09/11  mermaid_render_check + adr_formatter tools
  P2-T13  Orchestrator stage controller
  P2.5-T01/02/03/05  FastAPI skeleton + session/message/artifact endpoints
  P3-T01 through P3-T07  Socrates Engine end-to-end

Day 4 (June 12):
  P4-T01/02/03/04/05  Evidence Auditor + quality gate integration
  P5-T01/02/03/04/05/06  Streamlit UI (skeleton, chat, timeline, artifacts, one Mermaid diagram, connect to API)
  P6-T01/02/03  Dependency engine + change detection + selective re-run

Day 5 (June 13-14):
  P6-T04/05/06/07  Diff service + demo scenario testing
  P7-T01/02/03  Demo script + record + edit video
  P7-T04/05/06/07  README + cleanup + submit
```

**Key principle**: mock adapter (P1-T11) unblocks 3 days of agent work from Azure provisioning. Replace mock with live Foundry IQ as soon as KB is ready (end of Day 2).

---

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R1** | **Foundry IQ KB returns poor quality results** — documents poorly chunked, retrieval misses relevant content, citations irrelevant | High | Critical | Curate aggressively (P1-T01/02/03). Test retrieval early (P1-T08). If KB quality is poor by end of Day 2, fall back to direct Azure OpenAI with system prompt containing key reference data. |
| **R2** | **MAF WorkflowBuilder fan-out/fan-in doesn't work as documented** — preview SDK behavior differs from docs | Medium | High | Test Socrates workflow in isolation (P3-T07) by Day 3. If WorkflowBuilder fails, fall back to simple `asyncio.gather()` for parallel persona calls — functionally identical, just not using MAF workflows. |
| **R3** | **Time runs out before frontend integration** — backend works but UI is incomplete | Medium | High | Prioritize P5-T01/02/06 (skeleton + chat + connection) over P5-T07/08 (debate view + diff view). A working chat-only UI with text output is still a valid demo. Diff view is P1, not P0. |
| **R4** | **Foundry IQ MCP preview API is unstable** — connection drops, rate limits, unexpected errors | Medium | Medium | Wrap all Foundry IQ calls in retry logic with exponential backoff. Cache successful KB results in Cosmos DB to avoid redundant calls. Have a direct Azure AI Search fallback path. |
| **R5** | **Socrates latency makes demo awkward** — 30+ seconds of silence while personas "debate" | Low | Medium | Use streaming responses to show persona analyses appearing one by one. The latency becomes a feature — "watch the architects debate in real-time." If still too slow, default to light mode (3 personas). |
| **R6** | **Azure quota or model deployment unavailable** — GPT-4.1 or AI Search S1 not available in target region or subscription | Medium | Critical | Run P0-T06a quota check on Day 1 morning. If blocked, switch region (West US 2, East US 2). Last resort: use `gpt-4o` on an already-provisioned deployment + mock KB adapter (P1-T11) so coding work is unblocked. |
| **R7** | **FastAPI backend missing from original backlog** — P5-T06 frontend connection has no real API to call | High | High | **Fixed**: Phase 2.5 added explicitly. Start P2.5-T01/02/03 on Day 3 morning before frontend work begins. |
| **R8** | **Agent JSON output invalid or schema-breaking** — LLM returns malformed JSON that fails Pydantic parsing | Medium | Medium | In each specialist agent output parser: use `model_validate_json()` with one automatic retry (re-prompt with the validation error message). After 2 failures, return a partial fixture artifact marked `status: degraded`. Do not crash the orchestrator. |
| **R9** | **Foundry IQ citations exist but are irrelevant** — KB retrieval returns topically unrelated sources that pass citation presence check but fail relevance check | Medium | Medium | Use the seed KB (P1-T01/02/03) tuned to fraud detection queries. Evidence Auditor's check 2 (citation relevance) will flag irrelevant citations. Small curated KB reduces this risk significantly vs large generic KB. |
| **R10** | **Streamlit session state bugs** — rerun triggers, stale state, widget key collisions cause UI to break | Medium | Medium | Backend owns all session state (Cosmos DB). Streamlit only holds `session_id` in `st.session_state`. Re-fetch all data from API on each interaction. Avoid storing artifacts or agent output in Streamlit state. |
| **R11** | **Contest registration or submission deadline confusion** — registration deadline (June 12) precedes submission deadline (June 14) | Low | Critical | Complete P0-T08 (registration) on Day 1. Verify Discord access and submission portal URL immediately. Do not rely on remembering this during the final crunch on June 13–14. |

---

## Go / No-Go Criteria for Submission

Submit if **ALL** of these are true by June 14, 11:00 AM PT:

| # | Criterion | Required? |
|---|---|---|
| 1 | Can complete Stages 1–5 (Intake → Requirements → Pattern → Options → Socrates) end-to-end for fraud detection scenario | **Must have** |
| 2 | Socrates produces meaningful persona analyses + synthesis with recommendation and blind spots | **Must have** |
| 3 | ADR and at least one HLD Mermaid diagram are generated | **Must have** |
| 4 | Quality gates enforce blocking/warning at stage transitions | **Must have** |
| 5 | Foundry IQ KB returns relevant, cited results for architecture queries — **at least one real `knowledge_base_retrieve` result must be visible/cited in the demo; mock KB is only for development and rehearsal** | **Must have** |
| 6 | A requirement change triggers dependency-based selective re-reasoning | **Must have** |
| 7 | Demo video recorded (<5 min) showing the full flow + change scenario | **Must have** |
| 8 | GitHub repo is clean with README, architecture diagram, and setup instructions | **Must have** |
| 9 | Evidence Auditor runs at least once (after Socrates) | **Must have** |
| 10 | Before/after diff view shows artifact version comparison | **Nice to have** |
| 11 | Mini WAF review covers all 5 pillars | **Nice to have** |
| 12 | Live deployed demo on Azure Container Apps | **Nice to have** |

**Do NOT submit if**: Stages 1–5 don't work end-to-end, OR Socratic debate doesn't produce meaningful output, OR no Foundry IQ grounding is visible. Better to not submit than to submit a broken demo.

---

_Generated: June 9, 2026_  
_Architecture version: Archimedes v2.2_  
_Author: Viswanath Bandi_

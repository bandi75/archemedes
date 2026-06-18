# Archimedes — Claude Code Context

## What this project is

Archimedes is an AI architecture workbench. A user describes a system they want to build; a multi-agent pipeline produces sequentially richer artefacts — requirements, options, Socratic challenge, ADR, HLD, WAF review — each backed by evidence retrieved from Azure AI Search. The pipeline is stateful, versioned, and re-runnable: changing a requirement re-runs only the affected downstream stages.

---

## How to run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

cp .env.example .env            # then fill in values (see Environment section below)

# Terminal 1 — API
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — UI
streamlit run streamlit_ui/app.py
```

API: http://localhost:8000  
UI:  http://localhost:8501  
OpenAPI docs: http://localhost:8000/docs

---

## Quickest mock-only start (no Azure)

Set these in `.env` and nothing else is required:

```
ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=false
ARCHIMEDES_API_STORAGE_BACKEND=memory
USE_MOCK_KB=true
```

This runs in-memory storage with fixture KB data and no live LLM calls (the Socratic review engine is fully deterministic; all other pipeline stages call the LLM via `FOUNDRY_PROJECT_ENDPOINT`).

---

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Yes (live agents) | — | Azure AI Foundry project endpoint for LLM calls |
| `DEFAULT_ARCHITECTURE_MODEL` | No | `gpt-4.1` | Model deployment name |
| `ARCHIMEDES_API_STORAGE_BACKEND` | No | `memory` | `memory` or `cosmos` |
| `ARCHIMEDES_API_COSMOS_ENDPOINT` | If cosmos | — | Cosmos DB account URL |
| `ARCHIMEDES_API_COSMOS_DATABASE_NAME` | No | `archimedes` | Cosmos database name |
| `ARCHIMEDES_API_COSMOS_KEY` | No | — | Cosmos key; empty = DefaultAzureCredential |
| `ARCHIMEDES_API_VALIDATE_REQUIRED_ENV` | No | `true` | Set `false` to start without live Azure config |
| `USE_MOCK_KB` | No | `true` | `true` = fixture KB; `false` = Azure AI Search |
| `ARCH_SEARCH_ENDPOINT` | If real KB | — | Full Azure AI Search endpoint URL |
| `ARCH_SEARCH_SERVICE_NAME` | If real KB | — | Alternative to `ARCH_SEARCH_ENDPOINT` |
| `ARCH_SEARCH_API_KEY` | If real KB | — | Azure AI Search query key |
| `ARCH_KB_INDEX` | No | `archimedes-arch-idx` | Search index name |
| `ARCHIMEDES_API_URL` | No | `http://localhost:8000/api/v1` | Used by Streamlit frontend |

---

## Project layout

```
src/
  api/                    FastAPI shell
    main.py               App factory, Settings, lifespan, logging config
    deps.py               FastAPI DI: get_storage, get_stage_controller
    storage.py            InMemoryArchimedesStorage (non-Cosmos fallback)
    routers/
      sessions.py         POST /sessions, POST /sessions/{id}/messages, GET /sessions/{id}
      artifacts.py        GET /sessions/{id}/artifacts/{stage}/latest
      evidence.py         GET /sessions/{id}/evidence, /claims
      changes.py          POST /sessions/{id}/changes
      diffs.py            POST/GET /sessions/{id}/diffs

  archimedes/             Core business logic
    agents/
      client.py           FoundryChatClient — wraps azure-ai-inference ChatCompletionsClient
      factory.py          AgentFactory — lazy client, run_stage() LLM tool-call loop, tool schemas
      pattern_detector.py Deterministic keyword-scoring pattern detector (no LLM)
      evidence_auditor.py Deterministic evidence auditor (no LLM)

    models/               All Pydantic schemas
      enums.py            StageName, StageStatus, ClaimType, TrustLevel, ...
      session.py          ArchitectureSession, StageExecution, DependencyMap
      artifacts.py        VersionedArtifact, RequirementContent, OptionsContent, ...
      patches.py          StagePatch, ApplyPatchResult
      claims.py           ClaimRecord
      evidence.py         EvidenceSource
      quality_gates.py    QualityGateResult, QualityGateCheck
      change.py           ChangeEvent, DependencyImpactResult
      diffs.py            ArtifactDiff, FieldDiff
      socrates.py         SocraticReview, PersonaAnalysis, SocratesReviewContext

    orchestrator/
      controller.py       StageController — message routing, stage execution, re-reasoning
      dependency_engine.py detect_requirement_changes(), compute_change_impact()

    socrates/             Fully deterministic Socratic debate engine (no LLM)
      dispatcher.py       DispatcherExecutor — formats context, fans out to personas
      persona.py          PersonaExecutor — per-persona deterministic analysis
      synthesizer.py      SocratesSynthesizerExecutor — ranks options, generates pre-mortem
      workflow.py         SocratesWorkflow — async run(), sync run_sync(), build_stage_patch()

    state/
      state_manager.py    ArchitectureStateManager — apply_patch(), read/write artefacts
      quality_gates.py    evaluate_quality_gate() — checklist-driven gate evaluation
      diff_service.py     ArtifactDiffService — before/after diff computation

    storage/
      cosmos_client.py    CosmosStorageClient — CRUD with ETags, session-partitioned

    tools/
      foundry_iq.py       FoundryIQRetriever — real Azure AI Search via httpx; logs all calls
      mock_foundry_iq.py  MockFoundryIQAdapter — fixture-backed KB (USE_MOCK_KB=true)

prompts/                  Agent system prompts (markdown)
  intake.md, requirements.md, options.md, hld.md, adr.md, waf.md
  socrates/               devils_advocate.md, sre_ops_lead.md, security_architect.md,
                          finops_lead.md, delivery_lead.md, synthesizer.md

tests/                    pytest suite (~84 tests)
docs/design/              15 design documents (source of truth for data models and API contracts)
```

---

## Pipeline — 10 stages in order

| # | Stage (`StageName` value) | Executor | Notes |
|---|---|---|---|
| 1 | `intake` | `IntakeAgent` (LLM) | Clarifies business need, extracts context |
| 2 | `requirements_extraction` | `RequirementsEngineer` (LLM) | Functional + NFRs; calls `evaluate_quality_gate` tool |
| 3 | `pattern_detection` | `PatternDetector` (deterministic) | Keyword scoring; no LLM |
| 4 | `options_generation` | `OptionsGenerator` (LLM) | 3 architecture options with trade-offs |
| 5 | `socratic_review` | `SocratesWorkflow` (deterministic) | 5-persona challenge; auto-runs `evidence_audit_checkpoint` after |
| 6 | `evidence_audit_checkpoint` | `EvidenceAuditor` (deterministic) | Auto-triggered after step 5 |
| 7 | `adr_generation` | `ADRWriter` (LLM) | Architecture Decision Record |
| 8 | `hld_generation` | `HLDDesigner` (LLM) | High-Level Design diagram + components |
| 9 | `mini_waf_review` | `WAFReviewer` (LLM) | WAF 5-pillar review; auto-runs `final_evidence_audit` after |
| 10 | `final_evidence_audit` | `EvidenceAuditor` (deterministic) | Auto-triggered after step 9 |

Each `POST /sessions/{id}/messages` advances the pipeline by one stage. The controller detects if the user message describes a requirement change and re-runs only impacted stages instead.

---

## Key design decisions (things not obvious from reading the code)

**Agent client is lazily initialised.** `AgentFactory.from_env()` is called at `StageController` construction but `create_foundry_chat_client()` is deferred until first `run_stage()` call. This lets the server start without `FOUNDRY_PROJECT_ENDPOINT` when `ARCHIMEDES_API_VALIDATE_REQUIRED_ENV=false`.

**No mock stage data.** All 6 LLM-backed stages call real agents via `AgentFactory.run_stage()`. There is no hardcoded stub payload path — that was removed. The only "mock" is `USE_MOCK_KB=true` which substitutes fixture documents for Azure AI Search results.

**Tool call loop.** `AgentFactory.run_stage()` runs the standard LLM tool-call loop: sends system prompt + user message, handles `foundry_iq_retrieve` and `evaluate_quality_gate` tool calls, collects evidence from KB calls, loops until no tool calls remain, then builds a `StagePatch` from the final JSON response.

**Socrates is deterministic.** All Socratic personas and the synthesizer use hardcoded structured logic, not LLM calls. Personas produce findings based on the `architecture_options` list in context. If `OPTIONS_GENERATION` hasn't run yet, Socrates receives an empty options list and the quality gate blocks.

**Evidence tracking is structural.** Every `StagePatch` carries `evidence_sources` and `claims`. Evidence retrieved via `foundry_iq_retrieve` during a tool call is automatically collected and linked to the claim in `run_stage()`. The `EvidenceAuditor` later checks these links.

**Cosmos ETags.** `CosmosStorageClient` uses ETags for optimistic concurrency on session updates.

**Logging.** `archimedes.tools.foundry_iq` logs every Azure AI Search request and response at INFO. `archimedes.orchestrator.controller` logs stage routing decisions. `azure.cosmos` and `azure.core` are suppressed to WARNING to avoid header noise.

---

## Testing

```bash
pytest                        # all unit tests (~84 passing)
pytest -m integration         # cloud-dependent tests (require real Azure)
pytest tests/test_orchestrator_controller.py -v   # pipeline orchestration
pytest tests/test_socrates.py -v                  # Socratic engine
```

**Tests that exercise LLM-backed stages** pass a `FakeAgentFactory` to `StageController`. The real `AgentFactory.run_stage()` is not called in unit tests. See `tests/test_orchestrator_controller.py` for the pattern.

**Cosmos tests** require a running Cosmos DB emulator or live account and are marked `@pytest.mark.integration`.

---

## Storage backends

| Backend | When | How |
|---|---|---|
| `InMemoryArchimedesStorage` | `ARCHIMEDES_API_STORAGE_BACKEND=memory` | Dict-backed; lost on restart; fine for dev/tests |
| `CosmosStorageClient` | `ARCHIMEDES_API_STORAGE_BACKEND=cosmos` | Session-partitioned; ETags; 4 containers |

Cosmos containers: `architecture_sessions`, `versioned_artifacts`, `claims_evidence`, `change_events`.

---

## Azure AI Search (knowledge base)

When `USE_MOCK_KB=false`, `FoundryIQRetriever` calls:
```
POST {ARCH_SEARCH_ENDPOINT}/indexes/{ARCH_KB_INDEX}/docs/search?api-version=2024-07-01
```
with semantic search, extractive captions, and `top_k` results. Every call is logged — look for `[azure-search]` and `[kb-retriever]` lines in the server output to confirm KB is being hit.

---

## Design documents

The `docs/design/` directory is the source of truth for data contracts and behaviour. When in doubt about a model field or API contract, check there before reading the code.

| File | Read when you need to understand... |
|---|---|
| `01-archimedes-hld.md` | Overall system architecture |
| `02-domain-models.md` | Entity relationships and invariants |
| `03-pydantic-schemas.md` | Exact field definitions for all models |
| `04-database-design.md` | Cosmos container schema, partition keys |
| `05-api-contracts.md` | FastAPI routes and request/response shapes |
| `06-stage-pipeline.md` | Stage lifecycle, transitions, quality gate rules |
| `07-agent-specifications.md` | Per-agent tool access matrix and prompt intent |
| `08-socrates-engine.md` | Socratic debate workflow internals |
| `10-foundry-iq-knowledge-base.md` | KB index setup and retrieval config |
| `11-evidence-and-claims.md` | Evidence taxonomy and audit rules |
| `12-dependency-and-rereasoning.md` | How requirement changes trigger selective re-runs |

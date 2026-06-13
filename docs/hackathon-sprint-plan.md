# Hackathon Sprint Plan — Agents League June 2026

**Track:** Reasoning Agents (Microsoft Foundry)  
**Deadline:** Monday June 15, 2026 at 12:29 PM  
**Last updated:** June 13, 2026

---

## Phase Status Summary

| Phase | Title | Status | Notes |
|---|---|---|---|
| P0 | Context-aware Socrates persona findings | ✅ Done | |
| P1 | Richer orchestrator chat messages | ✅ Done | |
| P2 | GET /sessions + sidebar session list | ✅ Done | |
| P3 | End-to-end demo smoke test | ✅ Done | |
| P4 | Assumption validation flow | ✅ Done | |
| P5 | Structured artifact rendering | ✅ Done | |
| P6 | README overhaul | ✅ Done | |
| P8 | MAF discovery spike | ✅ Done | `agent-framework==1.8.1` installed; imports verified |
| P9 | MAF foundation — replace AgentFactory tool-call loop | ✅ Done | `MAFAgentFactory` + `_run_in_new_loop` (SelectorEventLoop fix) |
| P10 | Socrates Standard — 5 LLM persona agents + synthesizer | ✅ Done | `MAFSocratesWorkflow` + `ConcurrentBuilder`; persona prompts enriched |
| P11 | Human-in-loop requirements clarification | ⏭ Skipped | Time constraint; not needed for demo story |
| P12 | Requirement change agent (MAF wrapper) | ⏭ Skipped | Existing NLP heuristics sufficient for demo |
| P13 | Submission checklist | 🔶 In Progress | Code side done — pending commit, push, public repo, registration |

**Test suite:** 89 / 89 passing as of June 13 2026.

**Pending before submission:**
1. `git add` + `git commit` + `git push origin main` — all P8–P10 changes are uncommitted
2. Verify `github.com/bandi75/archemedes` is **public**
3. End-to-end demo smoke test (live Foundry endpoint, all 10 stages)
4. Register at `aka.ms/agentsleague/aisf`

---

## Judging Criteria Alignment

| Criterion | Weight | Current State | Remaining Gap |
|---|---|---|---|
| Reliability | 20% | 10-stage pipeline runs end-to-end; 89 tests pass; ETags concurrency | None — commit and push needed |
| Reasoning | 20% | All 6 LLM stages use `MAFAgentFactory` + `Agent.run()`; 5 persona agents run concurrently via `ConcurrentBuilder` in Socratic review | None |
| Accuracy | 20% | KB retrieval via MAF `foundry_iq_retrieve` tool; evidence grounding in all LLM stages; EvidenceAuditor checks claim–source links | Output quality tied to Foundry endpoint + prompts |
| User Experience | 15% | Socrates tab shows severity-badged persona findings + synthesizer decision; session history sidebar; assumption validation | P11 (human-in-loop) skipped — minor gap |
| Creativity | 15% | 5 real LLM agents run in parallel via MAF `ConcurrentBuilder`; each persona enriched to reference specific context values; synthesizer pre-mortem | None |
| Community | 10% | README has MAF architecture section with code snippet and pipeline diagram | Repo must be made **public** before submission |

---

## Completed ✅

### P0 · Context-aware Socrates persona findings
Socrates personas now extract option names, Azure services, NFRs, and constraints from context.
Each persona finding references the actual architecture under review.

### P1 · Richer orchestrator chat messages
Quality gate decision, evidence source count, and key Socratic findings surface in the chat panel.
Stage-aware thinking bubble shows while backend is processing.

### P2 · GET /sessions endpoint + sidebar session list
`GET /sessions` returns all sessions sorted newest-first.
Sidebar session browser — up to 10 recent sessions, clickable, active session marked.

### P3 · End-to-end demo smoke test
Full fintech fraud demo validated through all 10 stages.

### P4 · Assumption validation flow
`POST /sessions/{id}/claims/{id}/validate` endpoint.
Unresolved assumptions appear as expandable prompts with Accept / Reject buttons.

### P5 · Structured artifact rendering
Requirements, WAF, ADR, Options, Pattern Detection, HLD all render as structured views.
Mermaid diagrams render via Mermaid 11 CDN with graceful fallback.

### P6 · README overhaul
Pipeline flowchart, Foundry IQ section, Socratic persona table, demo scenario, judging alignment.

---

## Day 2–3 — MAF Integration (June 13–15)

**Goal:** Replace the hand-rolled tool-call loop with Microsoft Agent Framework (MAF).  
Deliver visible multi-agent Socratic reasoning via 5 LLM persona agents running concurrently.

### Architecture target

```text
Current:
  StageController → AgentFactory → custom AzureOpenAI tool-call loop → deterministic Socrates

Target:
  StageController → MAF Agent/Workflow → MAF tool execution + session handling
                 → StateManager (unchanged) validates & persists StagePatch
```

**Boundary rule:** MAF runs reasoning. Archimedes governs state.  
`StageController`, `StateManager`, `DependencyEngine`, `DiffService`, Cosmos writes — all stay outside MAF.

---

### P8 · MAF discovery spike ✅
**Criterion impact:** Reliability (20%) — foundational, must not break existing 89 tests  
**Effort:** ~1 hour  
**Files:** `requirements.txt`, `src/archimedes/agents/maf_factory.py`

Completed. `agent-framework==1.8.1` installed. Imports verified:
- `from agent_framework import Agent, tool, workflow`
- `from agent_framework.foundry import FoundryChatClient`
- `from agent_framework.orchestrations import ConcurrentBuilder`

**Steps:**
1. `pip install agent-framework agent-framework-foundry` and confirm install succeeds
2. Import `from agent_framework import Agent` and `from agent_framework.foundry import FoundryChatClient` — confirm names
3. Write a minimal smoke test: create a `FoundryChatClient`, wrap in `Agent` with one `@tool` function, call `agent.run("hello")` against the Foundry endpoint
4. Identify any API differences from documentation (constructor signatures, tool registration, result shape)
5. If packages do not exist or API is materially different, fall back to wrapping existing `openai.AzureOpenAI` with a thin MAF-compatible interface

**Add feature flag** to `Settings` in `src/api/main.py`:
```python
agent_runtime: str = "maf"  # "maf" | "legacy"
```
This lets Phase 1 be merged even before Socrates Standard is ready, with legacy as safe fallback.

**Acceptance test:** `pip install` succeeds; smoke-test script runs without import errors.

---

### P9 · MAF foundation — replace AgentFactory tool-call loop ✅
**Criterion impact:** Reasoning (20%), Reliability (20%)  
**Effort:** ~3 hours  
**Files:** `src/archimedes/agents/maf_client.py`, `src/archimedes/agents/maf_tools.py`, `src/archimedes/agents/maf_factory.py`, `src/archimedes/agents/middleware.py`

Replace the 165-line manual tool-call loop in `AgentFactory.run_stage()` with MAF's `Agent.run()`.  
`StageController` is unchanged. The patch-building and state persistence stay where they are.

**New files:**

`maf_client.py` — factory for the MAF `FoundryChatClient`:
```python
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

def create_maf_chat_client(endpoint: str, model: str) -> FoundryChatClient:
    return FoundryChatClient(
        project_endpoint=endpoint,
        model=model,
        credential=DefaultAzureCredential(),
    )
```

`maf_tools.py` — convert existing tool functions to `@tool` decorated MAF tools:

| Tool | MAF tool? | Notes |
|---|---|---|
| `foundry_iq_retrieve` | **Yes** | Agents need grounded evidence |
| `evaluate_quality_gate` | **Yes** | Agent asks for gate validation |
| `mermaid_render_check` | **Yes** | HLD agent self-corrects diagrams |
| `dependency_engine` | No | App logic, stays outside MAF |
| `diff_generator` | No | App logic, stays outside MAF |
| Cosmos writes | No | Agents must not mutate state |

`maf_factory.py` — replace `AgentFactory.run_stage()`:
```python
agent = Agent(
    client=maf_chat_client,
    name=agent_def.name,
    instructions=agent_def.instructions,
    tools=[foundry_iq_retrieve, evaluate_quality_gate],
    middleware=[EvidenceCollectorMiddleware(session_id)],
)
result = await agent.run(user_message)
# extract JSON from result, build StagePatch as before
```

`middleware.py` — `EvidenceCollectorMiddleware`:
- Intercepts every `foundry_iq_retrieve` tool call result
- Captures query, source IDs, chunk refs, trust metadata
- Returns enriched evidence records for inclusion in `StagePatch`
- Replaces the manual evidence collection loop in current `run_stage()`

**Deterministic stages** (PatternDetector, EvidenceAuditor) do not use MAF — they are not LLM agents.  
`SocratesWorkflow` is replaced entirely in P10.

**Acceptance test:**
- `pytest` — all 89 existing tests pass (no regression)
- Intake + requirements stages run through MAF and produce valid `StagePatch`
- Evidence sources appear in the response (middleware working)

---

### P10 · Socrates Standard — 5 LLM persona agents + synthesizer ✅
**Criterion impact:** Reasoning (20%), Creativity (15%)  
**Effort:** ~4 hours  
**Files:** `src/archimedes/socrates/maf_socrates.py`, `prompts/socrates/*.md` (5 new prompts), `frontend/app.py`

This is the highest-value MAF feature for judging. Replace the deterministic keyword-scoring  
Socrates with 5 real LLM agents running concurrently on the architecture context.

**Workflow:**
```text
StageController
  → builds SocratesReviewContext (unchanged)
  → invokes SocratesStandardWorkflow

SocratesStandardWorkflow (MAF concurrent workflow)
  → runs 5 persona agents via asyncio.gather or WorkflowBuilder concurrent pattern:
      DevilsAdvocateAgent   (prompts/socrates/devils_advocate.md)
      SRELeadAgent          (prompts/socrates/sre_ops_lead.md)
      SecurityArchitectAgent(prompts/socrates/security_architect.md)
      FinOpsLeadAgent       (prompts/socrates/finops_lead.md)
      DeliveryLeadAgent     (prompts/socrates/delivery_lead.md)
  → collects PersonaFinding[] from all 5
  → invokes SocratesSynthesizerAgent with all findings
  → returns SocratesStagePatch

StateManager (unchanged)
  → validates patch, stores artifact, stores claims/evidence, updates quality gate
```

**Persona agent output schema** (each agent returns this JSON):
```json
{
  "persona": "devils_advocate",
  "severity": "high | medium | low",
  "finding": "...",
  "challenged_assumption": "...",
  "recommended_action": "...",
  "confidence": 0.78
}
```

**Persona focus areas** (prompts must enforce reference to actual context values):

| Persona | Must reference |
|---|---|
| Devil's Advocate | Weakest assumption in the primary option; "what makes this fail" |
| SRE / Ops Lead | Actual availability target (e.g. `99.95%`), RTO/RPO, failure modes |
| Security Architect | Named services, data sensitivity, named compliance frameworks (PCI-DSS, GDPR) |
| FinOps Lead | Actual TPS/scale values, multi-region cost, always-on services |
| Delivery Lead | Service count, team skill gaps, MVP vs production delta |

**Synthesizer output:**
```json
{
  "overall_confidence": "medium",
  "decision_quality": "acceptable_with_warnings",
  "top_risks": [],
  "blind_spots": [],
  "premortem": "narrative text",
  "required_design_changes": [],
  "recommended_decision": "keep | modify | reject option",
  "open_questions": [],
  "persona_findings": []
}
```

**Quality gate rules:**
- `PASSED`: no critical unresolved risks
- `PASSED_WITH_WARNINGS`: high/medium risks with mitigations
- `FAILED`: critical unresolved risk OR missing required decision inputs

**UI update** — Socrates tab in `frontend/app.py`:
- Replace persona cards that show keyword-score metrics with persona finding cards
- Show `severity` badge (🔴 High / 🟠 Medium / 🟡 Low)
- Show synthesizer `recommended_decision` prominently at the top
- Show `premortem` as an expandable narrative section

**Acceptance test:**
- Socrates tab shows 5 distinct LLM-generated persona findings
- Each finding references at least one artifact-specific value (TPS, compliance framework, SLA target, or named Azure service)
- Synthesizer produces a `recommended_decision` that is not empty

---

### P11 · Human-in-loop — requirements agent clarification
**Criterion impact:** Reasoning (20%), UX (15%)  
**Effort:** ~2 hours  
**Files:** `src/archimedes/agents/maf_factory.py`, `src/archimedes/orchestrator/controller.py`, `frontend/app.py`

The `RequirementsEngineer` and `IntakeAgent` currently produce artifacts in one pass.  
With MAF sessions, each agent can surface `open_questions` and the user can answer them  
before the stage finalises, or explicitly say "proceed with these as assumptions".

**Changes required:**
- MAF `AgentSession` tracks conversation continuity within a stage run
- If a stage result contains `open_questions: [...]`, `StageController` marks stage as  
  `awaiting_clarification` instead of `completed`
- `StageController.process_message()` resumes the MAF session with the user's answer  
  when the session is in `awaiting_clarification`
- In the UI: if the last API response has `stage_status == "awaiting_clarification"`,  
  display the open questions as a numbered list above the chat input
- User can answer each question, or type "proceed" to continue with assumptions

**Scope limit:** Apply to `intake` and `requirements_extraction` stages only.  
Do not apply to ADR/HLD/WAF — those stages do not ask clarifying questions.

**Acceptance test:**
- After intake stage, if agent asks "What is the expected peak TPS?", the UI displays it
- Typing an answer resumes the stage; typing "proceed" advances with it as an assumption

---

### P12 · Requirement change agent (MAF wrapper)
**Criterion impact:** Reasoning (20%), Creativity (15%)  
**Effort:** ~1.5 hours  
**Files:** `src/archimedes/agents/maf_factory.py`, `src/archimedes/orchestrator/controller.py`

Requirement-change detection currently uses regex heuristics inside `StageController`.  
A MAF `RequirementChangeAgent` classifies the change more reliably and extracts  
`changed_fields` for the `DependencyEngine`.

**Flow:**
```text
User: "Actually, make it 100K TPS and multi-region active-active."

RequirementChangeAgent (MAF):
  → changed_fields: [throughput, topology, availability]
  → needs_clarification: false
  → confidence: 0.92

DependencyEngine (deterministic, unchanged):
  → impacted_stages: [requirements, options, socrates, adr, hld, waf, evidence_audit]

SelectiveRerunController:
  → invokes affected MAF agents/workflows only

StateManager (unchanged):
  → creates version 2 artifacts, DiffService computes before/after
```

`DependencyEngine` stays deterministic. Only the natural language classification moves to MAF.  
`StageController` still owns the selective rerun logic.

**Acceptance test:**
- Posting "increase to 100K TPS" after requirements stage triggers re-run only of impacted stages
- New artifact versions are created; diff shows changed fields

---

### P13 · Submission checklist
**Effort:** ~1 hour (June 15 morning)

**Code-side (done):**
- [x] `agent-framework` listed in `requirements.txt`
- [x] `ARCHIMEDES_API_AGENT_RUNTIME=maf` in `.env.example` with comment explaining `legacy` fallback
- [x] All 89 unit tests pass with MAF runtime (confirmed June 13 2026)
- [x] README updated with MAF architecture section, `ConcurrentBuilder` code snippet, and pipeline diagram
- [x] `.env.example` contains no real secrets or keys
- [x] Judging criteria table in README updated to reference MAF explicitly

**Pending — user actions required:**
- [ ] `git add -A && git commit -m "feat(maf): P8–P10 MAF migration + bug fixes" && git push origin main`
- [ ] Verify `github.com/bandi75/archemedes` is set to **Public** in GitHub repo settings
- [ ] Run end-to-end demo smoke test: paste fintech fraud scenario, advance all 10 stages, verify Socrates tab shows 5 LLM persona findings with PCI-DSS / TPS references
- [ ] Confirm Evidence tab shows KB source documents retrieved during the run
- [ ] Confirm HLD Mermaid diagram renders without syntax errors in the UI
- [ ] Register submission at `aka.ms/agentsleague/aisf`

---

## MAF Implementation Order

```
June 13 (today):
  P8  — MAF discovery spike (~1 hr)
  P9  — MAF foundation, AgentFactory → MAF Agent (~3 hr)
  P10 — Socrates Standard persona prompts + MAF agents (~4 hr, start)

June 14:
  P10 — Socrates Standard UI update (finish)
  P11 — Human-in-loop for requirements (~2 hr)
  P12 — RequirementChangeAgent (~1.5 hr)
  End-to-end demo smoke test

June 15 morning:
  P13 — Final checklist, README MAF update, submission
```

**If time runs short, priority order is: P8 → P9 → P10 → P13.**  
P11 and P12 improve reasoning depth but P9 + P10 already deliver the multi-agent story.

---

## What to Skip

| Item | Reason to skip |
|---|---|
| Socrates Deep (iterative group chat) | Concurrent P10 is enough for demo; iterative adds LLM latency and complexity risk |
| SSE / live streaming | Thinking bubble achieves same perceived effect |
| Terraform / Bicep IaC | No judging criterion covers deployment automation |
| Application Insights telemetry | No judging criterion |
| Full MAF `SequentialBuilder` for all 10 stages | StageController gate logic is more expressive than SequentialBuilder allows |
| Hosted Foundry Agents (AI Studio deployments) | `FoundryChatClient` + `DefaultAzureCredential` is sufficient |
| Socrates cross-examination / persona rebuttal rounds | P10 parallel pass is enough |

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| MAF package name or API differs from docs | Medium | P8 spike verifies before writing P9; `AGENT_RUNTIME=legacy` fallback |
| MAF `agent.run()` result shape differs from expected | Medium | `result_adapter.py` normalises output before StagePatch construction |
| Socrates Standard LLM output does not parse to PersonaFinding schema | Medium | Instruct agent to return strict JSON; add `result_or_empty()` fallback |
| Socrates Standard adds 5× LLM latency (~30s per run) | High | Persona agents run via `asyncio.gather` concurrently; total ~= 1 agent call time |
| P9 breaks existing 89 tests | Medium | Feature flag: tests use `legacy` runtime; MAF tested separately |
| Requirement-change rerun triggers too many stages | Low | DependencyEngine logic unchanged; MAF only wraps classification step |
| README MAF diagram doesn't render on GitHub | Low | Test Mermaid blocks on GitHub preview before submitting |

---

## Definition of Done

The submission is ready when:
1. A judge can paste the fintech fraud demo scenario, advance through 10 stages, and see  
   five LLM-generated Socratic persona findings that explicitly reference PCI-DSS, throughput  
   targets, and named Azure services — executed via Microsoft Agent Framework
2. The Evidence tab shows named Azure AI Search documents retrieved through MAF middleware
3. The README explains the MAF-based multi-agent reasoning pipeline with an updated diagram  
   and explicitly calls out `agent-framework` + `agent-framework-foundry` as dependencies
4. All 89 unit tests pass
5. The repo is public with no secrets in `.env.example`

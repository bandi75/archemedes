# Archimedes Build Backlog

This document is the single source of truth for Archimedes implementation planning, sequencing, and status tracking.

It consolidates:

- the historical hackathon delivery backlog
- the later MAF migration and sprint work previously tracked in `docs/hackathon-sprint-plan.md`
- the current React/Next.js frontend roadmap aligned to `docs/design/14-frontend-specification.md`
- the API delivery priorities aligned to `docs/design/05-api-contracts-updated.md`

## Current Product Direction

- Backend remains FastAPI plus orchestration, state management, evidence, and diff services.
- Frontend target is the React/Next.js architecture workbench described in `docs/design/14-frontend-specification.md`.
- The Streamlit UI was implemented for the hackathon demo path and remains part of project history, but it is now legacy and not the forward implementation target.

## Naming Conventions

- `P#` phases represent historical and current implementation phases in this backlog.
- `R#` phases represent the active React/Next.js implementation roadmap.
- Status values: `Completed`, `In Progress`, `Planned`, `Open`, `Blocked`, `Historical`.

## Design Document Reference Map

| Document | Primary Purpose | Backlog Use |
|---|---|---|
| `01-archimedes-hld.md` | System context, logical architecture, component overview, tech stack | Cross-cutting architecture reference |
| `04-database-design.md` | Cosmos containers, concurrency, idempotency, persistence rules | Historical backend and state phases |
| `05-api-contracts-updated.md` | Canonical FastAPI surface, SSE/event model, React view-model APIs, MVP endpoint priorities | Backend/API gap closure and React roadmap |
| `06-stage-pipeline.md` | Pipeline stage order, transitions, lifecycle rules | Orchestrator and pipeline screens |
| `07-agent-specifications.md` | Specialist agent boundaries, StagePatch behavior, MAF runtime model | Agent and MAF phases |
| `08-socrates-engine.md` | Persona workflows, synthesis model, debate depth | Socrates delivery and UI rendering |
| `10-foundry-iq-knowledge-base.md` | Knowledge base curation, retrieval, evidence sourcing | KB and evidence phases |
| `11-evidence-and-claims.md` | Claim taxonomy, evidence quality, audit rules | Evidence and validation phases |
| `12-dependency-and-rereasoning.md` | Change impact, rerun logic, diff behavior | Change Impact Studio and backend change flows |
| `13-infrastructure-and-deployment.md` | Azure provisioning and deployment | Historical infrastructure work and future deployment hardening |
| `14-frontend-specification.md` | Canonical React/Next.js workbench UX, information architecture, components, implementation phases | Active frontend roadmap |
| `15-demo-scenario.md` | Demo walkthrough and expected stage outputs | Demo validation and go/no-go checks |

---

## Historical Delivery Phases

These phases capture the implementation history that produced the current backend, orchestration flow, evidence model, hackathon demo path, and legacy Streamlit UI.

## Phase 0: Foundation

_Status: Completed_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P0-T01` | Repository and project scaffold | Base repo structure | Completed | Repo, folders, starter files, and license created. |
| `P0-T02` | Core Pydantic models | Session, stage, quality gate, dependency models | Completed | Core session/state schema layer implemented and tested. |
| `P0-T03` | Artifact and patch models | Versioned artifacts and StagePatch models | Completed | Artifact versioning and patch semantics implemented. |
| `P0-T04` | Claims and evidence models | ClaimRecord and EvidenceSource models | Completed | Claim/evidence schema and validation rules implemented. |
| `P0-T05` | Change and diff models | ChangeEvent and ArtifactDiff models | Completed | Diff/change tracking foundations implemented. |
| `P0-T06` | Azure resource validation and provisioning | Foundry, Search, OpenAI, Cosmos, Storage, ACA environment | Completed | Core Azure runtime resources and identities provisioned and validated. |
| `P0-T07` | Cosmos storage and helper module | Persistent storage helpers | Completed | CRUD, ETag concurrency, and idempotency support implemented. |
| `P0-T08` | Contest registration | Submission readiness prerequisite | Completed | Historical hackathon registration completed. |

### Foundation Notes

- Cosmos containers are `architecture_sessions`, `versioned_artifacts`, `claims_evidence`, and `change_events`.
- Idempotency and optimistic concurrency are part of the persisted state contract and remain required for current API behavior.

---

## Phase 1: Knowledge Base and Core State

_Status: Completed_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P1-T01` | Curate Azure architecture seed docs | KB source set for demo domain | Completed | Initial fraud-detection architecture references collected. |
| `P1-T02` | Curate WAF and service guidance | WAF and service source set | Completed | Reliability, security, cost, and service-limit material curated. |
| `P1-T03` | Upload and index KB sources | Blob and Search-backed knowledge base | Completed | Foundry-connected knowledge base created and retrieval validated. |
| `P1-T04` | Implement `ArchitectureStateManager` | Patch application and persistence | Completed | State manager with idempotency, artifact writes, claims, evidence, and change logging implemented. |
| `P1-T05` | Implement quality gate evaluation | Stage-level gate service | Completed | Deterministic gate evaluation service implemented and tested. |
| `P1-T06` | Implement mock Foundry IQ adapter | Fixture-backed retrieval fallback | Completed | Mock retrieval path added for local/demo resilience. |

### Knowledge and State Notes

- The system supports both live Foundry-backed retrieval and a mock retrieval mode.
- Evidence metadata, freshness, and trust remain first-class inputs to both backend and UI work.

---

## Phase 2: Agent Layer

_Status: Completed_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P2-T01` | MAF shared client and agent factory | Shared MAF-backed specialist runtime | Completed | Shared Foundry client and prompt-driven specialist factory implemented. |
| `P2-T02` | Intake and requirements prompts | Intake and requirements agents | Completed | Intake and requirements extraction prompts implemented. |
| `P2-T03` | Pattern and option generation | Pattern detection and options generation | Completed | Deterministic plus LLM-assisted stage flow implemented. |
| `P2-T04` | Artifact-generation specialists | ADR, HLD, WAF generation | Completed | Core specialist prompts and stage outputs implemented. |
| `P2-T05` | Supporting tools | Mermaid checks, cost estimation, ADR formatting, STRIDE mapping | Completed | Deterministic helper tools implemented. |
| `P2-T06` | Orchestrator stage controller | Main routing and stage execution loop | Completed | Controller coordinates stages, persistence, and user progression. |

### Agent Notes

- The orchestrator remains the lifecycle controller.
- Deterministic stages stay outside MAF where appropriate.

---

## Phase 2.5: FastAPI Backend

_Status: Completed, with additional React-facing work still planned below_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P2.5-T01` | FastAPI app skeleton | App factory, CORS, errors, health | Completed | Backend app bootstrapped and validated locally. |
| `P2.5-T02` | Session APIs | `POST /sessions`, message flow, `GET /sessions/{id}` | Completed | Core session lifecycle APIs implemented. |
| `P2.5-T03` | Pipeline and artifact APIs | Pipeline status and artifact retrieval | Completed | Session pipeline status and artifact reads implemented. |
| `P2.5-T04` | Evidence and diff APIs | Claims, evidence, and diff retrieval | Completed | Evidence and diff endpoints implemented. |
| `P2.5-T05` | Settings, readiness, and normalization | Readiness and error handling | Completed | Runtime configuration and baseline operational checks implemented. |

### Backend Notes

- This phase delivered the control surface needed for the legacy UI and current orchestration.
- The updated API contract adds additional view-model endpoints and SSE expectations that remain active work for the React roadmap.

---

## Phase 3: Socrates Engine

_Status: Completed_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P3-T01` | Persona prompts | Five persona prompts plus synthesizer | Completed | Socrates persona prompts and synthesis rules created. |
| `P3-T02` | Dispatcher and persona executors | Persona execution flow | Completed | Dispatcher, persona execution, and synthesis components implemented. |
| `P3-T03` | Socrates workflow | Fan-out/fan-in review flow | Completed | Workflow-based Socrates execution path implemented. |
| `P3-T04` | End-to-end validation | Socrates test coverage | Completed | Standard-depth review flow covered by tests. |

---

## Phase 4: Evidence and Quality

_Status: Completed_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P4-T01` | Evidence auditor prompt and routine | Evidence audit capability | Completed | Evidence auditing logic and models implemented. |
| `P4-T02` | Claim/evidence linking | Stage outputs linked to evidence | Completed | Specialist outputs now emit linked claim and evidence records. |
| `P4-T03` | Quality-gate orchestration | Stage transition enforcement | Completed | Quality gate outcomes wired into stage advancement flow. |
| `P4-T04` | Post-Socrates checkpoint | Evidence audit checkpoint | Completed | Evidence audit automatically runs after Socrates. |
| `P4-T05` | Final evidence audit | Terminal audit gate | Completed | Final audit runs before completion/output acceptance. |

---

## Phase 5: Legacy Streamlit Frontend and Integration

_Status: Historical / Completed_

This phase is retained for tracking history only. It delivered the hackathon demo UI and validated the backend orchestration path, but it is not the active frontend roadmap.

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P5-T01` | Streamlit shell and chat | Legacy workbench scaffold | Historical | Streamlit layout, chat, and sidebar pipeline timeline implemented. |
| `P5-T02` | Artifact workspace | Stage artifact rendering | Historical | Artifact tabs, summaries, and stage-linked content implemented. |
| `P5-T03` | Mermaid rendering | Legacy HLD rendering path | Historical | Mermaid rendering with graceful fallback added to Streamlit UI. |
| `P5-T04` | API integration | End-to-end UI to backend flow | Historical | Streamlit wired to session, pipeline, artifact, claim, evidence, and diff endpoints. |
| `P5-T05` | Socrates rendering | Persona findings and synthesis display | Historical | Socrates results displayed in the legacy UI. |
| `P5-T06` | Before/after diff view | Legacy rerun comparison screen | Historical | Diff rendering added for hackathon rerun demo. |

### Legacy UI Notes

- The Streamlit UI remains useful as a demo artifact and fallback implementation reference.
- It must not be treated as the target architecture for future feature delivery.

---

## Phase 6: Re-Reasoning and Demo Scenario

_Status: Completed_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P6-T01` | Dependency impact engine | Impacted/stable stage computation | Completed | Deterministic dependency engine implemented. |
| `P6-T02` | Requirement-change detection | Change detection in orchestration flow | Completed | Change detection wired into controller and API flows. |
| `P6-T03` | Selective rerun | Impact-based stage re-execution | Completed | Impacted stages rerun in order with new artifact versions. |
| `P6-T04` | Diff service | Structured before/after diffs | Completed | Diff generation and diff APIs implemented. |
| `P6-T05` | Demo scenario validation | 10K TPS fraud scenario flow | Completed | Primary demo scenario validated end to end. |
| `P6-T06` | Change scenario validation | 100K TPS plus multi-region change flow | Completed | Rerun and diff scenario validated. |
| `P6-T07` | End-to-end integration testing | Demo-path reliability | Completed | Edge-case coverage added for skip, disagreement, and override patterns. |

---

## Phase 7: Polish and Submission

_Status: Partially completed / historical_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P7-T01` | Demo script and README packaging | Submission content | Completed | README overhaul and demo-oriented packaging completed. |
| `P7-T02` | Demo recording and editing | Submission assets | Historical | Hackathon-specific deliverables tracked historically. |
| `P7-T03` | Repo cleanup and submission | Contest finalization | Historical | Historical submission tasks retained for record only. |
| `P7-T08` | Streamlit deployment for live demo | Optional legacy deployment | Historical | Legacy UI deployment path retained as reference, not active roadmap. |

---

## Post-Hackathon / Current-State Backlog Updates

This section absorbs the work and status previously tracked in `docs/hackathon-sprint-plan.md`.

## Phase 8: MAF Migration Outcomes and Current-State Updates

_Status: Mixed_

| ID | Task | Output | Status | Summary |
|---|---|---|---|---|
| `P8` | MAF discovery spike | Framework validation | Completed | `agent-framework` and core MAF imports validated; safe migration path established. |
| `P9` | MAF foundation | Replace manual tool-call loop with MAF `Agent.run()` where appropriate | Completed | MAF-backed client, tools, middleware, and factory path established without replacing deterministic services. |
| `P10` | Socrates Standard | Five concurrent persona agents plus synthesizer | Completed | Current state includes 5 LLM persona findings and synthesizer output aligned to judging criteria. |
| `P11` | Human-in-loop clarification | Clarification flow for intake and requirements | Completed | Assumption/open-question flow added for early-stage interactions. |
| `P12` | Requirement-change agent wrapper | MAF-assisted change classification | Completed | Natural-language change classification upgraded while keeping dependency and rerun logic deterministic. |
| `P13-T01` | Context-aware Socrates findings | Artifact-aware persona outputs | Completed | Persona findings now reference option names, services, TPS, compliance, and other context values. |
| `P13-T02` | Richer orchestrator messages | More informative chat/status messages | Completed | Quality gate decisions, evidence counts, and stage-aware reasoning cues surfaced. |
| `P13-T03` | `GET /sessions` plus session list support | Session history support | Completed | Sessions endpoint and sidebar/list browsing capability added. |
| `P13-T04` | Assumption validation flow | Claim validation UX and endpoint | Completed | Assumption validation endpoint and UI pattern implemented. |
| `P13-T05` | Structured artifact rendering | Better artifact-specific presentation | Completed | Requirements, ADR, HLD, WAF, options, and pattern outputs render in structured form. |
| `P13-T06` | README overhaul | Documentation packaging | Completed | README updated for MAF architecture, demo story, and judging alignment. |
| `P13-T07` | Final repo commit and push | Manual release step | Open | Historical sprint plan recorded commit/push as still requiring a user action. |
| `P13-T08` | Verify repo is public | Manual GitHub setting check | Open | Historical sprint plan recorded public visibility check as unresolved. |
| `P13-T09` | Final smoke-test and visual verification | Manual demo verification | Open | Historical sprint plan recorded final manual checks for Socrates, evidence, and Mermaid rendering as unresolved. |
| `P13-T10` | Register final submission | Manual contest submission | Historical | Historical user action retained for traceability. |

### Current-State Notes

- These items are preserved here so the backlog contains both implementation history and the latest state transitions that were previously split across two docs.
- Manual GitHub/submission actions stay open or historical rather than being silently marked complete.

---

## Active React / Next.js Roadmap

These are the active implementation phases for the forward UI architecture. They supersede the legacy Streamlit phase as the frontend roadmap.

## React Phase 1: Foundation

_Status: Completed_

Backlog goal: establish the React/Next.js workbench shell and common design system described in `docs/design/14-frontend-specification.md` section 22, Phase 1.

| ID | Task | Depends On | Output | Status | Summary |
|---|---|---|---|---|---|
| `R1-T01` | Create Next.js app shell and workspace structure | Existing FastAPI backend | `ui/` React/Next.js frontend workspace | Completed | Added Next.js App Router workspace, TypeScript config, package scripts, env example, and local dev baseline in `ui/`. |
| `R1-T02` | Implement design tokens and Tailwind theme mapping | `R1-T01` | Color, spacing, typography, and semantic token layer | Completed | Added Tailwind config and global CSS variables mapped to the frontend spec token direction. |
| `R1-T03` | Build canonical navigation and top chrome | `R1-T01`, `R1-T02` | Left navigation, top bar, search affordance, CTA shell | Completed | Implemented `AppShell`, `LeftNav`, and `TopBar` with first-class Pipeline navigation and global search chrome. |
| `R1-T04` | Build shared components | `R1-T02` | Shared cards, badges, drawers, tables, status components | Completed | Implemented Phase 1 shared components: page header, metric card, status badge, quality gate badge, data table, icon button, and right drawer. |
| `R1-T05` | Build zero states, sessions list, and pipeline skeleton | `R1-T03`, `R1-T04` | Home zero-state, recent sessions, pipeline skeleton states | Completed | Added command-center page with metrics, recent sessions table, and stable pipeline skeleton layout. |
| `R1-T06` | Add mock data mode and frontend fixtures | `R1-T04`, `R1-T05` | Demo-safe mock rendering path | Completed | Added frontend fixture data and mock mode env defaults so Phase 2 screens can develop ahead of complete view-model APIs. |

### React Phase 1 API Alignment

- The shell anticipates `GET /api/v1/dashboard/summary` and `GET /api/v1/sessions`.
- This phase does not depend on complete backend view-model delivery, but it aligns mock state and loading surfaces to `05-api-contracts-updated.md` sections 18 and 26.

---

## React Phase 2: Hero Demo Screens

_Status: Completed_

Backlog goal: deliver the high-impact MVP screens described in `14-frontend-specification.md` section 22, Phase 2, using the P0 React endpoints from `05-api-contracts-updated.md` section 26.1.

| ID | Task | Depends On | Output | Status | Summary |
|---|---|---|---|---|---|
| `R2-T01` | Implement Architecture Pipeline screen | `R1-T04`, backend pipeline view support | Pipeline screen backed by `GET /api/v1/sessions/{session_id}/pipeline/view` | Completed | Added `/pipeline` hero screen with stage status, metrics, quality gates, and live trace panel using the pipeline view model. |
| `R2-T02` | Implement Socrates Reasoning Lab | `R1-T04`, Socrates view support | Socrates hero screen backed by `GET /api/v1/sessions/{session_id}/socrates/view` | Completed | Added `/socrates` screen rendering decision under review, synthesis, confidence, blind spots, and persona cards. |
| `R2-T03` | Implement Evidence and Claims Explorer | `R1-T04`, evidence view support | Evidence screen backed by `GET /api/v1/sessions/{session_id}/evidence/view` | Completed | Added `/evidence` screen with claims, coverage metrics, evidence source counts, confidence, and validation status. |
| `R2-T04` | Implement Artifact Studio | `R1-T04`, artifact package view support | Artifact package screen backed by `GET /api/v1/sessions/{session_id}/artifacts/package-view` | Completed | Added `/artifacts` screen with package status, artifact cards, render-status badge, and separate quality gate badges. |
| `R2-T05` | Implement Change Impact Studio | `R1-T04`, change impact support | Change impact screen backed by `GET /api/v1/sessions/{session_id}/changes/{change_event_id}/impact-view` | Completed | Added `/changes` screen showing impacted/stable stages, rerun order, and change event summary. |
| `R2-T06` | Implement snapshot-then-stream event behavior | `R2-T01` | Event timeline, running state updates, reconnect behavior | Completed | Added `GET /events`, `GET /events/stream`, and a React live-events panel that opens SSE when mock mode is disabled. |
| `R2-T07` | Integrate P0 session lifecycle and run flows | `R2-T01` through `R2-T06` | Session create/load/run UX | Completed | Added required P0 pipeline controls: create session, run, run-next, pause, resume, retry, cancel, claim validation, changes, re-reason, diffs, and health/readiness coverage. |
| `R2-T08` | Validate hero-screen acceptance criteria | `R2-T01` through `R2-T07` | MVP hero-screen readiness | Completed | Validated backend view APIs and event endpoints with pytest; validated React route/component types with `npm run typecheck`. |

### React Phase 2 Required APIs

The hero-screen implementation assumes delivery or completion of these high-priority APIs from `05-api-contracts-updated.md`:

- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/sessions/{session_id}/overview`
- `GET /api/v1/sessions/{session_id}/pipeline`
- `GET /api/v1/sessions/{session_id}/pipeline/view`
- `GET /api/v1/sessions/{session_id}/socrates/view`
- `GET /api/v1/sessions/{session_id}/evidence/view`
- `GET /api/v1/sessions/{session_id}/artifacts/package-view`
- `POST /api/v1/sessions/{session_id}/claims/{claim_id}/validate`
- `POST /api/v1/sessions/{session_id}/changes`
- `GET /api/v1/sessions/{session_id}/changes/{change_event_id}/impact-view`
- `POST /api/v1/sessions/{session_id}/changes/{change_event_id}/rereason`
- `GET /api/v1/sessions/{session_id}/diffs`
- `GET /api/v1/health`
- `GET /api/v1/health/ready`

---

## React Phase 3: Full Workbench

_Status: Completed_

Backlog goal: complete the broader workbench experience described in `14-frontend-specification.md` section 22, Phase 3, using P1 resource/view APIs from `05-api-contracts-updated.md` section 26.2.

| ID | Task | Depends On | Output | Status | Summary |
|---|---|---|---|---|---|
| `R3-T01` | Implement Intake Workspace | `R2` foundation and session flows | Intake screen | Completed | Added `/intake` workspace with session creation controls and business-need draft surface. |
| `R3-T02` | Implement Requirements Review | Requirements view support | Requirements screen backed by `GET /api/v1/sessions/{session_id}/requirements/view` | Completed | Added `/requirements` screen and backend requirements view model with requirements, constraints, assumptions, open questions, and quality gate state. |
| `R3-T03` | Implement Pattern Explorer | Patterns view support | Pattern screen backed by `GET /api/v1/sessions/{session_id}/patterns/view` | Completed | Added `/patterns` screen and backend patterns view model with detected patterns, signals, service directions, and pattern-specific NFRs. |
| `R3-T04` | Implement Options Board | Options view support | Options screen backed by `GET /api/v1/sessions/{session_id}/options/view` | Completed | Added `/options` screen and backend options view model with option cards, rejected options, tradeoff data, cost estimate, and selected option. |
| `R3-T05` | Implement Mermaid Diagram Viewer and version history | Artifact/version endpoints | Diagram viewer and artifact history UX | Completed | Added `/diagrams` Mermaid source viewer and `/history` version-history screen using artifact package and artifact list data. |
| `R3-T06` | Integrate P1 resource APIs | `R3-T01` through `R3-T05` | Full workbench data integration | Completed | Added `GET /artifacts`, `GET /claims/{claim_id}`, `GET /audits/evidence/latest`, and consumed P1 view/resource APIs from the React data layer. |
| `R3-T07` | Validate full-workbench acceptance criteria | `R3-T01` through `R3-T06` | Full workbench readiness | Completed | Validated Phase 3 backend endpoints with pytest and React full-workbench routes with `npm run typecheck`. |

---

## React Phase 4: Product Hardening

_Status: Planned_

Backlog goal: productize the new frontend and align backend/frontend operational quality with the hardening direction in `14-frontend-specification.md` section 22, Phase 4.

| ID | Task | Depends On | Output | Status | Summary |
|---|---|---|---|---|---|
| `R4-T01` | Add authentication and session ownership | `R3` | Authenticated workbench | Planned | Introduce Entra ID, ownership boundaries, and protected session access patterns. |
| `R4-T02` | Implement export and packaging flows | `R3` and export API decisions | Export UX | Planned | Add architecture package export and handoff flows once backend export contracts are finalized. |
| `R4-T03` | Responsive and accessibility pass | `R2`, `R3` | Improved usability and a11y | Planned | Complete responsive behavior, keyboard access, contrast rules, and accessibility checks. |
| `R4-T04` | Automated frontend test coverage | `R2`, `R3` | UI regression protection | Planned | Add component, integration, and end-to-end test coverage for core workbench flows. |
| `R4-T05` | Operational hardening for live events | `R2-T06` | Stable event and reconnect behavior | Planned | Validate SSE retry, replay, partial success, and error-state handling under realistic backend conditions. |
| `R4-T06` | Session-scoped routing model | `R3`, `R4-T01` | `/sessions/[sessionId]/...` workspace routes | Planned | Move flat workbench routes behind explicit session context so Pipeline is the default session landing page and stage pages are deep-dive workspaces. |
| `R4-T07` | Stage availability and attention states | `R4-T06` | Disabled/ready/running/needs-action navigation states | Planned | Mark unavailable pages until their stage exists and surface waiting-for-user banners for assumptions, evidence gaps, and rerun decisions. |
| `R4-T08` | Knowledge Library / Architecture Catalog domain | `R3` | Cross-session reusable grounding model | Planned | Add versioned organization library concepts for approved services, patterns, standards, templates, review checklists, constraints, and evidence-backed catalog items. |
| `R4-T09` | User/session ownership data model | `R4-T01`, `R4-T06` | Owner-aware sessions and access boundaries | Planned | Add user, owner, shared-with, organization, and tenant context to session APIs and UI so multi-session usage remains unambiguous. |

---

## Backend/API Work Needed for React Delivery

These items track the backend/API closure needed for the React MVP. R4 still owns product hardening such as auth, export, accessibility, frontend automation, and live-event stress testing.

| ID | Task | Status | Summary |
|---|---|---|---|
| `B1` | Complete React view-model APIs from section 18 | Completed | Implemented overview, pipeline, requirements, patterns, options, Socrates, evidence, artifact package, change impact, and event view APIs. |
| `B2` | Align event history and SSE behavior to section 11 | Completed | Added list-events replay cursors, SSE `Last-Event-ID`/`after_event_id` replay, retry hints, no-cache streaming headers, and structured event metadata. |
| `B3` | Validate P0 endpoint checklist from section 26.1 | Completed | Added pytest coverage across session creation/load, pipeline status/run controls, events/SSE, hero view APIs, assumption validation, changes/rereason, diffs, and health/readiness. |
| `B4` | Validate P1 endpoint checklist from section 26.2 | Completed | Added pytest coverage for session listing, requirements/options/patterns view models, artifact list/latest, claim detail, evidence list, and latest evidence audit. |
| `B5` | Confirm acceptance criteria from section 28 | Completed | React MVP API acceptance is validated by targeted backend tests; remaining broader product hardening is tracked under R4. |

---

## Summary

| Phase | Focus | State |
|---|---|---|
| `P0` | Foundation and Azure/runtime setup | Completed |
| `P1` | Knowledge base and state layer | Completed |
| `P2` | Agent layer and orchestrator | Completed |
| `P2.5` | FastAPI backend baseline | Completed |
| `P3` | Socrates engine | Completed |
| `P4` | Evidence and quality | Completed |
| `P5` | Legacy Streamlit frontend | Historical / Completed |
| `P6` | Re-reasoning and demo flows | Completed |
| `P7` | Hackathon polish and submission packaging | Historical / Mixed |
| `P8` | Post-hackathon MAF/current-state updates | Mixed |
| `R1` | React foundation | Completed |
| `R2` | React hero demo screens | Completed |
| `R3` | React full workbench | Completed |
| `R4` | Product hardening | Planned |
| `B1-B5` | Backend/API closure for React | Completed |

### Summary Notes

- Historical phases document how the current system was built and validated.
- Active implementation sequencing now centers on backend API completion for React and on React phases `R1` through `R4`.

---

## Critical Path

The current minimum path to the target product experience is no longer the Streamlit integration path. It is:

```text
B1  Complete P0 React view-model APIs
  -> B2  Align event history and SSE semantics
  -> R1  Next.js foundation and shared components
  -> R2  Hero screens (Pipeline, Socrates, Evidence, Artifact Studio, Change Impact)
  -> R2-T07  Session/run/change flow integration
  -> R2-T08  Hero-screen acceptance validation
  -> R3  Full workbench expansion
  -> R4  Product hardening
```

### Critical Path Dependencies

- `R2` depends on the screen-ready view APIs from `05-api-contracts-updated.md` section 18.
- `R2-T06` depends on section 11 SSE and replay semantics being implemented and stable.
- `R3` depends on the section 26.2 P1 APIs for deeper drill-down and history behavior.

---

## Recommended Execution Order

```text
1. Backend API gap closure for React MVP
   - Complete overview, pipeline view, Socrates view, evidence view, artifact package view, and change impact view.
   - Validate route naming and payload shape against section 26.1.
   - Finish SSE/list-event alignment to section 11.

2. React Phase 1 foundation
   - Create Next.js shell, tokens, navigation, shared components, and mock data mode.

3. React Phase 2 hero screens
   - Implement Pipeline, Socrates, Evidence, Artifact Studio, and Change Impact Studio.
   - Integrate session lifecycle, validate hero-screen acceptance criteria.

4. React Phase 3 full workbench
   - Add Intake, Requirements, Pattern Explorer, Options Board, Mermaid Viewer, and Version History.
   - Integrate section 26.2 P1 APIs.

5. React Phase 4 product hardening
   - Add auth, export flows, accessibility, responsive polish, event hardening, automated tests, session-scoped routing, and stage attention states.
```

### Sequencing Principle

Use the legacy Streamlit app only as a historical reference or fallback demo path. Do not invest new feature work there unless needed temporarily to validate backend behavior.

---

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| `R1` | React hero screens blocked by missing or unstable view-model APIs | High | High | Prioritize `B1`, validate route shapes early, and keep mock data mode available in `R1-T06`. |
| `R2` | SSE/live-event behavior diverges from contract | Medium | High | Implement section 11 replay/reconnect semantics before relying on live reasoning trace UX. |
| `R3` | Design tokens drift from the approved frontend spec | Medium | Medium | Centralize token mapping in `R1-T02` and validate component usage against sections 9 through 12. |
| `R4` | Mermaid render status becomes confused with quality-gate status | Medium | Medium | Keep separate render-status and quality-gate badges in Artifact Studio and diagram-related components. |
| `R5` | Legacy Streamlit UI is mistaken for the active roadmap | Medium | High | Keep legacy work explicitly labeled historical and direct all new frontend work to `R1` through `R4`. |
| `R6` | View-model responses become thin wrappers over raw artifacts, pushing parsing into the frontend | Medium | High | Enforce section 18 design rule: React screens consume screen-ready views, not raw `VersionedArtifact.content`. |
| `R7` | MAF/Socrates outputs become inconsistent across views | Medium | Medium | Use shared backend view-model shaping and acceptance checks for Pipeline, Socrates, and Evidence screens. |
| `R8` | Change Impact Studio lacks stable linkage between change events, reruns, and artifact versions | Medium | High | Ensure `change_event_id`, artifact versions, and diff retrieval are consistently exposed in change flows and views. |
| `R9` | Users lose session context when moving between Pipeline and stage workspaces | Medium | Medium | Move to session-scoped routes, keep Pipeline as the session landing page, and show active session/stage/version context on every workspace page. |

---

## Go / No-Go Criteria for React MVP

Proceed with the React MVP as the primary frontend path only when all of the following are true:

| # | Criterion | Required |
|---|---|---:|
| 1 | A user can create or load a session from the React UI | Yes |
| 2 | The React Pipeline screen renders stage status, quality gates, metrics, and live event state from backend view APIs | Yes |
| 3 | Socrates Reasoning Lab shows five personas plus synthesizer output without parsing raw artifacts client-side | Yes |
| 4 | Evidence and Claims Explorer exposes claims, evidence, trust/freshness, and assumption-validation actions | Yes |
| 5 | Artifact Studio renders package state, including clear separation of render status and quality-gate status | Yes |
| 6 | Change Impact Studio can render impacted/stable stages and drive selective rerun flows | Yes |
| 7 | Section 26.1 P0 hero endpoints are implemented and validated | Yes |
| 8 | Section 11 SSE/list-event semantics support snapshot-then-stream behavior and reconnect safety | Yes |
| 9 | Frontend acceptance criteria in `14-frontend-specification.md` section 23 are satisfied for hero screens | Yes |
| 10 | The legacy Streamlit UI is not being treated as the primary forward implementation plan | Yes |

---

## Verification Checklist for This Document

- Sprint-plan content has been absorbed into this backlog under current-state updates.
- Legacy Streamlit work is preserved as historical context, not as the active roadmap.
- Active frontend phases are now the React/Next.js phases from `14-frontend-specification.md`.
- The backlog references the React-facing APIs, endpoint priorities, SSE expectations, and acceptance criteria from `05-api-contracts-updated.md`.
- This file is the canonical implementation-planning and tracking document.

---

## Changelog

### UX Hub Review - 2026-06-18 11:15 +05:30

- Reviewed user/session/pipeline/stage UX feedback and confirmed the intended model: Pipeline is the session orchestration hub, while individual pages are stage detail workspaces.
- Added Pipeline stage action links, stage last-updated metadata, session-context header copy, and session-workspace navigation grouping in the React UI.
- Added `R4-T06` for session-scoped `/sessions/[sessionId]/...` routing and `R4-T07` for stage availability / attention states.
- Added risk `R9` to track session-context loss between Pipeline and stage pages.

### Screen UX Pass - 2026-06-18 11:37 +05:30

- Reviewed screen-by-screen feedback and skipped items already covered by the Pipeline/session-hub pass.
- Added visible session context to session-scoped pages and improved Command Center, Intake, Options, Evidence, Artifacts, Diagrams, History, Socrates, Patterns, Requirements, and Change Impact surfaces.
- Replaced Options raw JSON score display with score bars and selection/assumption context.
- Added planned `R4-T08` Knowledge Library / Architecture Catalog and `R4-T09` user/session ownership model work.

### Intake Pipeline Split - 2026-06-18 12:00 +05:30

- Split Intake creation mode from Pipeline controls by removing run/pause/resume/retry/change actions from the new-session Intake page.
- Updated Command Center links, copy, and cards so New Session opens `/sessions/new`, product-facing cards are clickable, and internal placeholder drawer content is removed.
- Expanded mock Pipeline to show Intake first plus all forward stages, including ADR, HLD, Mini WAF Review, Final Evidence Audit, and Change Impact / Re-Reasoning.
- Added global Architecture Libraries route/navigation outside the Session Workspace.

### Create Flow Minimal - 2026-06-18 12:35 +05:30

- Separated `/sessions/new` from the Intake stage detail page so new-session creation only captures title, business need, and default context.
- Reduced new-session actions to Create session, Cancel, and Use demo template.
- Restored `/intake` as an existing-session Stage 1 detail page with clarification/update/ready/return actions.
- Added creation-mode navigation that hides the full Session Workspace until a session exists.

### Pipeline State Controls - 2026-06-18 12:56 +05:30

- Made Pipeline action controls state-aware with contextual primary labels, disabled Pause/Resume/Retry/Cancel/Submit Change states, and clearer Cancel run semantics.
- Added Open actions metric for warnings and failures.
- Improved stage row action labels and unavailable-stage prerequisite hints.
- Enriched live reasoning trace rows with timestamp, stage, and event type.

### Pipeline Live Data - 2026-06-18 13:07 +05:30

- Switched Pipeline data loading to prefer real FastAPI sessions by default instead of mock data.
- Added latest-session discovery through `GET /api/v1/sessions` and `?sessionId=` support for loading a specific session pipeline.
- Updated new-session creation to redirect to Pipeline with the returned session ID.
- Kept mock Pipeline fallback only for explicit mock mode or API-unavailable situations.

### React CORS Fix - 2026-06-19 09:30 +05:30

- Fixed browser preflight failures for React session creation by allowing local React dev origins whenever local CORS origins are configured.
- Added regression coverage for `OPTIONS /api/v1/sessions` from `http://localhost:3000`.

### Intake Detail UX - 2026-06-19 09:42 +05:30

- Reworked the Intake page as an existing-session Stage 1 detail workspace rather than a creation/template surface.
- Added pipeline readiness status, original/refined business need cards, open clarifications, answer input, intake notes, setup source labels, and actionable readiness checklist.
- Renamed page actions to Edit business need, Submit clarification answers, Mark ready for requirements, and Back to pipeline.

### Intake Submit Wired - 2026-06-19 09:48 +05:30

- Wired Intake clarification answer submission to update page state and call the active session message API when available.
- Persisted created session IDs for later session-scoped Intake interactions.
- Unlocked Mark ready for requirements after clarification answers are submitted and reflected readiness in the session status/checklist.

### Intake API Submit - 2026-06-19 09:56 +05:30

- Removed the silent local-only submit path that prevented visible Network tab activity in mock/no-session cases.
- Added active-session resolution through URL, local storage, and `GET /sessions` before posting clarification answers.
- Added visible submitting/result status beside the Intake answer button and kept the primary/top submit action in sync.

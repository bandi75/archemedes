# Archimedes Frontend Specification

**Document ID:** `14-frontend-specification.md`  
**Solution:** Archimedes — AI Architecture Workbench  
**Version:** v2.2  
**Status:** Implementation-ready baseline  
**Last updated:** 2026-06-09  
**Related documents:** `01-archimedes-hld.md`, `03-pydantic-schemas.md`, `05-api-contracts.md`, `06-stage-pipeline.md`, `07-agent-specifications.md`, `08-socrates-engine.md`, `09-tool-specifications.md`, `11-evidence-and-claims.md`, `12-dependency-and-rereasoning.md`

---

## 1. Purpose

This document defines the frontend specification for Archimedes.

Archimedes is an AI architecture workbench that turns a raw business need into evidence-backed architecture decisions, stress-tested by Socrates and converted into professional architecture artifacts. The frontend must make this process understandable, inspectable, and impressive during the demo.

The frontend is not just a chat UI. It is a guided architecture workbench with:

- A business-need intake/chat experience.
- A visible 11-stage architecture pipeline.
- Stage execution status and quality gate badges.
- Socrates adversarial review visualization.
- Artifact viewer for requirements, options, ADR, HLD, WAF review, and evidence audits.
- Mermaid architecture diagram rendering.
- Claims/evidence transparency.
- Requirement-change impact and before/after diff view.
- Demo-friendly progress and storytelling.

The MVP frontend should be implemented using **Streamlit** for speed. A later production frontend can be implemented using **React/Next.js**.

---

## 2. Scope

This document covers:

- Frontend goals and principles.
- MVP frontend stack.
- Layout and page structure.
- User journey.
- Main panels and components.
- Session lifecycle behavior.
- Pipeline timeline behavior.
- Chat and command behavior.
- Artifact viewer behavior.
- Socrates debate view.
- Evidence and claims view.
- Requirement-change and diff view.
- Mermaid rendering approach.
- API integration.
- SSE/event streaming behavior.
- Error and retry UX.
- MVP acceptance criteria.

This document does not cover:

- Backend API implementation. See `05-api-contracts.md`.
- Agent prompts. See `07-agent-specifications.md`.
- Socrates workflow internals. See `08-socrates-engine.md`.
- Stage transition rules in detail. See `06-stage-pipeline.md`.
- Full data schemas. See `03-pydantic-schemas.md`.
- Infrastructure provisioning. See `13-infrastructure-and-deployment.md`.

---

## 3. Frontend Design Goals

The frontend should support three goals.

### 3.1 Make architecture reasoning visible

The user should be able to see:

- What stage Archimedes is currently running.
- What inputs the stage used.
- What output was generated.
- Whether the stage passed its quality gate.
- Which claims are facts, assumptions, or recommendations.
- Which evidence sources support important claims.

### 3.2 Make Socrates a demo highlight

Socrates should not appear as hidden backend processing. The UI should show:

- Which persona pack was used.
- Which personas participated.
- Findings by persona.
- Blind spots.
- Pre-mortem scenarios.
- Confidence score.
- Final synthesis.

### 3.3 Make re-reasoning obvious

When a requirement changes, the UI should clearly show:

- What changed.
- Which stages are impacted.
- Which stages remain stable.
- Which artifacts received new versions.
- What changed between before and after versions.

This is the main demo differentiator.

---

## 4. MVP Frontend Stack

### 4.1 MVP choice

Use **Streamlit** for MVP.

Reasons:

- Fast to implement.
- Easy to build chat + sidebar + tabs.
- Supports Markdown rendering out of the box.
- Can embed HTML components for Mermaid.
- Good enough for hackathon/demo flow.
- Reduces frontend engineering overhead.

### 4.2 Later production direction

For production or portfolio-grade polish, migrate to:

- React or Next.js.
- Tailwind CSS or Fluent UI.
- Dedicated Mermaid renderer.
- State management using Zustand/Redux/React Query.
- WebSocket/SSE client for live progress.
- Authentication through Microsoft Entra ID.

### 4.3 MVP deployment

For MVP, two options are acceptable:

| Option | Description | Recommendation |
|---|---|---|
| Single container | Streamlit app calls FastAPI backend | Easiest for local demo |
| Two containers | Streamlit frontend + FastAPI backend | Better deployment separation |

Recommended MVP:

```text
frontend/streamlit_app.py
backend/FastAPI app
```

Both can run locally with Docker Compose and later deploy to Azure Container Apps.

---

## 5. UX Principles

The frontend should feel like an **architecture control room**, not a chatbot.

### 5.1 Layout principles

- Keep the chat visible but not dominant.
- Show the pipeline timeline prominently.
- Use tabs for artifacts and evidence.
- Use badges for stage status and quality gates.
- Make before/after changes visual.
- Avoid overwhelming the user with raw JSON unless they choose developer/debug mode.

### 5.2 Tone

UI labels should be professional and architecture-friendly:

- “Architecture Session” instead of “Conversation”.
- “Stage Timeline” instead of “Progress”.
- “Decision Brief” instead of “Answer”.
- “Evidence Audit” instead of “Sources”.
- “Re-reasoning Impact” instead of “Re-run”.

### 5.3 Demo-first behavior

For the demo, the frontend should:

- Show visible progress during long-running stages.
- Avoid blank screens while agents run.
- Surface intermediate outputs as soon as they complete.
- Make latency feel like thoughtful analysis, especially during Socrates.

---

## 6. Information Architecture

The MVP should use a single-page Streamlit layout with sections and tabs.

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Header: Archimedes — AI Architecture Workbench                       │
│ Session selector | New session | Run pipeline | Demo scenario         │
└─────────────────────────────────────────────────────────────────────┘
┌───────────────────────┬─────────────────────────────────────────────┐
│ Left Sidebar           │ Main Workspace                              │
│                       │                                             │
│ Session summary        │ ┌─────────────────────────────────────────┐ │
│ Pipeline timeline      │ │ Chat / Intake / Commands                 │ │
│ Quality gates          │ └─────────────────────────────────────────┘ │
│ Current stage          │                                             │
│ Run controls           │ ┌─────────────────────────────────────────┐ │
│                       │ │ Artifact tabs                            │ │
│                       │ │ Requirements | Options | Socrates | ADR   │ │
│                       │ │ HLD | WAF | Evidence | Diff              │ │
│                       │ └─────────────────────────────────────────┘ │
└───────────────────────┴─────────────────────────────────────────────┘
```

---

## 7. Primary User Journey

### 7.1 Demo flow

The MVP demo should follow this journey:

1. User starts a new architecture session.
2. User enters a business need.
3. Archimedes creates a session.
4. User starts the pipeline.
5. Stages 1–10 execute sequentially.
6. UI shows stage progress and generated artifacts.
7. Socrates stage displays persona findings and synthesis.
8. Evidence Audit checkpoint shows whether the outputs are grounded.
9. HLD tab shows Mermaid architecture diagram.
10. User changes a requirement.
11. Archimedes generates an impact plan.
12. User triggers selective re-reasoning.
13. UI shows impacted/stable stages and before/after diff.

### 7.2 Recommended demo input

```text
Design a real-time fraud detection platform on Azure for a fintech processing 10K transactions per second with PCI-DSS constraints and 99.95% availability.
```

### 7.3 Recommended requirement change

```text
Actually, make it 100K TPS and multi-region active-active.
```

---

## 8. Page-Level Structure

The MVP can be implemented as one Streamlit page with logical sections.

### 8.1 Header

The header should display:

- Product name: `Archimedes`.
- Subtitle: `Evidence-backed architecture workbench`.
- Current session ID or name.
- Current stage.
- Overall run status.

Example:

```text
Archimedes
Evidence-backed architecture workbench
Session: Real-time Fraud Detection | Stage: Socratic Review | Status: Running
```

### 8.2 Sidebar

The sidebar should contain:

- New session button.
- Existing session selector.
- Demo scenario loader.
- Current session summary.
- Pipeline timeline.
- Quality gate summary.
- Run controls.
- Developer/debug toggle.

### 8.3 Main workspace

The main workspace should contain:

- Chat/intake panel.
- Stage event stream panel.
- Artifact tabs.
- Requirement-change panel when needed.

---

## 9. Frontend Components

### 9.1 Session Controls

Purpose: Create, load, and manage architecture sessions.

Controls:

- `New Session`
- `Load Session`
- `Load Demo Scenario`
- `Refresh Status`
- `Reset Demo`

Associated APIs:

```text
POST /api/v1/sessions
GET  /api/v1/sessions/{session_id}
GET  /api/v1/sessions/{session_id}/timeline
```

MVP behavior:

- On new session, clear local UI state.
- Store `session_id` in `st.session_state`.
- Fetch timeline immediately after session creation.

---

### 9.2 Chat / Intake Panel

Purpose: Capture raw business need and follow-up user instructions.

Inputs:

- Free-text business need.
- Follow-up commands.
- Requirement changes.

Suggested UI:

```text
[Text area]
Tell Archimedes what you want to design...

[Start Architecture Pipeline]
[Submit Requirement Change]
```

Behavior:

- First user message creates or updates session business need.
- `Start Architecture Pipeline` triggers pipeline execution.
- Requirement-change messages should call the requirement-change API, not restart the whole pipeline.

Associated APIs:

```text
POST /api/v1/sessions
POST /api/v1/sessions/{session_id}/pipeline/run
POST /api/v1/sessions/{session_id}/requirement-changes
```

---

### 9.3 Pipeline Timeline

Purpose: Show the 11-stage pipeline and stage status.

Stages:

| # | Stage | Display Label |
|---|---|---|
| 1 | `intake` | Intake |
| 2 | `requirements` | Requirements |
| 3 | `pattern_detection` | Pattern Detection |
| 4 | `options` | Options |
| 5 | `socrates` | Socrates Review |
| 6 | `evidence_audit_checkpoint` | Evidence Audit Checkpoint |
| 7 | `adr` | ADR |
| 8 | `hld` | HLD |
| 9 | `waf_review` | Mini WAF Review |
| 10 | `final_evidence_audit` | Final Evidence Audit |
| 11 | `rereasoning` | Re-reasoning / Diff |

Status values:

```text
pending | running | completed | failed | skipped
```

Visual treatment:

| Status | Suggested UI |
|---|---|
| `pending` | Gray badge |
| `running` | Spinner / blue badge |
| `completed` | Green check |
| `failed` | Red warning |
| `skipped` | Muted badge |

Quality gate values:

```text
passed | passed_with_warnings | failed
```

Visual treatment:

| Quality Gate | Suggested UI |
|---|---|
| `passed` | Green `Passed` badge |
| `passed_with_warnings` | Amber `Warnings` badge |
| `failed` | Red `Failed` badge |

Associated APIs:

```text
GET /api/v1/sessions/{session_id}/timeline
GET /api/v1/sessions/{session_id}/events
```

---

### 9.4 Stage Event Stream

Purpose: Show live updates while the pipeline executes.

Events should include:

- Stage started.
- Stage completed.
- Stage failed.
- Quality gate result.
- Artifact generated.
- Evidence audit completed.
- Requirement change detected.
- Re-reasoning stage started/completed.

SSE event example:

```json
{
  "event_type": "stage_completed",
  "session_id": "arch-session-001",
  "stage": "options",
  "stage_run_id": "options-run-001",
  "status": "completed",
  "message": "Architecture options generated",
  "timestamp": "2026-06-09T12:00:00Z"
}
```

MVP implementation options:

| Option | Notes |
|---|---|
| Polling every 2–5 seconds | Easiest Streamlit implementation |
| SSE client | Better UX, more implementation effort |

Recommended MVP:

- Use polling initially.
- Add SSE later if time permits.

---

## 10. Artifact Tabs

The main workspace should show artifacts in tabs.

Recommended tabs:

```text
Overview | Requirements | Patterns | Options | Socrates | ADR | HLD | WAF | Evidence | Diff | Debug
```

### 10.1 Overview Tab

Purpose: Show session summary.

Contents:

- Business need.
- Current stage.
- Detected primary pattern.
- Recommended option, if available.
- Current decision confidence.
- Quality gate summary.
- Evidence audit status.
- Latest warning messages.

Associated APIs:

```text
GET /api/v1/sessions/{session_id}
GET /api/v1/sessions/{session_id}/timeline
```

---

### 10.2 Requirements Tab

Purpose: Display structured requirements.

Sections:

- Functional requirements.
- Non-functional requirements.
- Constraints.
- Assumptions.
- Open questions.
- Quality gate result.

Display rules:

- Show requirements as tables.
- Highlight missing or warning NFRs.
- Mark assumptions requiring validation.

Associated API:

```text
GET /api/v1/sessions/{session_id}/artifacts/requirements/latest
```

---

### 10.3 Patterns Tab

Purpose: Show detected architecture patterns.

Sections:

- Primary pattern.
- Secondary patterns.
- Pattern signals.
- Typical pipeline.
- Azure services to explore.
- Pattern-specific implied NFRs.

Example:

```text
Primary pattern: Real-time streaming
Typical pipeline: Ingestion → Feature enrichment → Real-time scoring → Alert/action pipeline
```

Associated API:

```text
GET /api/v1/sessions/{session_id}/artifacts/pattern_detection/latest
```

---

### 10.4 Options Tab

Purpose: Show architecture options and trade-offs.

Sections:

- Options matrix.
- Recommended option.
- Rejected option.
- Trade-off scores.
- Risks and mitigations.
- Evidence links.

Suggested table columns:

```text
Option ID | Name | Summary | Cost | Complexity | Scalability | Ops Burden | Status
```

Associated API:

```text
GET /api/v1/sessions/{session_id}/artifacts/options/latest
```

---

### 10.5 Socrates Tab

Purpose: Show adversarial reasoning results.

Sections:

- Depth mode.
- Persona pack.
- Persona findings.
- Blind spots.
- Pre-mortem scenarios.
- Confidence score.
- Synthesized recommendation.

Suggested UI:

```text
Socrates Review — Standard Depth
Personas: Devil's Advocate, SRE/Ops Lead, Security Architect, FinOps Lead, Delivery Lead

[Accordion] Devil's Advocate
[Accordion] SRE/Ops Lead
[Accordion] Security Architect
[Accordion] FinOps Lead
[Accordion] Delivery Lead

Synthesis:
- Recommendation
- Confidence
- Blind spots
- Pre-mortem
```

Associated APIs:

```text
GET  /api/v1/sessions/{session_id}/socrates/latest
POST /api/v1/sessions/{session_id}/socrates/run
```

---

### 10.6 ADR Tab

Purpose: Display the Architecture Decision Record.

Sections:

- Decision title.
- Context.
- Decision.
- Alternatives considered.
- Consequences.
- Status.
- Evidence references.

Display format:

- Markdown rendering.
- Optional download button.

Associated API:

```text
GET /api/v1/sessions/{session_id}/artifacts/adr/latest
```

---

### 10.7 HLD Tab

Purpose: Display high-level architecture design.

Sections:

- Architecture narrative.
- Mermaid diagrams.
- Component table.
- Data flows.
- Trust boundaries.
- Open issues.

Supported diagram types:

- System context.
- Container/component diagram.
- Data flow.
- Optional network/security zones.

Associated API:

```text
GET /api/v1/sessions/{session_id}/artifacts/hld/latest
```

---

### 10.8 WAF Tab

Purpose: Show mini Well-Architected review.

Sections:

- Reliability.
- Security.
- Cost optimization.
- Operational excellence.
- Performance efficiency.
- Findings by severity.
- Recommendations.

Suggested table columns:

```text
Pillar | Finding | Severity | Recommendation | Evidence
```

Associated API:

```text
GET /api/v1/sessions/{session_id}/artifacts/waf_review/latest
```

---

### 10.9 Evidence Tab

Purpose: Show claims, evidence, source trust, and audit results.

Sections:

- Claim summary.
- Facts.
- Assumptions.
- Recommendations.
- Evidence sources.
- Evidence audit report.
- Unsupported claims.
- Stale or low-trust citations.
- Contradictions.

Suggested filters:

```text
All | Facts | Assumptions | Recommendations | Unsupported | Needs Validation
```

Associated APIs:

```text
GET /api/v1/sessions/{session_id}/claims
GET /api/v1/sessions/{session_id}/evidence
GET /api/v1/sessions/{session_id}/evidence-audits/latest
```

---

### 10.10 Diff Tab

Purpose: Show before/after changes after requirement updates.

Sections:

- Requirement change summary.
- Impacted stages.
- Stable stages.
- Artifact versions created.
- Before/after comparison.
- Human-readable diff summary.

Associated APIs:

```text
POST /api/v1/sessions/{session_id}/requirement-changes
POST /api/v1/sessions/{session_id}/rereasoning/run
GET  /api/v1/sessions/{session_id}/diffs/latest
GET  /api/v1/sessions/{session_id}/diffs/{diff_id}
```

---

### 10.11 Debug Tab

Purpose: Help implementation and demo troubleshooting.

Visible only when developer mode is enabled.

Contents:

- Raw session JSON.
- Stage execution records.
- Last event payloads.
- Latest StagePatch summary.
- API response logs.
- Error details.

Do not expose this tab in production.

---

## 11. Mermaid Rendering

### 11.1 Requirement

The frontend must render Mermaid diagrams produced by the HLD stage.

### 11.2 MVP options

Streamlit does not natively render Mermaid. Use one of the following approaches.

#### Option A: Embed Mermaid JavaScript

Use `st.components.v1.html()` to render Mermaid.

Example:

```python
import streamlit as st
import streamlit.components.v1 as components

def render_mermaid(mermaid_code: str, height: int = 600):
    html = f"""
    <div class="mermaid">
    {mermaid_code}
    </div>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
    components.html(html, height=height, scrolling=True)
```

Pros:

- Fast.
- No backend rendering dependency.

Cons:

- Network dependency on CDN unless vendored.
- Render failures happen in frontend.

#### Option B: Backend render check

Use the backend `mermaid_render_check` tool before returning diagrams.

Pros:

- Better quality control.
- Can retry generation before showing broken diagrams.

Cons:

- Slightly more backend complexity.

Recommended MVP:

- Use Option A for rendering.
- Use backend render check if available.
- If rendering fails, show Mermaid source and warning.

### 11.3 Mermaid fallback behavior

If a diagram fails to render:

- Show warning: `Diagram render failed. Showing source.`
- Display Mermaid source in a code block.
- Provide `Retry HLD generation` button if backend supports it.

---

## 12. Requirement Change UX

Requirement-change handling should be highly visible.

### 12.1 Input behavior

When user submits a change such as:

```text
Actually, make it 100K TPS and multi-region active-active.
```

The frontend should call:

```text
POST /api/v1/sessions/{session_id}/requirement-changes
```

The response should include:

- Change ID.
- Detected changed fields.
- Impacted stages.
- Stable stages.
- Proposed re-run plan.

### 12.2 Impact plan display

Show a dedicated impact card:

```text
Requirement Change Detected
Scale: 10K TPS → 100K TPS
Availability topology: single-region → multi-region active-active

Impacted stages:
✓ Options
✓ Socrates
✓ ADR
✓ HLD
✓ WAF Review
✓ Final Evidence Audit

Stable stages:
✓ Business Need
✓ Compliance Framework Selection
✓ Functional Requirements

[Run Selective Re-Reasoning]
```

### 12.3 Re-reasoning run behavior

When user clicks `Run Selective Re-Reasoning`, call:

```text
POST /api/v1/sessions/{session_id}/rereasoning/run
```

Then:

- Show progress only for impacted stages.
- Do not visually reset stable stages.
- Show new versions as they are produced.
- Enable Diff tab when re-run completes.

---

## 13. Before/After Diff UX

The Diff tab should make the demo moment clear.

### 13.1 Diff summary card

Example:

```text
Before/After Diff
Change: 10K TPS → 100K TPS + multi-region active-active

Versions:
Options: v1 → v2
Socrates: v1 → v2
ADR: v1 → v2
HLD: v1 → v2
WAF Review: v1 → v2

Key changes:
- Added multi-region topology.
- Added stronger reliability and failover requirements.
- Cost sensitivity increased from medium to high.
- SRE persona raised operational complexity risk.
```

### 13.2 Stage-specific diff views

Provide selection:

```text
[Options Diff] [Socrates Diff] [ADR Diff] [HLD Diff] [WAF Diff]
```

Display each diff using:

- Added items.
- Removed items.
- Modified items.
- Human-readable summary.

### 13.3 HLD diff

For HLD, show:

- Diagram v1.
- Diagram v2.
- Components added.
- Components removed.
- Data flow changes.
- Trust boundary changes.

If side-by-side rendering is too much for MVP, show:

```text
Before diagram
After diagram
Change summary
```

---

## 14. Evidence and Claims UX

Evidence transparency is a core differentiator.

### 14.1 Claim display

Each claim should show:

```text
Claim text
Type: Fact / Assumption / Recommendation
Confidence
Stage
Evidence count
Validation status
```

### 14.2 Evidence display

Each evidence source should show:

```text
Source title
Source type
Retrieved via
Trust level
Freshness
KB version
Retrieved at
Excerpt
```

### 14.3 Claim type visual treatment

| Claim Type | Suggested UI |
|---|---|
| Fact | Blue badge |
| Assumption | Amber badge |
| Recommendation | Purple or neutral badge |

### 14.4 Evidence audit status

| Audit Result | Suggested UI |
|---|---|
| Strong | Green |
| Adequate | Amber |
| Weak | Red |

Unsupported or low-trust items should be visible, not hidden.

---

## 15. Error Handling UX

### 15.1 Stage failure

When a stage fails, show:

```text
Stage failed: HLD Generation
Reason: Mermaid render check failed after retry

Actions:
[Retry Stage]
[View Error Details]
[Skip for Demo]
```

For MVP, `Skip for Demo` should only be visible in developer/demo mode.

### 15.2 Quality gate failure

When a quality gate fails:

```text
Quality Gate Failed: Requirements
Blocking failures:
- Scale target is missing
- Security requirements not identified

Please provide the missing details before continuing.
```

If only warnings:

```text
Quality Gate Passed with Warnings
- Data residency not specified
- Availability target assumed as 99.9%

[Continue] [Add Details]
```

### 15.3 API failures

Show friendly error messages:

| Failure | UI Message |
|---|---|
| Network error | `Backend is not reachable. Check API service.` |
| 404 session | `Session not found. Load or create a new session.` |
| 409 conflict | `Session changed during execution. Refresh and retry.` |
| 422 validation | `Invalid request. Review required fields.` |
| 500 backend | `Unexpected backend error. See debug details.` |

---

## 16. Frontend State Management

### 16.1 Streamlit session state

Use `st.session_state` for:

```python
st.session_state["session_id"]
st.session_state["session_summary"]
st.session_state["timeline"]
st.session_state["selected_stage"]
st.session_state["selected_artifact_tab"]
st.session_state["developer_mode"]
st.session_state["last_events"]
st.session_state["polling_enabled"]
```

### 16.2 Refresh strategy

Use explicit and automatic refresh:

- Manual `Refresh` button.
- Auto-refresh while pipeline is running.
- Stop auto-refresh when all stages are completed/failed.

Suggested polling interval:

```text
2 seconds during active execution
5 seconds during idle review
```

---

## 17. API Client Layer

Implement a small frontend API client wrapper instead of calling `requests` everywhere.

Suggested file:

```text
frontend/api_client.py
```

Suggested functions:

```python
def create_session(business_need: str) -> dict: ...
def get_session(session_id: str) -> dict: ...
def get_timeline(session_id: str) -> dict: ...
def run_pipeline(session_id: str, start_stage: str | None = None) -> dict: ...
def get_artifact(session_id: str, stage: str, version: str = "latest") -> dict: ...
def get_claims(session_id: str) -> dict: ...
def get_evidence(session_id: str) -> dict: ...
def get_latest_evidence_audit(session_id: str) -> dict: ...
def submit_requirement_change(session_id: str, change_text: str) -> dict: ...
def run_rereasoning(session_id: str, change_id: str) -> dict: ...
def get_latest_diff(session_id: str) -> dict: ...
def run_socrates(session_id: str, depth: str = "standard") -> dict: ...
```

The API client should centralize:

- Base URL.
- Headers.
- Idempotency keys for mutating calls.
- Error handling.
- Timeout settings.

---

## 18. Suggested Streamlit File Structure

```text
frontend/
├── streamlit_app.py
├── api_client.py
├── components/
│   ├── session_controls.py
│   ├── pipeline_timeline.py
│   ├── chat_panel.py
│   ├── artifact_tabs.py
│   ├── mermaid_viewer.py
│   ├── socrates_view.py
│   ├── evidence_view.py
│   ├── diff_view.py
│   └── error_panel.py
├── styles/
│   └── app.css
└── README.md
```

For MVP, this can be simplified to:

```text
frontend/
├── streamlit_app.py
└── api_client.py
```

But component separation is recommended if time permits.

---

## 19. Visual Design Direction

### 19.1 Theme

Use a clean professional architecture-dashboard look.

Suggested characteristics:

- Light theme for readability.
- Minimal accent colors.
- Clear stage badges.
- High contrast for warnings/failures.
- Avoid flashy animations.

### 19.2 Typography

Use Streamlit defaults for MVP. For later React implementation:

- Segoe UI or system font stack.
- Clear code font for Mermaid/source outputs.

### 19.3 Layout density

The UI should be information-rich but not cluttered.

Recommended:

- Sidebar for status and controls.
- Main panel for current work.
- Tabs for detailed artifacts.
- Expanders for long persona findings.

---

## 20. MVP UI Screens

### 20.1 Screen 1 — New Session / Intake

Contents:

- Product header.
- Business need text area.
- Demo scenario button.
- Start pipeline button.

Success criteria:

- User can create session.
- Business need appears in overview.

### 20.2 Screen 2 — Pipeline Running

Contents:

- Stage timeline with running indicator.
- Event stream.
- Partial artifacts as they complete.

Success criteria:

- User can see progress.
- UI does not appear frozen.

### 20.3 Screen 3 — Socrates Review

Contents:

- Persona cards.
- Findings by persona.
- Blind spots.
- Pre-mortem.
- Synthesized recommendation.

Success criteria:

- Socrates looks like adversarial reasoning, not simple summarization.

### 20.4 Screen 4 — HLD Artifact

Contents:

- Mermaid architecture diagram.
- Architecture narrative.
- Component table.
- Trust boundaries.

Success criteria:

- User can understand the proposed architecture visually.

### 20.5 Screen 5 — Evidence View

Contents:

- Claims summary.
- Evidence sources.
- Audit result.
- Unsupported/stale claims if any.

Success criteria:

- User can see that recommendations are grounded.

### 20.6 Screen 6 — Requirement Change / Diff

Contents:

- Requirement change card.
- Impacted/stable stages.
- Selective re-run progress.
- Before/after diff.

Success criteria:

- Demo clearly shows re-reasoning instead of full restart.

---

## 21. Frontend Interaction Flows

### 21.1 Start pipeline

```text
User enters business need
→ Frontend creates session
→ User clicks Start Pipeline
→ API starts pipeline run
→ Frontend polls timeline/events
→ Artifacts appear stage by stage
```

### 21.2 View artifact

```text
User opens tab
→ Frontend calls get_artifact(stage, latest)
→ Artifact rendered as table/Markdown/Mermaid
→ Claims/evidence links shown where available
```

### 21.3 Requirement change

```text
User enters change text
→ Frontend submits requirement change
→ Backend returns impact plan
→ Frontend displays impacted/stable stages
→ User clicks Run Selective Re-Reasoning
→ Frontend tracks impacted stage progress
→ Diff tab enabled
```

### 21.4 Retry failed stage

```text
Stage fails
→ Frontend displays failure reason
→ User clicks Retry Stage
→ Backend starts new stage_run_id
→ Frontend polls timeline
```

---

## 22. Frontend-to-Backend Mapping

| UI Action | API |
|---|---|
| Create session | `POST /api/v1/sessions` |
| Load session | `GET /api/v1/sessions/{session_id}` |
| Start full pipeline | `POST /api/v1/sessions/{session_id}/pipeline/run` |
| Get timeline | `GET /api/v1/sessions/{session_id}/timeline` |
| Get events | `GET /api/v1/sessions/{session_id}/events` |
| Get artifact | `GET /api/v1/sessions/{session_id}/artifacts/{stage}/latest` |
| Get claims | `GET /api/v1/sessions/{session_id}/claims` |
| Get evidence | `GET /api/v1/sessions/{session_id}/evidence` |
| Get audit | `GET /api/v1/sessions/{session_id}/evidence-audits/latest` |
| Run Socrates | `POST /api/v1/sessions/{session_id}/socrates/run` |
| Submit requirement change | `POST /api/v1/sessions/{session_id}/requirement-changes` |
| Run selective re-reasoning | `POST /api/v1/sessions/{session_id}/rereasoning/run` |
| Get latest diff | `GET /api/v1/sessions/{session_id}/diffs/latest` |
| Retry stage | `POST /api/v1/sessions/{session_id}/stages/{stage}/retry` |

---

## 23. Demo Mode

The MVP should include a demo mode to reduce risk.

### 23.1 Demo scenario button

Button:

```text
Load Fraud Detection Demo
```

It should populate:

```text
Design a real-time fraud detection platform on Azure for a fintech processing 10K transactions per second with PCI-DSS constraints and 99.95% availability.
```

### 23.2 Demo change button

Button:

```text
Apply Demo Change: 100K TPS + Multi-region
```

It should submit:

```text
Actually, make it 100K TPS and multi-region active-active.
```

### 23.3 Demo fallback data

Optional but recommended:

- Store sample artifact JSON files under `frontend/demo_data/`.
- If backend is unavailable, allow UI-only walkthrough.
- Clearly mark fallback mode as demo/mock.

Suggested structure:

```text
frontend/demo_data/
├── session_summary.json
├── timeline.json
├── requirements.json
├── pattern_detection.json
├── options.json
├── socrates.json
├── adr.json
├── hld.json
├── waf_review.json
├── evidence_audit.json
└── diff.json
```

This helps protect the demo if live agent calls fail.

---

## 24. Accessibility and Usability

MVP should follow simple usability rules:

- Avoid color-only status indicators; include text labels.
- Use readable font sizes.
- Keep important controls above the fold.
- Use expanders for long content.
- Avoid horizontal scrolling where possible.
- Show timestamps for stage events.

---

## 25. Security Considerations

For MVP:

- Do not expose secrets in frontend logs.
- Do not show raw API keys.
- Do not render arbitrary unsafe HTML except controlled Mermaid component.
- Treat Mermaid source as generated content and sanitize where practical.
- Protect debug mode in deployed environments.

For production:

- Use Entra ID authentication.
- Enforce session ownership.
- Add RBAC for viewer/editor/admin roles.
- Disable public debug endpoints.
- Use secure cookies/session tokens if web app becomes multi-user.

---

## 26. Observability

The frontend should log key events locally and optionally send telemetry to backend later.

Frontend events:

- Session created.
- Pipeline started.
- Stage selected.
- Artifact viewed.
- Socrates viewed.
- Requirement change submitted.
- Diff viewed.
- API error occurred.

For MVP, simple console or Streamlit debug log is enough.

For production, use Application Insights browser telemetry or an equivalent frontend telemetry approach.

---

## 27. Testing Strategy

### 27.1 Manual test cases

| Test | Expected Result |
|---|---|
| Create new session | Session ID created and overview shown |
| Load demo scenario | Business need populated |
| Start pipeline | Timeline moves from pending to running/completed |
| View requirements | Structured requirements displayed |
| View Socrates | Persona findings and synthesis displayed |
| View HLD | Mermaid diagram renders or source fallback appears |
| View evidence | Claims and evidence records displayed |
| Submit change | Impact plan shown |
| Run re-reasoning | Only impacted stages rerun |
| View diff | Before/after changes shown |
| Simulate stage failure | Retry/error UI shown |

### 27.2 Mock API testing

Before backend is complete, test UI against static JSON fixtures.

Recommended approach:

```text
frontend/demo_data/*.json
api_client.py supports DEMO_MODE=true
```

### 27.3 Browser testing

For Streamlit MVP:

- Chrome.
- Edge.
- 1440×900 or higher resolution.

Mobile is not required for MVP.

---

## 28. MVP Acceptance Criteria

The frontend MVP is acceptable when:

1. User can create or load an architecture session.
2. User can enter a business need and start the pipeline.
3. The 11-stage timeline is visible.
4. Stage status updates are visible through polling or SSE.
5. Requirements, options, Socrates, ADR, HLD, WAF, and evidence artifacts are viewable.
6. Mermaid HLD diagram renders or gracefully falls back to source.
7. Evidence audit status is visible.
8. Requirement change impact plan is visible.
9. Selective re-reasoning can be triggered.
10. Before/after diff is visible.
11. Stage failures and quality gate warnings are understandable.
12. Demo scenario can be loaded quickly.

---

## 29. Deferred Features

The following are intentionally deferred:

- Full React/Next.js implementation.
- Multi-user collaboration.
- Role-based access control.
- Artifact export to Word/PDF.
- Real-time WebSocket if polling is sufficient.
- Advanced diagram editing.
- Full accessibility compliance review.
- User-managed prompt customization.
- Multi-session comparison.
- Advanced evidence graph visualization.

---

## 30. Implementation Checklist

### MVP build checklist

- [ ] Create `frontend/streamlit_app.py`.
- [ ] Create `frontend/api_client.py`.
- [ ] Add environment variable for backend base URL.
- [ ] Build session create/load UI.
- [ ] Build demo scenario loader.
- [ ] Build pipeline timeline component.
- [ ] Build pipeline run button.
- [ ] Add polling-based timeline refresh.
- [ ] Build artifact tabs.
- [ ] Build requirements table view.
- [ ] Build options matrix view.
- [ ] Build Socrates persona view.
- [ ] Build ADR Markdown view.
- [ ] Build HLD Mermaid view.
- [ ] Build WAF findings view.
- [ ] Build evidence and claims view.
- [ ] Build requirement-change form.
- [ ] Build impact plan display.
- [ ] Build selective re-reasoning trigger.
- [ ] Build diff view.
- [ ] Add error handling.
- [ ] Add developer/debug mode.
- [ ] Add optional mock/demo data mode.

---

## 31. Open Decisions

| Decision | Options | Recommendation |
|---|---|---|
| Streamlit vs React for MVP | Streamlit / React | Streamlit |
| Event updates | Polling / SSE | Polling first, SSE later |
| Mermaid rendering | Frontend JS / backend image | Frontend JS with fallback |
| Demo fallback | None / static fixtures | Static fixtures recommended |
| Debug mode | Always visible / toggle | Toggle |
| Authentication | None / API key / Entra ID | None or API key for MVP |

---

## 32. Summary

The Archimedes frontend should present the system as a structured architecture workbench.

The MVP should prioritize:

- Clear session intake.
- Visible pipeline execution.
- Artifact review.
- Socrates debate visibility.
- Evidence transparency.
- Requirement-change impact and diff.

The UI does not need production-grade polish for the first build, but it must make the architecture reasoning process easy to follow. The demo should leave the user with the impression that Archimedes is not merely generating text; it is managing a traceable architecture lifecycle.

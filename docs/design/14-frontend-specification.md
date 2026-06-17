# Archimedes Frontend Specification

**Document ID:** `14-frontend-specification.md`  
**Solution:** Archimedes — AI Architecture Workbench  
**Version:** v3.0  
**Status:** Consolidated React / Next.js frontend baseline  
**Last updated:** 2026-06-17  
**Frontend direction:** Next.js + React + TypeScript  
**Supersedes:** `14a-frontend-specification.md` and `14b-archimedes-ui-design-system.md`  
**Legacy UI:** Streamlit MVP retained only as historical reference in Appendix A  
**Related documents:** `01-archimedes-hld.md`, `03-pydantic-schemas.md`, `05-api-contracts.md`, `06-stage-pipeline.md`, `07-agent-specifications.md`, `08-socrates-engine.md`, `09-tool-specifications.md`, `11-evidence-and-claims.md`, `12-dependency-and-rereasoning.md`, `13-infrastructure-and-deployment.md`, `15-demo-scenario.md`

---

## 1. Purpose

This document is the single frontend specification for Archimedes.

Archimedes is an AI Architecture Workbench that converts a raw business need into evidence-backed architecture decisions, stress-tested by Socrates, and converted into professional architecture artifacts.

The frontend must make the process understandable, inspectable, and visually impressive. It should feel like an **AI Architecture Control Room**, not a chatbot or raw JSON artifact viewer.

The UI must make the following visible:

1. Architecture lifecycle progress.
2. Agent and tool activity.
3. Socrates persona reasoning and synthesis.
4. Quality gates, warnings, failures, and retries.
5. Claims, evidence, assumptions, trust, and freshness.
6. Versioned artifacts.
7. Requirement-change impact and selective re-reasoning.
8. Before/after architecture differences.
9. Demo and product readiness signals, when feature-flagged.

The generated mockups remain the target look and feel. Next.js is the implementation framework and should not materially change the visual direction.

---

## 2. Consolidation Decision

### 2.1 What changed

The previous frontend documentation existed in two parts:

| Document | Prior role | New decision |
|---|---|---|
| `14a-frontend-specification.md` | Streamlit MVP frontend specification | Retired. Valid behavioral requirements have been folded into this document as legacy-retained behavior. |
| `14b-archimedes-ui-design-system.md` | React/Next.js UI design system draft | Promoted and merged into this document. |

### 2.2 Why this consolidation is necessary

Keeping both documents active creates implementation ambiguity:

- `14a` describes a Streamlit-style single-page app with chat, sidebar, tabs, and pipeline timeline.
- `14b` describes a polished React/Next.js workbench with dashboard screens, drawers, live reasoning traces, and view-model APIs.
- The generated mockups also had inconsistent navigation labels and product chrome.

This consolidated document resolves those conflicts and becomes the only active frontend source of truth.

### 2.3 Streamlit status

Streamlit is now **legacy UI**.

Streamlit concepts that remain valid:

- Business-need intake and command flow.
- Session creation/loading behavior.
- Pipeline visibility.
- Stage status and quality gate badges.
- Artifact tabs.
- Mermaid rendering fallback.
- Evidence and claims visibility.
- Requirement-change and before/after diff flow.
- Polling/SSE-style event updates.
- Error, retry, and partial-success states.

Streamlit implementation details that are retired:

- Single-page Streamlit layout as primary IA.
- `st.session_state` as frontend state model.
- Streamlit sidebar as primary navigation implementation.
- Raw JSON fallback as normal artifact display.
- Streamlit-specific deployment assumptions.

See Appendix A for the legacy UI mapping.

---

## 3. Design Principles

| Principle | Meaning | UI implication |
|---|---|---|
| Architecture control room | Archimedes is not a chatbot-only experience. | Use dashboards, timelines, structured panels, drawers, and artifact viewers. |
| Reasoning visibility | Users should see what agents are doing. | Show live stage events, persona activity, tool calls, evidence retrieval, and quality gates. |
| Evidence-first trust | Architecture decisions must be inspectable. | Claims and evidence are first-class UI objects. |
| Professional artifact quality | Outputs should feel architecture-board ready. | Render ADR, HLD, WAF, and evidence reports as documents, not raw JSON. |
| Guided complexity | The app is sophisticated but should not overwhelm. | Use progressive disclosure, right drawers, tabs, and collapsible debug views. |
| Demo clarity without demo leakage | Hackathon/demo signals should be visible only when enabled. | Put judging/readiness panels behind feature flags and provide neutral production copy. |
| Consistent visual language | Screens should look like one product. | Reuse tokens, components, badges, tables, cards, drawers, and navigation patterns. |
| No hidden state mutation | The UI should never imply architecture changed silently. | Requirement changes must show impact, rerun plan, versions, and diffs. |
| No raw chain-of-thought | Show structured reasoning summaries, not hidden model reasoning. | Use event traces, persona findings, assumptions, evidence, and synthesis summaries. |

---

## 4. Product Personality

Archimedes should feel:

- Senior-architect grade.
- Calm and trustworthy.
- Analytical, not flashy.
- Microsoft/Azure-friendly without copying Azure Portal exactly.
- Modern enterprise SaaS workbench.
- Transparent about reasoning without exposing raw hidden model chain-of-thought.

Avoid:

- Generic chatbot look.
- Raw JSON as primary display.
- Overly dark cyber/security styling.
- Cartoonish AI visuals.
- Excessive gradients or noisy backgrounds.
- Tiny unreadable dashboard text.
- Hackathon-only copy in production mode.

---

## 5. Recommended Frontend Stack

| Concern | Recommendation |
|---|---|
| Framework | Next.js App Router |
| Language | TypeScript |
| UI styling | Tailwind CSS |
| Component base | shadcn/ui plus custom Archimedes components |
| Server state | TanStack Query |
| Client/workbench state | Zustand |
| Tables | TanStack Table |
| Diagrams | Mermaid JS renderer with source fallback |
| Live backend updates | Server-Sent Events first; WebSocket only if bidirectional coordination becomes necessary |
| Icons | Lucide React |
| Auth later | Microsoft Entra ID through MSAL |
| Charts | Recharts or lightweight custom SVG/progress components |
| Flow diagrams later | React Flow only if impact maps need richer interactivity |

Implementation guidance:

- Keep FastAPI as the orchestration backend.
- Use Next.js primarily as a rich client workbench.
- Use Client Components for interactive screens.
- Do not move agent orchestration into Next.js.
- Avoid deep SSR/server-action complexity in the first version.
- Use snapshot APIs plus SSE event streaming for live progress.

---

## 6. Core Layout System

### 6.1 Global App Shell

The generated screens use a consistent shell that should be preserved.

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Top Bar: Search, notifications, help, user profile                   │
├───────────────┬─────────────────────────────────────────────────────┤
│ Left Nav      │ Main Workbench Area                                  │
│               │                                                     │
│ Product logo  │ Page header / breadcrumb / actions                   │
│ Navigation    │ KPI cards / status panels                            │
│ Assistant CTA │ Primary screen content                               │
│ Help/support  │ Optional right drawer or live reasoning trace         │
└───────────────┴─────────────────────────────────────────────────────┘
```

### 6.2 Screen width

| Breakpoint | Behavior |
|---|---|
| `< 1024px` | Not a primary MVP target. Show simplified single-column fallback. |
| `1024–1279px` | Collapse secondary right panels where needed. |
| `1280–1535px` | Primary laptop layout. All hero screens must work well here. |
| `1536px+` | Full workbench layout with right-side drawers and multi-column cards. |

### 6.3 Page structure

Every major screen follows this pattern:

```text
Breadcrumb
Page title + short description
Primary actions
Optional feature-flagged readiness chips
Main content region
Optional right-side drawer / live reasoning trace
```

---

## 7. Canonical Information Architecture

The mockups showed multiple competing navigation vocabularies. This specification defines the canonical IA.

### 7.1 Active MVP navigation

Use this navigation for the first React implementation:

```text
Home
Sessions
Intake
Pipeline
Requirements
Patterns
Options
Socrates
Evidence
Artifacts
Change Impact
Settings
```

### 7.2 Full product navigation groups

The grouped product IA may be introduced later, but only after the MVP screens are stable.

```text
Workspace
- Home
- Sessions
- Intake

Design
- Pipeline
- Requirements
- Patterns
- Options

Reasoning
- Socrates
- Assumptions
- Risks

Evidence
- Claims
- Evidence Audit
- Sources

Artifacts
- Architecture Package
- ADR
- HLD
- WAF Review
- Diagrams

Change Control
- Change Impact
- Version History
- Before / After Diff

Admin
- Knowledge Base
- Agent Runs
- Settings
```

### 7.3 Retired or future mockup labels

The following labels appeared in generated mockups but are **not canonical MVP navigation labels**:

| Mockup label | MVP decision |
|---|---|
| Architect | Retire or map internally to `Pipeline` / `Design`. |
| Blueprints | Future artifact/catalog concept. Disabled or hidden for MVP. |
| ADR Library | Future library view. Use `Artifacts` for MVP. |
| Decisions | Future decision catalog. Use `Artifacts` / `Options` for MVP. |
| Simulations | Future capability. Disabled or hidden for MVP. |
| Reviews | Future review workflow. Use `Socrates` / `Evidence` / `WAF` in MVP. |
| Catalog | Future architecture catalog. Disabled or hidden for MVP. |
| Governance Center | Future admin/governance group. Disabled or hidden for MVP. |
| Ontology Workbench | Not part of Archimedes MVP frontend. Hide. |
| Integrations | Future admin group. Hide or disabled. |

### 7.4 Navigation states

| State | Visual treatment |
|---|---|
| Default | Neutral text, muted icon |
| Hover | Pale blue background |
| Active | Pale blue background, navy text, left accent bar |
| Disabled | Muted text, no hover emphasis, optional `Coming soon` tooltip |
| Alert | Small amber/red count badge with text tooltip |

### 7.5 Pipeline navigation rule

`Pipeline` is a hero screen and must always have a first-class nav entry.

It must not be hidden inside `Sessions`, `Architect`, or `Design Studio`.

---

## 8. Branding and Product Chrome

### 8.1 Logo

Use one canonical logo treatment across all screens.

Recommended MVP logo:

- Flat `A` monogram or simple geometric mark.
- Navy primary color.
- No 3D/isometric cube in the app shell.
- 3D/isometric illustration may appear inside the Home hero card only.

### 8.2 Product name

Use:

```text
Archimedes
AI Architecture Workbench
```

Avoid alternating with `Architecture Management`, `Design Studio`, or `AI Architect` in the top-left brand area.

### 8.3 Top search

Use one search placeholder everywhere:

```text
Search sessions, artifacts, requirements, claims, or decisions...
```

Keyboard shortcut:

```text
/
```

Rules:

- Show `/` shortcut hint inside the search box.
- Pressing `/` focuses the global search input unless the user is typing in a form field.
- Initial search scope includes sessions, artifacts, requirements, claims, evidence sources, and decisions.

### 8.4 Persistent assistant CTA

A compact `Socrates AI Assistant` CTA may appear near the bottom of the left nav.

Copy:

```text
Socrates AI Assistant
Ask. Challenge. Validate.
```

Rules:

- It should open a guided side panel, not replace the current screen.
- It should be hidden or simplified on very narrow layouts.
- It should not imply Socrates is a general chatbot; it is a reasoning assistant for the active architecture session.

### 8.5 Demo chrome feature flags

The following UI elements are useful for demo/hackathon mode but should be feature-flagged:

| Element | Demo copy | Production copy |
|---|---|---|
| Judging readiness panel | `Judging Readiness` / `Hackathon evaluation themes` | `Architecture Readiness` / `Decision quality signals` |
| `Excellent — You’re ready to impress` | Allowed in demo mode | Replace with `Architecture package is ready for review` |
| `BETA` tag | Allowed in demo mode | Replace with version badge or remove |
| `Generated with Socrates Reasoning Engine` footer | Allowed in demo mode | Replace with `Generated by Archimedes` plus timestamp |
| Creativity score | Allowed in demo mode | Replace with `Change impact coverage` or hide |

Feature flag:

```ts
type UiMode = 'demo' | 'product'
```

---

## 9. Visual Tokens

### 9.1 Color palette

#### Core colors

| Token | Hex | Usage |
|---|---:|---|
| `--color-bg-app` | `#F6F8FB` | App background |
| `--color-bg-surface` | `#FFFFFF` | Cards, tables, drawers |
| `--color-bg-muted` | `#F1F5F9` | Secondary panels |
| `--color-border` | `#E2E8F0` | Card/table borders |
| `--color-border-strong` | `#CBD5E1` | Active borders, separators |
| `--color-text-primary` | `#0F172A` | Main text |
| `--color-text-secondary` | `#475569` | Secondary text |
| `--color-text-muted` | `#64748B` | Metadata, captions |
| `--color-primary` | `#0F2A4A` | Navy primary buttons, active nav, major actions |
| `--color-primary-hover` | `#173B66` | Primary hover |
| `--color-primary-soft` | `#EAF2FF` | Selected nav, light emphasis |
| `--color-link` | `#1D4ED8` | Links only |

#### Semantic colors

| Token | Hex | Usage |
|---|---:|---|
| `--color-success` | `#16A34A` | Passed, supported, completed |
| `--color-success-soft` | `#DCFCE7` | Success badge background |
| `--color-warning` | `#D97706` | Warnings, assumptions |
| `--color-warning-soft` | `#FEF3C7` | Warning badge background |
| `--color-danger` | `#DC2626` | Failed, contradicted, critical |
| `--color-danger-soft` | `#FEE2E2` | Error badge background |
| `--color-info` | `#0284C7` | Running, active process, info messages |
| `--color-info-soft` | `#E0F2FE` | Info badge background |
| `--color-purple` | `#7C3AED` | Socrates/persona emphasis |
| `--color-purple-soft` | `#EDE9FE` | Persona badge background |
| `--color-teal` | `#0D9488` | Evidence freshness/current source |
| `--color-teal-soft` | `#CCFBF1` | Evidence freshness badge background |
| `--color-azure-chip` | `#2563EB` | Azure service chips only |
| `--color-azure-chip-soft` | `#DBEAFE` | Azure service chip background |

### 9.2 Color semantic rules

- `link` is only for navigation/action links.
- `info` is for process state and active execution.
- `azure-chip` is for Azure service tags.
- `purple` must be used consistently for Socrates mode, persona group badges, and reasoning emphasis.
- `teal` must be used consistently for evidence freshness/current-source indicators.
- Do not use color alone; pair with text and icons.

### 9.3 Tailwind token mapping

```ts
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        app: '#F6F8FB',
        surface: '#FFFFFF',
        muted: '#F1F5F9',
        border: '#E2E8F0',
        primary: {
          DEFAULT: '#0F2A4A',
          hover: '#173B66',
          soft: '#EAF2FF',
        },
        link: '#1D4ED8',
        success: {
          DEFAULT: '#16A34A',
          soft: '#DCFCE7',
        },
        warning: {
          DEFAULT: '#D97706',
          soft: '#FEF3C7',
        },
        danger: {
          DEFAULT: '#DC2626',
          soft: '#FEE2E2',
        },
        info: {
          DEFAULT: '#0284C7',
          soft: '#E0F2FE',
        },
        purple: {
          DEFAULT: '#7C3AED',
          soft: '#EDE9FE',
        },
        teal: {
          DEFAULT: '#0D9488',
          soft: '#CCFBF1',
        },
        azureChip: {
          DEFAULT: '#2563EB',
          soft: '#DBEAFE',
        },
      },
      borderRadius: {
        card: '14px',
        panel: '18px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 23, 42, 0.06)',
        elevated: '0 12px 28px rgba(15, 23, 42, 0.12)',
      },
    },
  },
}
```

---

## 10. Typography

### 10.1 Font stack

Recommended font stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Use monospace only for:

- Mermaid source.
- JSON debug output.
- IDs and technical logs.
- Code snippets.

```css
font-family: "JetBrains Mono", "SFMono-Regular", Consolas, "Liberation Mono", monospace;
```

### 10.2 Type scale

| Token | Size | Weight | Usage |
|---|---:|---:|---|
| `text-display` | 32px | 700 | Home hero heading only |
| `text-page-title` | 26px | 700 | Page titles |
| `text-section-title` | 18px | 650 | Card/section headings |
| `text-card-title` | 15px | 650 | Card titles |
| `text-body` | 14px | 400 | Main body text |
| `text-body-strong` | 14px | 600 | Important row labels |
| `text-table-body` | 13px | 400 | Dense tables |
| `text-caption` | 12px | 500 | Metadata, labels |
| `text-micro` | 11px | 600 | Badges, compact metrics only |

### 10.3 Typography rules

- Use sentence case for headings.
- Avoid ALL CAPS except tiny status badges.
- Table body text should be 13px minimum.
- 11px text is reserved for badges and tiny metadata only.
- Muted-gray table text must still pass contrast expectations.

---

## 11. Spacing and Sizing

### 11.1 Spacing scale

| Token | Value | Usage |
|---|---:|---|
| `space-1` | 4px | Tight icon gaps |
| `space-2` | 8px | Badge/card internal gaps |
| `space-3` | 12px | Form and row gaps |
| `space-4` | 16px | Card padding minimum |
| `space-5` | 20px | Medium panel padding |
| `space-6` | 24px | Page section spacing |
| `space-8` | 32px | Major sections |

### 11.2 Standard dimensions

| Element | Size |
|---|---:|
| Left nav width | 264px |
| Collapsed nav width | 72px |
| Top bar height | 64px |
| Page horizontal padding | 24px |
| Right drawer width | 420–520px |
| Card border radius | 14px |
| Panel border radius | 18px |
| Badge height | 22–26px |
| Table row height | 56–68px |

---

## 12. Core Components

### 12.1 AppShell

Purpose: Global shell with left navigation, top bar, main content area, and optional right drawer.

```ts
type AppShellProps = {
  children: React.ReactNode
  rightPanel?: React.ReactNode
  activeNavItem: string
  uiMode: 'demo' | 'product'
}
```

Rules:

- Left nav remains visible on desktop.
- Top bar contains search, notifications, help, and user profile.
- Main content scrolls independently.
- Right drawer may overlay or dock depending on screen size.
- Use one canonical logo and one canonical search placeholder.

### 12.2 PageHeader

```ts
type PageHeaderProps = {
  breadcrumb: string[]
  title: string
  description?: string
  actions?: React.ReactNode
  badges?: React.ReactNode
}
```

Rules:

- Breadcrumb above title.
- Title and actions aligned horizontally.
- Demo/readiness badges only appear when enabled.

### 12.3 MetricCard

```ts
type MetricCardProps = {
  label: string
  value: string | number
  icon?: React.ReactNode
  trend?: string
  status?: 'neutral' | 'success' | 'warning' | 'danger' | 'info'
  progress?: number
}
```

Rules:

- Keep values large and clear.
- Trend text should be short.
- Use semantic color only when meaningful.

### 12.4 StatusBadge

```ts
type StatusBadgeProps = {
  variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'purple' | 'teal'
  children: React.ReactNode
  icon?: React.ReactNode
}
```

Common badge mappings:

| Meaning | Variant | Label |
|---|---|---|
| Stage completed | success | `✓ Completed` |
| Stage running | info | `● Running` |
| Stage pending | neutral | `Pending` |
| Stage failed | danger | `✕ Failed` |
| Gate passed | success | `✓ Passed` |
| Gate warning | warning | `⚠ Passed with warnings` |
| Gate failed | danger | `✕ Failed` |
| Fact | info | `Fact` |
| Assumption | warning | `Assumption` |
| Recommendation | success | `Recommendation` |
| Socrates/persona | purple | `Persona` |
| Current/fresh evidence | teal | `Current` |
| High trust | success | `High trust` |
| Medium trust | warning | `Medium trust` |
| Low trust | danger | `Low trust` |

### 12.5 QualityGateBadge

```ts
type QualityGateStatus = 'passed' | 'passed_with_warnings' | 'failed'
```

| Status | Badge |
|---|---|
| `passed` | Green `✓ Passed` |
| `passed_with_warnings` | Amber `⚠ Passed with warnings` |
| `failed` | Red `✕ Failed` |

Rules:

- Always include icon + text.
- Do not rely on color alone.
- Clicking badge opens gate detail drawer.

### 12.6 DataTable

Use for requirements, claims, evidence, session lists, artifact lists, and traceability.

Features:

- Sticky header where useful.
- Row hover state.
- Optional row selection.
- Status badge cells.
- Compact filters.
- Right drawer on row click.
- Pagination only if dataset is large.

Rules:

- Tables must not show raw nested JSON.
- Use summary columns and detail drawers.
- Table rows must not rely only on color.
- Tradeoff matrix cells must include both label and color/icon, for example `✓ Best`, `● Good`, `⚠ Fair`, `✕ Weak`.

### 12.7 RightDrawer

```ts
type RightDrawerProps = {
  title: string
  subtitle?: string
  open: boolean
  onClose: () => void
  tabs?: React.ReactNode
  children: React.ReactNode
}
```

Rules:

- Use 420–520px width.
- Keep primary facts at top.
- Put raw/debug data in a collapsed section.
- Use tabs if content exceeds one screen.

---

## 13. Live Reasoning Trace

### 13.1 Purpose

The Live Reasoning Trace is the core interaction pattern that makes backend orchestration visible.

It shows **structured reasoning events**, not hidden model chain-of-thought.

Examples:

```text
Requirements Engineer started
Retrieved 4 Foundry IQ sources
Extracted 5 functional requirements and 6 NFRs
Quality gate passed with warnings

Socrates Standard Mode started
Security Architect reviewing PCI-DSS scope
FinOps Lead evaluating throughput cost sensitivity
Synthesizer producing recommendation
```

### 13.2 Snapshot-then-stream model

The UI must not depend on a perfect uninterrupted SSE connection.

When opening or reloading a session screen:

1. Fetch the current screen snapshot through the relevant view API.
2. Fetch recent persisted events for the active session/stage.
3. Open SSE stream with `Last-Event-ID` if available.
4. Merge incoming events into the live-events store idempotently.
5. If SSE disconnects, reconnect with backoff and replay from last received event ID.
6. If replay is not available, refetch snapshot and continue streaming.

Required endpoints:

```text
GET /api/v1/sessions/{session_id}/events?after_event_id={event_id}
GET /api/v1/sessions/{session_id}/events/stream
```

### 13.3 Event model

```ts
type ReasoningEvent = {
  id: string
  sequence: number
  timestamp: string
  eventType:
    | 'stage_started'
    | 'stage_completed'
    | 'stage_failed'
    | 'agent_started'
    | 'agent_completed'
    | 'persona_started'
    | 'persona_completed'
    | 'persona_finding'
    | 'tool_call_started'
    | 'tool_call_completed'
    | 'evidence_retrieved'
    | 'quality_gate_updated'
    | 'artifact_created'
    | 'claim_validation_updated'
    | 'change_impact_started'
    | 'change_impact_completed'
    | 'rerun_started'
    | 'rerun_completed'
    | 'diff_created'
  sessionId: string
  stage?: string
  stageRunId?: string
  actor?: string
  title: string
  message?: string
  status?: 'running' | 'completed' | 'failed' | 'warning'
  metadata?: Record<string, unknown>
}
```

### 13.4 Visual rules

- Use newest-at-bottom in timeline-style traces.
- Use newest-at-top only in audit feeds and tables.
- Running events use an animated dot and soft info background.
- Completed events use green check.
- Warnings use amber triangle.
- Failures use red icon.
- Tool calls are collapsed by default.
- Evidence retrieval events show count, trust, and freshness summary.
- Persona events update persona cards and trace entries together.

### 13.5 Live micro-transitions

Persona cards and stage rows must visibly transition as events arrive.

| State | Visual behavior |
|---|---|
| Pending | Muted icon, neutral border, no animation |
| Running | Soft info/purple tint, animated dot, elapsed timer, current focus text |
| Completed | Green check, completed timestamp, finding summary visible |
| Warning | Amber border/badge, warning summary visible |
| Failed | Red badge, retry/action link where applicable |
| Partial success | Amber badge, completed/failed count visible |

Socrates persona cards should show a compact mid-flight state:

```text
Security Architect
Running
Reviewing PCI-DSS scope, trust boundaries, and data exposure paths...
```

---

## 14. Screen Specifications

## 14.1 Home / Architecture Command Center

Purpose: Landing dashboard and demo/product control center.

Must show:

- Active sessions.
- Quality gate summary.
- Evidence coverage.
- Socrates findings.
- Open assumptions.
- Recent sessions.
- Architecture readiness or demo readiness.
- New session and Run demo scenario buttons.

Components:

- `MetricCard`
- `RecentSessionsTable`
- `ReadinessPanel`
- `RecentArtifactsList`
- `ChangeActivityList`

Readiness dimensions:

| Dimension | Demo label | Production label | Source |
|---|---|---|---|
| Reliability | Reliability | Workflow reliability | Stage completion, failures, retries |
| Reasoning | Reasoning | Reasoning coverage | Socrates persona coverage, blind spots, synthesis |
| Accuracy | Accuracy | Evidence quality | Evidence coverage, supported claim ratio |
| UX | User Experience | Artifact usability | Artifact rendering health, no raw JSON fallback |
| Creativity | Creativity | Change intelligence | Change impact and diff availability |

First-run zero state:

```text
Welcome to Archimedes
Start with a business need, run the architecture pipeline, and watch agents create an evidence-backed architecture package.

[New Architecture Session] [Run Demo Scenario]
```

### 14.2 Intake Workspace

Purpose: Capture business need and structured context.

Must show:

- Business need prompt box.
- Structured context fields.
- Requirement completeness meter.
- Detected items.
- Missing items.
- Open questions.
- Suggested demo scenarios.
- Extracted seed requirement chips.

Components:

- `BusinessNeedInput`
- `ContextFieldGrid`
- `RequirementCompletenessPanel`
- `RequirementChipList`
- `OpenQuestionsPanel`

Rules:

- Business need text area is primary.
- Structured fields should support edits before pipeline run.
- Requirement changes after pipeline execution must call requirement-change APIs, not restart the pipeline.
- Missing items are warnings unless quality gates make them blockers.

### 14.3 Architecture Pipeline

Purpose: Show lifecycle state, quality gates, metrics, and execution trace.

Must show:

- 10 normal pipeline stages plus re-reasoning stage.
- Stage status.
- Quality gate status.
- Duration.
- LLM calls.
- Tool calls.
- Evidence count.
- Retry count.
- Selected stage drawer.
- Live execution timeline.

Components:

- `PipelineStageList`
- `PipelineStageCard`
- `StageDetailDrawer`
- `QualityGateBadge`
- `LiveReasoningTrace`

Stage status values:

```text
pending | running | completed | failed | skipped | paused | waiting_for_user
```

Quality gate values:

```text
passed | passed_with_warnings | failed
```

Rules:

- Running stage must be visually obvious.
- Warnings should be visible but not alarming unless blocking.
- Failed stage should show retry action and failure reason.
- Clicking a stage opens detail drawer.
- Pipeline must have a first-class nav entry.

### 14.4 Requirements Review

Purpose: Show structured extracted requirements.

Must show:

- Functional requirements.
- Non-functional requirements.
- Constraints.
- Assumptions.
- Open questions.
- Confidence.
- Evidence status.
- User validation status.
- Traceability to stages.

Components:

- `RequirementsMatrix`
- `RequirementRow`
- `AssumptionValidationCard`
- `TraceabilityTable`
- `OpenQuestionsPanel`

```ts
type RequirementRowView = {
  id: string
  description: string
  category: string
  priority: 'must' | 'should' | 'could' | 'wont'
  confidence: 'high' | 'medium' | 'low'
  evidenceStatus: 'verified' | 'partial' | 'assumed' | 'unsupported'
  requiresValidation: boolean
  impactedStages: string[]
}
```

### 14.5 Pattern Explorer

Purpose: Show architecture patterns detected before option generation.

Must show:

- Primary patterns.
- Secondary patterns.
- Confidence.
- Why detected.
- Triggering requirements.
- Recommended Azure services.
- Evidence sources.
- Design implications.

Components:

- `PatternCard`
- `PatternEvidencePanel`
- `TriggeredByChips`
- `DesignImplicationsPanel`

Rules:

- Pattern confidence should not imply final architecture certainty.
- Evidence should be shown as supporting context.
- Pattern cards should drive the Options stage.

### 14.6 Architecture Options Board

Purpose: Compare candidate architecture options.

Must show:

- 2–4 viable options.
- At least one rejected option.
- Recommended option.
- Main services.
- Fit score.
- Complexity.
- Cost band.
- Reliability fit.
- Security fit.
- Operational burden.
- Trade-off matrix.

Components:

- `ArchitectureOptionCard`
- `OptionServiceIconList`
- `TradeoffMatrix`
- `RecommendationSummaryPanel`

Option status mapping:

| Status | Visual treatment |
|---|---|
| Recommended | Green badge, stronger border |
| Viable | Blue badge |
| Needs validation | Amber badge |
| Rejected | Muted/red badge |

Trade-off matrix accessibility:

| Rating | Label |
|---|---|
| Best | `✓ Best` |
| Good | `● Good` |
| Fair | `⚠ Fair` |
| Weak | `✕ Weak` |

### 14.7 Socrates Reasoning Lab

Purpose: The main reasoning showcase.

Must show:

- Socrates mode: Light / Standard / Deep.
- Persona cards.
- Persona status.
- Persona finding.
- Severity.
- Confidence.
- Decision under review.
- Key requirements.
- Major assumptions.
- Synthesizer output.
- Blind spots.
- Pre-mortem.
- Confidence score.
- Conditions for approval.
- Live reasoning trace.

Components:

- `SocratesModeBanner`
- `PersonaFindingCard`
- `DecisionUnderReviewCard`
- `SocraticSynthesisPanel`
- `BlindSpotList`
- `PremortemList`
- `ConditionsForApprovalList`
- `LiveReasoningTrace`

```ts
type PersonaFindingView = {
  persona: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  confidence: number
  finding: string
  recommendation?: string
  linkedRequirements: string[]
  linkedEvidenceCount: number
}
```

Rules:

- Standard mode must show 5 personas plus Synthesizer.
- Persona findings must reference actual scenario details.
- Do not show raw model chain-of-thought.
- Show concise, actionable reviewer findings.
- Synthesizer owns the final recommendation, not any single persona.
- Persona failures should show partial success if minimum threshold is met.

### 14.8 Evidence & Claims Explorer

Purpose: Make accuracy, trust, and auditability visible.

Must show:

- Claims supported.
- Evidence coverage.
- Unsupported assumptions.
- Contradictions.
- Freshness score.
- Claim table.
- Filters.
- Claim detail drawer.
- Evidence source detail.
- User validation controls for assumptions.

Components:

- `EvidenceKpiStrip`
- `ClaimsTable`
- `ClaimDetailDrawer`
- `EvidenceSourceCard`
- `AssumptionValidationControls`
- `ContradictionsPanel`

Claim statuses:

```text
supported | weak_evidence | needs_user_validation | stale | contradicted | unsupported
```

Evidence trust levels:

```text
high | medium | low
```

Freshness values:

```text
current | recent | stale | unknown
```

Rules:

- Facts without evidence should be flagged.
- Assumptions should be visible and actionable.
- Recommendations should link to supporting facts/assumptions.
- Low-trust evidence should not appear as strong support.

### 14.9 Artifact Studio

Purpose: Render professional architecture artifacts.

Must show tabs:

```text
Requirements | Options | Socrates Brief | ADR | HLD | Mermaid Diagram | Mini WAF Review | Evidence Report
```

Must show artifact metadata:

- Version.
- Stage.
- Quality gate status.
- Evidence coverage.
- Created time.
- Change event reference, if regenerated.
- Export/copy actions.

Components:

- `ArtifactTabs`
- `AdrRenderer`
- `HldRenderer`
- `WafPillarCards`
- `MermaidViewer`
- `ArtifactMetadataPanel`
- `ExportActions`

Rules:

- Avoid raw JSON by default.
- Provide debug/source view as collapsed panel.
- ADR should render as Context, Decision, Alternatives, Consequences, Risks, Evidence.
- HLD should render narrative and diagrams.
- WAF should render five pillar cards.

### 14.10 Mermaid Diagram Viewer

Purpose: Render architecture diagrams safely.

Must show:

- Diagram type selector.
- Rendered Mermaid diagram.
- Source fallback.
- Render status.
- Component explanation.
- Trust boundaries and data flows, where available.

Components:

- `MermaidViewer`
- `DiagramTypeTabs`
- `DiagramExplanationPanel`
- `RenderStatusBadge`

Render statuses:

```text
not_checked | render_passed | render_warning | render_failed
```

Badge logic:

| Case | Artifact quality gate | Render badge | UI message |
|---|---|---|---|
| Artifact passed and diagram rendered | Passed | Render passed | Show rendered diagram. |
| Artifact passed but diagram render failed | Passed | Render failed | Show source fallback and error. Do not mark artifact failed solely due to renderer. |
| Artifact passed with warnings and render failed | Passed with warnings | Render failed | Show both gate warning and render fallback. |
| HLD gate failed due to invalid diagram content | Failed | Render failed | Show blocking failure and retry action. |

Rules:

- If rendering fails, show source plus error message.
- Do not block artifact viewing because browser-side diagram rendering failed.
- Do not conflate artifact quality gate with diagram render status.

### 14.11 Change Impact Studio

Purpose: Showcase selective re-reasoning and before/after diffs.

Must show:

- Requirement change summary.
- Before/after cards.
- Impact map.
- Stable stages.
- Impacted stages.
- Selective re-run plan.
- Created artifact versions.
- Before/after diff table.
- Run impact analysis and apply re-run actions.

Components:

- `RequirementChangeSummary`
- `BeforeAfterCards`
- `ImpactMap`
- `RerunPlanPanel`
- `ArtifactVersionList`
- `BeforeAfterDiffTable`
- `LiveReasoningTrace`

Change impact values:

```text
stable | impacted | high_impact | audit_only | skipped
```

Rules:

- Never silently mutate architecture artifacts.
- Always show what changed and why.
- Link regenerated artifacts to the triggering change event.
- Show work saved by selective re-run when available.
- Regenerated versions become active automatically only if quality gates pass, unless future approval workflow is enabled.

---

## 15. Interaction Patterns

### 15.1 Drawers over navigation

Use right-side drawers for detailed inspection:

- Claim details.
- Evidence source details.
- Stage details.
- Persona details.
- Artifact metadata.
- Change event details.

### 15.2 Tabs for artifact families

Use tabs when switching between related views:

- Artifact Studio tabs.
- Evidence Explorer tabs.
- Socrates finding categories.

### 15.3 Progressive disclosure

Default view should show summaries. Deeper technical detail should be available through:

- Expanders.
- Drawers.
- Debug tabs.
- Source view.
- Raw JSON view, hidden by default.

### 15.4 Command/chat behavior

The UI may include a ChatGPT/Claude-like command panel, but it must be architecture-workbench aware.

Rules:

- First business-need input creates or updates the architecture session.
- `Start Architecture Pipeline` triggers pipeline execution.
- Follow-up requirement changes call requirement-change APIs.
- Chat should not dominate the screen; it complements the pipeline, artifacts, and evidence panels.
- Chat responses should surface stage/gate/evidence summaries, not only free-form text.

---

## 16. Loading, Empty, Error, and Running States

### 16.1 Loading state

Use skeleton cards/tables for initial data loading.

Examples:

- Dashboard KPI skeletons.
- Pipeline stage skeletons.
- Claims table skeleton rows.

### 16.2 Running state

Running stage should show:

- Spinner or animated dot.
- Current activity message.
- Last event timestamp.
- Elapsed time.
- Link/button to view live trace.

### 16.3 First-run zero state

A brand-new account with no sessions must show a useful landing state.

Required content:

```text
No architecture sessions yet.
Start a new architecture session or run the fintech fraud detection demo scenario.
```

Actions:

```text
[New Architecture Session]
[Run Demo Scenario]
[View sample architecture package]
```

### 16.4 Empty state

Empty screens should explain the next action.

Example:

```text
No evidence audit yet.
Run the Evidence Audit Checkpoint stage to validate claims and sources.
```

### 16.5 Error state

Errors should include:

- Clear title.
- Human-readable message.
- Failure reason, if available.
- Retry action, if safe.
- Link to debug details for developers.

### 16.6 Partial success state

Show partial success clearly.

Example:

```text
Socrates completed with 4 of 5 personas.
Delivery Lead timed out. Synthesizer used available findings.
```

---

## 17. Accessibility Rules

Minimum expectations:

- All status colors must include text/icons.
- Keyboard focus states must be visible.
- Buttons and interactive rows must have accessible labels.
- Table rows should not rely only on color.
- Trade-off matrix cells must include labels, not just dots.
- Use sufficient contrast for text and badges.
- Avoid tiny text below 11px.
- Use 13px minimum for table body text.
- Motion should be subtle and not required for understanding.

Badge examples:

```text
✓ Passed
⚠ Passed with warnings
✕ Failed
```

Avoid:

```text
Only green/yellow/red dots with no label
```

---

## 18. API and View Model Alignment

React must consume screen-ready view APIs.

### 18.1 Required view APIs

```text
GET /api/v1/dashboard/summary
GET /api/v1/sessions
GET /api/v1/sessions/{session_id}/overview
GET /api/v1/sessions/{session_id}/pipeline/view
GET /api/v1/sessions/{session_id}/requirements/view
GET /api/v1/sessions/{session_id}/patterns/view
GET /api/v1/sessions/{session_id}/options/view
GET /api/v1/sessions/{session_id}/socrates/view
GET /api/v1/sessions/{session_id}/evidence/view
GET /api/v1/sessions/{session_id}/artifacts/package-view
GET /api/v1/sessions/{session_id}/changes/{change_event_id}/impact-view
GET /api/v1/sessions/{session_id}/events
GET /api/v1/sessions/{session_id}/events/stream
```

### 18.2 Mutating APIs used by frontend

```text
POST /api/v1/sessions
POST /api/v1/sessions/{session_id}/pipeline/run-next
POST /api/v1/sessions/{session_id}/pipeline/stages/{stage_id}/run
POST /api/v1/sessions/{session_id}/changes
POST /api/v1/sessions/{session_id}/changes/{change_event_id}/rerun
POST /api/v1/sessions/{session_id}/claims/{claim_id}/validate
```

### 18.3 Design rule

React components must not parse raw artifact JSON to infer business meaning.

Backend should provide DTOs such as:

- `DashboardSummaryView`
- `SessionOverviewView`
- `PipelineView`
- `RequirementsReviewView`
- `PatternExplorerView`
- `OptionsBoardView`
- `SocratesReasoningView`
- `EvidenceExplorerView`
- `ArtifactPackageView`
- `ChangeImpactView`

### 18.4 View model expectations

Each screen view model should include:

- `session_id`
- `active_version`
- `current_stage`
- `quality_gate_summary`
- screen-specific data
- `last_updated_at`
- `source_artifact_versions`
- `warnings`
- `feature_flags`

---

## 19. Recommended Frontend Folder Structure

```text
apps/web/
  src/
    app/
      layout.tsx
      page.tsx
      sessions/
      intake/
      pipeline/
      requirements/
      patterns/
      options/
      socrates/
      evidence/
      artifacts/
      changes/
      settings/
    components/
      app-shell/
      badges/
      cards/
      data-table/
      drawer/
      forms/
      layout/
      mermaid/
      metrics/
      tabs/
      timeline/
    features/
      dashboard/
      sessions/
      intake/
      pipeline/
      requirements/
      patterns/
      options/
      socrates/
      evidence/
      artifacts/
      changes/
      live-trace/
    lib/
      api-client.ts
      query-client.ts
      sse-client.ts
      formatters.ts
      routes.ts
    stores/
      session-store.ts
      ui-store.ts
      live-events-store.ts
    types/
      api.ts
      view-models.ts
      domain.ts
    styles/
      globals.css
```

---

## 20. Component Inventory

### 20.1 Shared components

| Component | Purpose |
|---|---|
| `AppShell` | Global layout |
| `LeftNav` | Navigation |
| `TopBar` | Search/profile/actions |
| `PageHeader` | Breadcrumb/title/actions |
| `MetricCard` | KPI summary |
| `StatusBadge` | Generic status |
| `QualityGateBadge` | Quality gate status |
| `EvidenceTrustBadge` | Evidence trust |
| `FreshnessBadge` | Evidence freshness |
| `ClaimTypeBadge` | Fact/assumption/recommendation |
| `RightDrawer` | Detail inspection |
| `DataTable` | Structured tabular data |
| `LiveReasoningTrace` | Agent orchestration visibility |
| `MermaidViewer` | Diagram rendering |
| `DiffViewer` | Before/after comparison |
| `ReadinessPanel` | Demo/product readiness metrics |
| `GlobalSearch` | Search across sessions/artifacts/claims |

### 20.2 Feature components

| Feature | Components |
|---|---|
| Dashboard | `RecentSessionsTable`, `ReadinessPanel`, `RecentArtifactsList` |
| Sessions | `SessionList`, `SessionCard`, `SessionStatusBadge` |
| Intake | `BusinessNeedInput`, `ContextFieldGrid`, `RequirementCompletenessPanel` |
| Pipeline | `PipelineStageList`, `StageDetailDrawer`, `ExecutionTimeline` |
| Requirements | `RequirementsMatrix`, `OpenQuestionsPanel`, `TraceabilityTable` |
| Patterns | `PatternCard`, `PatternEvidencePanel`, `DesignImplicationsPanel` |
| Options | `ArchitectureOptionCard`, `TradeoffMatrix`, `RecommendationSummaryPanel` |
| Socrates | `PersonaFindingCard`, `SocraticSynthesisPanel`, `DecisionUnderReviewCard` |
| Evidence | `ClaimsTable`, `ClaimDetailDrawer`, `EvidenceSourceCard` |
| Artifacts | `AdrRenderer`, `HldRenderer`, `WafPillarCards`, `ArtifactMetadataPanel` |
| Change Impact | `ImpactMap`, `RerunPlanPanel`, `BeforeAfterDiffTable` |

---

## 21. Mockup Alignment Decisions

The generated mockups remain the visual target, with these corrections applied during implementation.

| Mockup area | Keep | Update |
|---|---|---|
| Overall visual language | Light enterprise cards, navy actions, pale blue selected states, detail drawers | Standardize nav labels and logo |
| Home dashboard | KPI cards, recent sessions, readiness panel | Feature-flag demo judging copy and provide product copy |
| Intake | Prompt box, completeness panel, open questions | Align nav and top search |
| Pipeline | Stage table, quality gates, right drawer, execution trace | Ensure `Pipeline` nav item exists |
| Requirements | Requirement matrix and open questions | Raise table body to 13px minimum |
| Pattern Explorer | Pattern cards and evidence panel | Use canonical service chips and evidence freshness tokens |
| Options | Option cards and matrix | Add labels/icons to matrix cells, not color dots only |
| Socrates | Persona cards, synthesis, confidence, conditions | Use purple Socrates/persona emphasis consistently |
| Evidence | Claims table and claim drawer | Use teal for freshness, green/amber/red for trust |
| Artifact Studio | ADR/HLD/WAF tabs and Mermaid preview | Separate quality gate badge from render status badge |
| Change Impact | Before/after cards, impact map, rerun plan, diff | Ensure artifact versions link to `change_event_id` |

---

## 22. Implementation Phases

### Phase 1 — Foundation

Build:

- Next.js app shell.
- Tailwind tokens.
- Canonical left navigation.
- Top bar and global search shortcut.
- Shared cards, badges, drawers, tables.
- API client and TanStack Query setup.
- Zustand UI/session/live-events stores.
- Mock data support.

Screens:

- Home zero state.
- Sessions list.
- Pipeline skeleton.

### Phase 2 — Hero demo screens

Build:

1. Architecture Pipeline.
2. Socrates Reasoning Lab.
3. Evidence & Claims Explorer.
4. Artifact Studio.
5. Change Impact Studio.

Add:

- SSE live trace.
- Snapshot-then-stream behavior.
- View-model API integration.
- Drawer interactions.
- Demo/product copy feature flag.

### Phase 3 — Full workbench

Build:

- Intake Workspace.
- Requirements Review.
- Pattern Explorer.
- Options Board.
- Mermaid Diagram Viewer.
- Version History.

### Phase 4 — Product hardening

Add:

- Entra ID authentication.
- User/session ownership.
- Export flows.
- Better responsive behavior.
- Test automation.
- Accessibility pass.

---

## 23. Acceptance Criteria

The React UI is acceptable when:

1. A user can create or load an architecture session.
2. A first-run user with no sessions sees useful zero-state actions.
3. The Pipeline screen shows stage status, quality gates, metrics, and live orchestration events.
4. Pipeline is a first-class navigation item.
5. Socrates shows Standard mode with 5 personas plus Synthesizer.
6. Each Socrates persona can show pending, running, completed, failed, and partial-success states.
7. Persona findings are specific to the architecture context and do not expose raw chain-of-thought.
8. Evidence Explorer shows claims, evidence, trust, freshness, contradictions, and assumptions.
9. Assumptions requiring validation can be accepted/rejected/commented from the UI.
10. Artifact Studio renders ADR, HLD, WAF, Mermaid, and evidence report without raw JSON as the default.
11. Diagram render status and artifact quality gate status are visibly separate.
12. Change Impact Studio shows before/after requirement changes, impacted/stable stages, re-run plan, created versions, and diff.
13. Live backend activity survives reload using snapshot-then-stream and event replay/catch-up.
14. Table cells and badges do not rely only on color.
15. Demo-only judging/readiness copy is behind a feature flag.
16. The UI preserves the generated mockup visual style while using canonical IA and tokens.
17. Errors, loading, empty, running, and partial-success states are handled cleanly.
18. The app is demo-ready on laptop/desktop screen widths.

---

## 24. Non-Goals for First React Version

Do not attempt in the first version:

- Full mobile-first responsive redesign.
- Full RBAC and enterprise tenant management.
- Native diagram editing.
- Complex drag/drop workflow editing.
- Deep collaboration/commenting.
- Full design-token theming engine.
- Moving orchestration to Next.js.
- Exposing raw model chain-of-thought.
- Recreating Streamlit UI behavior literally.

---

## 25. Open Decisions

| Decision | Current direction |
|---|---|
| Next.js rendering mode | Mostly client-side interactive workbench screens. Use server components only where useful and simple. |
| Component base | shadcn/ui plus custom Archimedes design components. |
| First deployment target | Azure Static Web Apps or Container Apps static frontend; backend remains FastAPI on Container Apps. |
| Live events | SSE first, WebSocket later only if required. |
| Demo/product mode | Feature flag using `UiMode = 'demo' | 'product'`. |
| Grouped full IA | Defer until MVP screens are stable. |
| Ontology/Governance/Integrations nav | Hide or disable as future product capabilities. |

---

## Appendix A — Legacy Streamlit UI Mapping

This appendix captures the parts of `14a` that remain valid after retiring Streamlit.

### A.1 Legacy goals retained

| Legacy goal | React equivalent |
|---|---|
| Make architecture reasoning visible | Pipeline screen, live reasoning trace, stage drawers |
| Make Socrates a demo highlight | Socrates Reasoning Lab |
| Make re-reasoning obvious | Change Impact Studio |
| Keep chat visible but not dominant | Optional command panel / Socrates assistant drawer |
| Show pipeline timeline prominently | Pipeline first-class screen |
| Use tabs for artifacts and evidence | Artifact Studio and Evidence Explorer tabs |
| Use badges for stage status and gates | `StatusBadge`, `QualityGateBadge` |
| Make before/after changes visual | `BeforeAfterCards`, `DiffViewer` |
| Avoid raw JSON unless debug mode | Collapsed Debug/Source panels only |

### A.2 Legacy components mapped to React

| Streamlit concept | React/Next.js replacement |
|---|---|
| Header | `TopBar` + `PageHeader` |
| Sidebar | `LeftNav` inside `AppShell` |
| Session selector | `Sessions` screen + session switcher |
| Chat/intake panel | `Intake Workspace` + optional command panel |
| Pipeline timeline | `Architecture Pipeline` screen |
| Stage event stream | `LiveReasoningTrace` |
| Artifact tabs | `ArtifactStudio` tabs |
| Socrates debate view | `SocratesReasoningLab` |
| Evidence/claims view | `EvidenceClaimsExplorer` |
| Mermaid render panel | `MermaidViewer` |
| Before/after diff view | `ChangeImpactStudio` + `DiffViewer` |
| Developer/debug toggle | Collapsed Debug tab or feature-flagged developer mode |

### A.3 Legacy session controls retained

React must preserve these user actions:

```text
New Session
Load Session
Load Demo Scenario
Refresh Status
Reset Demo
Start Architecture Pipeline
Submit Requirement Change
Retry Failed Stage
Validate Assumption
Export Artifact Package
```

### A.4 Legacy stage timeline retained

The React pipeline must preserve the 11-stage lifecycle:

```text
1. Intake
2. Requirements Extraction
3. Pattern Detection
4. Options Generation
5. Socratic Review
6. Evidence Audit Checkpoint
7. ADR Generation
8. HLD + Mermaid Diagrams
9. Mini WAF Review
10. Final Evidence Audit
11. Requirement Change / Re-reasoning / Diff
```

### A.5 Legacy event model retained and expanded

Legacy event types retained:

```text
stage_started
stage_completed
stage_failed
quality_gate_result
artifact_generated
evidence_audit_completed
requirement_change_detected
rereasoning_started
rereasoning_completed
```

React expands these into the structured event model in Section 13.

### A.6 Legacy artifact tabs retained

Legacy tabs retained as Artifact Studio tabs:

```text
Requirements
Options
Socrates
ADR
HLD
WAF
Evidence
Diff
Debug
```

The React implementation should rename where appropriate:

| Legacy tab | React label |
|---|---|
| Socrates | Socrates Brief |
| WAF | Mini WAF Review |
| Evidence | Evidence Report |
| Diff | Change Diff / Before-After Diff |
| Debug | Source / Debug, collapsed |

---

## Appendix B — Feedback Punch List Applied

| Feedback item | Resolution in this spec |
|---|---|
| Three competing nav vocabularies | Canonical MVP nav defined; mockup-only labels retired or future/disabled. |
| Pipeline missing from nav | Pipeline is first-class navigation item. |
| 14a and 14b conflict | Consolidated into one `14-frontend-specification.md`; Streamlit moved to legacy appendix. |
| Wrong document ID | Fixed to `14-frontend-specification.md`. |
| Logo inconsistency | Flat `A` monogram selected for app shell; 3D visual allowed only as illustration. |
| Search placeholder inconsistency | Single placeholder and `/` shortcut defined. |
| Demo chrome in product UI | Demo/product feature flag defined. |
| SSE reconnect/replay under-specified | Snapshot-then-stream model added. |
| Live micro-transitions missing | Persona/stage transition rules added. |
| First-run zero state missing | Zero-state requirements added. |
| Color-only table indicators | Labels/icons required in matrix cells and badges. |
| Blue overloaded | Link/info/Azure chip colors separated. |
| Purple/teal tokens inconsistent | Socrates/persona and evidence freshness usage enforced. |
| Table text density | 13px minimum table body added. |
| Diagram render vs gate pass confusion | Separate render/gate badge logic added. |
| Socrates assistant CTA inconsistent | Persistent CTA rules added. |

---

## Appendix C — Final Direction

The target UI remains the generated enterprise workbench visual style, corrected for consistency and implemented with Next.js.

The most important experience is **live visibility into backend reasoning and orchestration** through structured events, stage status, Socrates persona activity, evidence retrieval, quality gates, and artifact generation.

Archimedes should feel like a serious architecture decision platform: evidence-backed, inspectable, versioned, and impressive during a demo, while remaining suitable for later productization.

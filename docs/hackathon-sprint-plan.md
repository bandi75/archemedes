# Hackathon Sprint Plan — Agents League June 2026

**Track:** Reasoning Agents (Microsoft Foundry)  
**Deadline:** June 14, 2026  
**Remaining time at planning:** 2 days (June 12–13)

---

## Judging Criteria Alignment

| Criterion | Weight | Current State | Primary Gaps |
|---|---|---|---|
| Reliability | 20% | 10-stage pipeline runs end-to-end, KB live | Edge-case crashes, no session list |
| Reasoning | 20% | Multi-agent structure correct, Socrates wired | Persona findings are generic templates |
| Accuracy | 20% | Azure AI Search retrieval working and grounded | Output quality tied to prompt richness |
| User Experience | 15% | Streamlit UI with all major views present | Chat response minimal; raw JSON artifacts |
| Creativity | 15% | Socratic multi-persona challenge is novel | Undersold — README too thin |
| Community | 10% | Public repo planned | No demo, no architecture diagram |

**The single most damaging gap for the "Reasoning Agents" track:**  
`src/archimedes/socrates/persona.py` returns identical template text for every architecture.  
Judges evaluating a *reasoning* agent will notice that "Trust boundaries must be explicit" appears  
regardless of whether the input is a fintech fraud platform or a retail CMS.

---

## Day 1 — June 12: Reasoning + Reliability

### P0 · Context-aware Socrates persona findings
**Criterion impact:** Reasoning (20%)  
**Effort:** ~2 hours  
**File:** `src/archimedes/socrates/persona.py`

`SocratesReviewContext` carries `business_need`, `architecture_options`, `requirements`, and  
`session_context` — none of which is currently used by `_finding_for()`. Every persona returns  
the same hardcoded strings regardless of input.

**Changes required:**
- Extract option names, Azure services, NFRs, and constraints from the context
- Make each persona's finding reference the actual architecture under review
- Devil's Advocate → challenge the primary option's key assumption explicitly
- Security Architect → name the specific services/data sensitivity from the context
- FinOps Lead → reference the scale/throughput numbers from requirements
- SRE/Ops Lead → reference the availability target from requirements
- Delivery Lead → note the complexity signals (number of services, unfamiliar tech)

**Acceptance test:** Run the fintech fraud demo. Socrates output should mention  
"10K TPS", "PCI-DSS", "Event Hubs" or "AKS" — not just generic advice.

---

### P1 · Richer orchestrator chat messages
**Criterion impact:** Reasoning (20%), UX (15%)  
**Effort:** ~1 hour  
**Files:** `frontend/app.py` (line 428), `src/api/routers/sessions.py`

`_format_orchestrator_response` produces one flat line: `"Stage X completed. Produced: Y."`.  
The controller response already carries quality gate status and produced artifacts but the  
frontend discards everything except stage name.

**Changes required:**
- Surface the quality gate decision in the chat message (PASSED / PASSED_WITH_WARNINGS)
- Show how many evidence sources were retrieved for the stage
- Show the key Socratic finding when the stage is `socratic_review`
- Show unresolved assumption count when the evidence audit runs

**Example target output:**
```
Stage requirements_extraction completed (gate: PASSED_WITH_WARNINGS).
Retrieved 3 KB sources. 2 warnings: availability target not defined, compliance not specified.
→ Send your next instruction to advance to pattern detection.
```

---

### P2 · GET /sessions endpoint + sidebar session list
**Criterion impact:** UX (15%), Reliability (20%)  
**Effort:** ~45 minutes  
**Files:** `src/api/routers/sessions.py`, `frontend/api_client.py`, `frontend/app.py`

Judges cannot navigate between sessions. If a session fails mid-run, they have no way  
to reload a prior completed session.

**Changes required:**
- Add `GET /sessions` router handler returning `[{session_id, title, current_stage, created_at}]`
- Add `get_sessions()` method to `ArchimedesApiClient`
- Render a clickable session list in the Streamlit sidebar below the New Session button
- Clicking a session loads it into `st.session_state` and refreshes artifacts

---

### P3 · End-to-end demo smoke test
**Criterion impact:** Reliability (20%)  
**Effort:** ~30 minutes

Run the full fintech fraud demo scenario through all 10 stages.  
Check:
- [ ] All 10 stages complete without HTTP 500
- [ ] Evidence tab shows KB sources for WAF and HLD stages
- [ ] Socrates tab shows all 5 personas with findings
- [ ] Evidence audit tabs show metrics (claims, warnings, quality)
- [ ] Mermaid diagram renders in HLD tab
- [ ] No raw `null` or empty JSON in any artifact tab

Fix any blockers before proceeding to Day 2.

---

## Day 2 — June 13: UX + Community + Submission

### P4 · Assumption validation flow
**Criterion impact:** Reasoning (20%), UX (15%)  
**Effort:** ~2 hours  
**Files:** `src/api/routers/evidence.py`, `src/api/storage.py`, `frontend/app.py`

The `EvidenceAuditor` correctly flags `requires_user_validation` claims and the `StagePatch`  
carries them. There is no API or UI path for the user to respond. This breaks the  
human-in-the-loop reasoning loop that "Reasoning Agents" judges will look for.

**Changes required:**
- Add `POST /sessions/{session_id}/claims/{claim_id}/validate` endpoint  
  (body: `{"accepted": bool, "comment": str | null}`)
- Store the validation decision on the `ClaimRecord`
- In the chat panel, after each evidence audit stage, display unresolved assumptions  
  as expandable prompts with Accept / Reject buttons
- Re-running evidence audit after validation should clear the related finding

---

### P5 · Structured artifact rendering
**Criterion impact:** UX (15%), Accuracy (20%)  
**Effort:** ~1.5 hours  
**File:** `frontend/app.py`

Most artifact tabs show raw JSON. Three views matter most for the demo:

**Requirements** — render as two columns: Functional Requirements | NFRs + Constraints  
**WAF review** — render per-pillar cards with severity badge (Critical / High / Medium)  
**ADR** — render as structured sections: Context → Decision → Alternatives → Consequences  

These three are what judges will click first after creating a session.

---

### P6 · README overhaul
**Criterion impact:** Community (10%), all criteria via first impression  
**Effort:** ~2 hours  
**File:** `README.md`

The current README is minimal. This is the first thing judges read and the only artifact  
that is always reviewed (even if the live demo fails).

**Required sections:**
1. **What Archimedes does** — one paragraph, lead with the reasoning story
2. **Architecture diagram** — Mermaid flowchart of the 10-stage multi-agent pipeline  
   showing Foundry IQ evidence retrieval and Socratic parallel personas
3. **Foundry IQ integration** — explicitly call out how every LLM stage uses  
   `foundry_iq_retrieve` to ground recommendations in Azure Architecture Center docs
4. **Quick start** — 5 commands from clone to running demo
5. **Demo scenario** — screenshot of the Socrates tab showing 5 personas + synthesis
6. **Judging criteria alignment table** — brief paragraph for each criterion

---

### P7 · Submission checklist
**Effort:** ~30 minutes

- [ ] Repository is public
- [ ] `.env.example` contains no real secrets or keys
- [ ] `README.md` is the landing page (not `RUNBOOK.md`)
- [ ] Demo scenario runs end-to-end without manual intervention
- [ ] All 5 Socrates persona findings reference the actual architecture input
- [ ] Evidence tab shows real Azure AI Search source document names
- [ ] Mermaid diagram renders in HLD tab
- [ ] Submission registered at aka.ms/agentsleague/aisf

---

## What to Skip

The following gaps from the full analysis are **not worth touching in 2 days** — zero or  
near-zero impact on judging criteria relative to effort:

| Item | Reason to skip |
|---|---|
| SSE / live streaming | Complex; richer chat messages achieve same perceived effect |
| Typed `options.py` / `requirements.py` Pydantic models | No judge-visible impact |
| Terraform / Bicep IaC | No judging criterion covers deployment automation |
| Application Insights telemetry | No judging criterion |
| Pipeline pause / resume / retry API endpoints | Not on the demo path |
| Cosmos DB transactional batch writes | Correct at demo scale |
| Artifact markdown export / bundle export | Not shown in demo flow |
| Socrates cross-examination (deep adversarial round) | P4 is higher-value than this |

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Context-aware persona changes break Socrates quality gate | Medium | Keep minimum_personas check; test with demo scenario after change |
| GET /sessions query is slow on in-memory storage | Low | In-memory dict scan is negligible at demo scale |
| README diagrams don't render on GitHub | Low | Test Mermaid blocks on GitHub preview before submitting |
| LLM outputs vary and WAF/ADR stage produces poor content | Medium | Review and tighten prompts in `prompts/waf.md` and `prompts/adr.md` if smoke test shows thin output |

---

## Definition of Done

The submission is ready when:
1. A judge can paste the fintech fraud demo scenario, click through 10 stages, and see  
   Socratic findings that explicitly reference PCI-DSS, throughput targets, and Azure services
2. The Evidence tab shows named Azure AI Search documents (not empty)
3. The README explains the multi-agent reasoning pipeline with a diagram
4. The repo is public with no secrets in `.env.example`

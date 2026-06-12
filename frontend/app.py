from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from api_client import ArchimedesApiClient, ArchimedesApiError


STAGES = [
    ("intake", "Intake"),
    ("requirements_extraction", "Requirements"),
    ("pattern_detection", "Pattern"),
    ("options_generation", "Options"),
    ("socratic_review", "Socrates"),
    ("evidence_audit_checkpoint", "Evidence Check"),
    ("adr_generation", "ADR"),
    ("hld_generation", "HLD"),
    ("mini_waf_review", "WAF"),
    ("final_evidence_audit", "Final Audit"),
]

ARTIFACT_STAGES = [
    ("intake", "Intake"),
    ("requirements_extraction", "Requirements"),
    ("pattern_detection", "Pattern"),
    ("options_generation", "Options"),
    ("socratic_review", "Socrates"),
    ("evidence_audit_checkpoint", "Evidence Check"),
    ("adr_generation", "ADR"),
    ("hld_generation", "HLD"),
    ("mini_waf_review", "WAF"),
    ("final_evidence_audit", "Final Audit"),
]

DEMO_NEED = (
    "Design a real-time fraud detection platform on Azure for a fintech processing "
    "10K TPS with PCI-DSS constraints and 99.95% availability."
)


def main() -> None:
    st.set_page_config(page_title="Archimedes", layout="wide")
    _ensure_state()
    client = ArchimedesApiClient()

    _render_header(client)
    _render_sidebar(client)

    chat_col, artifact_col = st.columns([0.42, 0.58], gap="large")
    with chat_col:
        _render_chat_panel(client)
    with artifact_col:
        _render_artifact_workspace(client)


def _ensure_state() -> None:
    defaults = {
        "session_id": None,
        "messages": [],
        "pipeline": {"stages": []},
        "session": None,
        "artifacts": {},
        "last_error": None,
        "debug": False,
        "show_new_session_form": False,
        "is_processing": False,
        "pending_prompt": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _render_header(client: ArchimedesApiClient) -> None:
    top_left, top_right = st.columns([0.7, 0.3])
    with top_left:
        st.title("Archimedes")
        st.caption("Evidence-backed architecture workbench")
    with top_right:
        st.text_input("API URL", value=client.base_url, disabled=True)
        if st.session_state.session_id:
            st.caption(f"Session: {st.session_state.session_id}")

    if st.session_state.last_error:
        st.error(st.session_state.last_error)


def _render_sidebar(client: ArchimedesApiClient) -> None:
    with st.sidebar:
        st.header("Session")
        if st.button("New session", width="stretch"):
            _reset_session()
            st.session_state.show_new_session_form = True
            st.rerun()

        if st.session_state.show_new_session_form:
            _render_new_session_form(client)

        if st.button("Load demo scenario", width="stretch"):
            _create_session(client, DEMO_NEED, title="Fintech fraud detection demo", domain="fintech")
            st.session_state.messages.append({"role": "user", "content": DEMO_NEED})
            st.session_state.show_new_session_form = False
            st.rerun()

        st.session_state.debug = st.toggle("Debug JSON", value=st.session_state.debug)

        _render_session_list(client)

        st.divider()
        _render_session_summary()
        st.divider()
        _render_timeline()

        if st.button("Refresh status", width="stretch", disabled=not st.session_state.session_id):
            _refresh_session_state(client)
            st.rerun()


def _render_session_list(client: ArchimedesApiClient) -> None:
    st.divider()
    st.subheader("Recent Sessions")
    try:
        data = client.get_sessions()
        sessions = data.get("items", [])
    except ArchimedesApiError:
        sessions = []

    if not sessions:
        st.caption("No sessions yet")
        return

    for s in sessions[:10]:
        sid = s.get("session_id", "")
        label = s.get("title") or sid[:12]
        stage = s.get("current_stage") or "—"
        is_active = sid == st.session_state.get("session_id")
        display = f"{'▶ ' if is_active else ''}{label}  \n`{stage}`"
        if st.button(display, key=f"load_session_{sid}", width="stretch"):
            _load_session(client, sid)
            st.rerun()


def _load_session(client: ArchimedesApiClient, session_id: str) -> None:
    try:
        session = client.get_session(session_id)
    except ArchimedesApiError as exc:
        st.session_state.last_error = f"Failed to load session: {exc.detail}"
        return
    st.session_state.session_id = session_id
    st.session_state.session = session
    st.session_state.messages = []
    st.session_state.last_error = None
    _refresh_all(client)


def _render_session_summary() -> None:
    session = st.session_state.session
    if not session:
        st.caption("No active session")
        return
    st.subheader("Current")
    st.write(f"Stage: `{session.get('current_stage')}`")
    st.write(f"Version: `{session.get('active_version')}`")


def _render_timeline() -> None:
    st.subheader("Pipeline")
    stage_status = {
        item.get("stage"): item for item in st.session_state.pipeline.get("stages", [])
    }
    for stage, label in STAGES:
        item = stage_status.get(stage, {})
        status = item.get("status", "pending")
        version = item.get("artifact_version")
        gate = item.get("quality_gate") or {}
        gate_status = gate.get("status") if isinstance(gate, dict) else None
        line = f"**{label}**  \n`{status}`"
        if version:
            line += f" · v{version}"
        if gate_status:
            line += f" · gate `{gate_status}`"
        st.markdown(line)


def _render_new_session_form(client: ArchimedesApiClient) -> None:
    with st.form("new_session_form", clear_on_submit=False):
        business_need = st.text_area(
            "Business need",
            placeholder="Describe the architecture problem to start a session",
            height=120,
        )
        title = st.text_input("Title", placeholder="Optional session title")
        submitted = st.form_submit_button("Create session", width="stretch")

    if not submitted:
        return

    if not business_need.strip():
        st.session_state.last_error = "Business need is required to create a session."
        return

    _create_session(
        client,
        business_need.strip(),
        title=title.strip() or _derive_title(business_need),
    )
    if st.session_state.session_id:
        st.session_state.messages.append({"role": "user", "content": business_need.strip()})
        st.session_state.show_new_session_form = False
        st.rerun()


def _render_chat_panel(client: ArchimedesApiClient) -> None:
    st.subheader("Chat")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Processing state: show thinking bubble, do work, then rerun ---
    if st.session_state.is_processing and st.session_state.pending_prompt:
        pending = st.session_state.pending_prompt
        stage_hint = _pending_stage_label()
        with st.chat_message("assistant"):
            with st.spinner(f"Archimedes is running **{stage_hint}** — this may take a minute…"):
                _send_message(client, pending)
                _refresh_all(client)
        st.session_state.is_processing = False
        st.session_state.pending_prompt = None
        st.rerun()
        return

    prompt = st.chat_input(
        "Describe the architecture need or send the next instruction",
        disabled=st.session_state.is_processing,
    )
    if prompt:
        if not st.session_state.session_id:
            _create_session(client, prompt, title=_derive_title(prompt))
            if not st.session_state.session_id:
                st.rerun()
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.is_processing = True
        st.session_state.pending_prompt = prompt
        st.rerun()


def _render_artifact_workspace(client: ArchimedesApiClient) -> None:
    st.subheader("Architecture Workspace")
    tabs = st.tabs(["Artifacts", "Socrates", "Evidence", "Diff", "Debug"])
    with tabs[0]:
        _render_artifact_tabs(client)
    with tabs[1]:
        _render_socrates_view()
    with tabs[2]:
        _render_evidence_view(client)
    with tabs[3]:
        _render_diff_view(client)
    with tabs[4]:
        if st.session_state.debug:
            st.json(
                {
                    "session": st.session_state.session,
                    "pipeline": st.session_state.pipeline,
                    "artifacts": st.session_state.artifacts,
                }
            )
        else:
            st.caption("Enable Debug JSON in the sidebar.")


def _render_artifact_tabs(client: ArchimedesApiClient) -> None:
    if not st.session_state.session_id:
        st.info("Start a session to generate artifacts.")
        return
    labels = [label for _, label in ARTIFACT_STAGES]
    tabs = st.tabs(labels)
    for tab, (stage, _label) in zip(tabs, ARTIFACT_STAGES):
        with tab:
            if not _stage_has_artifact(stage):
                st.caption("No artifact yet.")
                continue
            artifact = _load_artifact(client, stage)
            if not artifact:
                st.caption("No artifact yet.")
                continue
            st.caption(f"Stage `{artifact.get('stage')}` · version {artifact.get('version')}")
            _render_artifact_content(stage, artifact)


def _render_artifact_content(stage: str, artifact: dict[str, Any]) -> None:
    content = artifact.get("content") or {}
    if stage == "socratic_review":
        _render_socratic_artifact(content)
        return
    if stage in {"evidence_audit_checkpoint", "final_evidence_audit"}:
        _render_evidence_audit_artifact(content)
        return
    if stage == "hld_generation":
        _render_hld_artifact(content)
        return
    if stage == "requirements_extraction":
        _render_requirements_artifact(content)
        return
    if stage == "pattern_detection":
        _render_pattern_artifact(content)
        return
    if stage == "options_generation":
        _render_options_artifact(content)
        return
    if stage == "adr_generation":
        _render_adr_artifact(content)
        return
    if stage == "mini_waf_review":
        _render_waf_artifact(content)
        return
    summary = content.get("summary") if isinstance(content, dict) else None
    if summary:
        st.markdown(str(summary))
    if isinstance(content, dict):
        st.json(content)
    else:
        st.write(content)


_HLD_DIAGRAM_SECTIONS = [
    ("system_context_diagram", "System Context (C4)"),
    ("container_diagram", "Container Diagram (C4)"),
    ("data_flow_diagram", "Data Flow"),
    ("network_topology_diagram", "Network Topology / Trust Zones"),
    ("network_topology", "Network Topology / Trust Zones"),
    ("deployment_diagram", "Deployment"),
]


def _render_hld_artifact(content: dict[str, Any]) -> None:
    if not isinstance(content, dict):
        st.json(content)
        return

    summary = content.get("summary") or content.get("description")
    if summary:
        st.markdown(str(summary))

    # --- Diagrams ---
    rendered_keys: set[str] = set()
    for key, label in _HLD_DIAGRAM_SECTIONS:
        val = content.get(key)
        if not val:
            continue
        rendered_keys.add(key)
        diagram = _find_mermaid(val) or (val if isinstance(val, str) else None)
        if diagram:
            st.markdown(f"### {label}")
            _render_mermaid_block(diagram)
        elif isinstance(val, dict):
            st.markdown(f"### {label}")
            st.json(val)

    # Catch any extra diagram-like fields the LLM may have named differently
    for key, val in content.items():
        if key in rendered_keys or not isinstance(val, str):
            continue
        diagram = _find_mermaid(val)
        if diagram:
            rendered_keys.add(key)
            label = key.replace("_", " ").title()
            st.markdown(f"### {label}")
            _render_mermaid_block(diagram)

    # --- Components ---
    components = content.get("components") or content.get("component_model") or []
    if components:
        st.markdown("### Components")
        if isinstance(components, list):
            rows = []
            for c in components:
                if isinstance(c, dict):
                    rows.append({
                        "Name": c.get("name") or c.get("id") or "",
                        "Azure Service": c.get("azure_service") or c.get("service") or "",
                        "Role": c.get("role") or c.get("description") or "",
                        "SKU / Tier": c.get("sku_tier") or c.get("sku") or c.get("tier") or "",
                    })
                else:
                    rows.append({"Name": str(c), "Azure Service": "", "Role": "", "SKU / Tier": ""})
            if rows:
                st.dataframe(rows, use_container_width=True)
        else:
            st.json(components)

    # --- Integration points ---
    integrations = content.get("integration_points") or content.get("integrations") or []
    if integrations:
        with st.expander(f"Integration Points ({len(integrations)})"):
            for item in integrations:
                if isinstance(item, dict):
                    source = item.get("source") or ""
                    target = item.get("target") or ""
                    protocol = item.get("protocol") or ""
                    description = item.get("description") or item.get("name") or item.get("endpoint") or ""
                    if source and target:
                        header = f"**{source}** → **{target}**"
                        if protocol:
                            header += f" `{protocol}`"
                        st.markdown(f"- {header}")
                        if description:
                            st.caption(f"  {description}")
                    else:
                        label = description or source or target or str(item)
                        st.markdown(f"- {label}")
                else:
                    st.markdown(f"- {item}")

    # --- Assumptions ---
    assumptions = content.get("assumptions") or []
    if assumptions:
        with st.expander(f"Assumptions ({len(assumptions)})"):
            for item in assumptions:
                text = item.get("description") or item.get("text") or str(item) if isinstance(item, dict) else str(item)
                st.markdown(f"- {text}")

    # --- Key risks ---
    risks = content.get("key_risks") or content.get("risks") or []
    if risks:
        with st.expander(f"Key Risks ({len(risks)})"):
            for item in risks:
                if isinstance(item, dict):
                    risk = item.get("risk") or item.get("description") or str(item)
                    mitigation = item.get("mitigation") or item.get("response") or ""
                    st.markdown(f"- **{risk}**")
                    if mitigation:
                        st.caption(f"  Mitigation: {mitigation}")
                else:
                    st.markdown(f"- {item}")

    # Fallback: show any remaining unrendered top-level keys as JSON
    skip = {*rendered_keys, "summary", "description", "components", "component_model",
            "integration_points", "integrations", "assumptions", "key_risks", "risks"}
    skip.update(k for k, _ in _HLD_DIAGRAM_SECTIONS)
    remainder = {k: v for k, v in content.items() if k not in skip and v}
    if remainder:
        with st.expander("Additional details"):
            st.json(remainder)


def _sanitize_mermaid(diagram: str) -> str:
    """Fix common LLM Mermaid generation errors before rendering."""
    import re
    lines = diagram.splitlines()
    out: list[str] = []
    for line in lines:
        # C4: LLM invents BoundedContext — map to Boundary (closest valid command)
        line = re.sub(r'\bBoundedContext\(', 'Boundary(', line)
        # Flowchart: parentheses inside subgraph labels cause parse errors.
        # e.g. "subgraph DMZ [DMZ (Per-Region)]" → "subgraph DMZ [DMZ - Per-Region]"
        def _clean_label(m: re.Match) -> str:
            return m.group(0).replace('(', '- ').replace(')', '')
        line = re.sub(r'subgraph\s+\w+\s+\[.*?\]', _clean_label, line)
        # Flowchart: multiple whitespace-separated node defs on one line
        # e.g. "    A[Foo]    B[Bar]" → separate lines (only when no connector)
        if '-->' not in line and '---' not in line:
            split = re.split(r'(?<=\])\s{2,}(?=\w+[\[({])', line)
            if len(split) > 1:
                indent = len(line) - len(line.lstrip())
                prefix = ' ' * indent
                out.extend(prefix + s.strip() for s in split)
                continue
        out.append(line)
    return '\n'.join(out)


def _render_mermaid_block(diagram: str) -> None:
    sanitized = _sanitize_mermaid(diagram)
    escaped = html.escape(sanitized)
    # Mermaid 11 includes C4 natively. On parse error show warning + source inline.
    components.html(
        f"""
        <div id="diagram-wrap" style="min-height:60px">
          <pre class="mermaid">{escaped}</pre>
        </div>
        <div id="diagram-error" style="display:none;padding:12px;background:#fff3cd;border:1px solid #ffc107;border-radius:6px;font-family:monospace;font-size:12px;white-space:pre-wrap"></div>
        <script type="module">
          import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
          mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose', theme: 'default' }});
          try {{
            await mermaid.run({{ querySelector: '.mermaid' }});
          }} catch(err) {{
            document.getElementById('diagram-wrap').style.display = 'none';
            var el = document.getElementById('diagram-error');
            el.style.display = 'block';
            el.textContent = '⚠ Diagram render error — ' + err.message;
          }}
        </script>
        """,
        height=500,
        scrolling=True,
    )
    # Always show source so content is never lost even when rendering fails
    with st.expander("Diagram source", expanded=False):
        st.code(diagram, language="mermaid")


_PATTERN_LABELS = {
    "real_time_streaming": "Real-Time Streaming",
    "web_api": "Web API",
    "event_driven": "Event-Driven",
    "batch_processing": "Batch Processing",
    "cqrs": "CQRS",
    "microservices": "Microservices",
    "serverless": "Serverless",
    "data_lakehouse": "Data Lakehouse",
}


def _render_pattern_artifact(content: dict[str, Any]) -> None:
    primary = content.get("primary_pattern") or ""
    secondary = content.get("secondary_patterns") or []
    confidence = float(content.get("confidence") or 0.0)
    signals = content.get("signals") or []
    rationale = content.get("rationale") or content.get("summary") or ""

    primary_label = _PATTERN_LABELS.get(primary, primary.replace("_", " ").title()) if primary else "Unknown"
    c1, c2 = st.columns([0.6, 0.4])
    with c1:
        st.metric("Primary Pattern", primary_label)
        if secondary:
            sec_labels = [_PATTERN_LABELS.get(p, p.replace("_", " ").title()) for p in secondary]
            st.caption("Secondary: " + " · ".join(sec_labels))
    with c2:
        st.metric("Confidence", f"{int(confidence * 100)}%" if confidence <= 1 else f"{int(confidence)}%")

    if rationale:
        st.markdown(str(rationale))

    if signals:
        st.markdown("**Matched signals:** " + " · ".join(f"`{s}`" for s in signals))


def _render_options_artifact(content: dict[str, Any]) -> None:
    options = content.get("options") or []
    rejected = content.get("rejected_options") or []

    if not options:
        st.json(content)
        return

    for i, opt in enumerate(options):
        if not isinstance(opt, dict):
            st.write(opt)
            continue
        name = opt.get("name") or f"Option {i + 1}"
        summary = opt.get("summary") or opt.get("rationale") or ""
        scores = opt.get("trade_off_scores") or {}
        components = opt.get("components") or []
        risks = opt.get("key_risks") or []

        with st.expander(f"**{name}**", expanded=(i == 0)):
            if summary:
                st.markdown(str(summary))

            if scores and isinstance(scores, dict):
                score_cols = st.columns(len(scores))
                for col, (metric, val) in zip(score_cols, scores.items()):
                    col.metric(metric.replace("_", " ").title(), f"{val}/10" if isinstance(val, (int, float)) else str(val))

            if components:
                st.markdown("**Components**")
                rows = []
                for c in components:
                    if isinstance(c, dict):
                        rows.append({
                            "Service": c.get("azure_service") or c.get("service") or c.get("name") or "",
                            "Role": c.get("role") or c.get("description") or "",
                            "SKU": c.get("sku_tier") or c.get("sku") or "",
                        })
                if rows:
                    st.dataframe(rows, use_container_width=True)

            if risks:
                st.markdown("**Key Risks**")
                for r in risks:
                    st.markdown(f"- {r}" if isinstance(r, str) else f"- {r.get('risk') or str(r)}")

    if rejected:
        with st.expander(f"Rejected options ({len(rejected)})"):
            for opt in rejected:
                if isinstance(opt, dict):
                    name = opt.get("name") or opt.get("option") or "Option"
                    reason = opt.get("reason") or opt.get("rejection_reason") or ""
                    st.markdown(f"- **{name}** — {reason}")
                else:
                    st.markdown(f"- {opt}")


def _render_requirements_artifact(content: dict[str, Any]) -> None:
    col_func, col_nfr = st.columns(2)
    with col_func:
        st.markdown("**Functional Requirements**")
        items = content.get("functional_requirements") or []
        if items:
            for item in items:
                text = item.get("description") or item.get("text") or str(item) if isinstance(item, dict) else str(item)
                st.markdown(f"- {text}")
        else:
            st.caption("None extracted.")
    with col_nfr:
        st.markdown("**NFRs & Constraints**")
        for item in (content.get("non_functional_requirements") or content.get("nfrs") or []):
            text = item.get("description") or item.get("text") or str(item) if isinstance(item, dict) else str(item)
            st.markdown(f"- {text}")
        for item in (content.get("constraints") or []):
            text = item.get("description") or item.get("text") or str(item) if isinstance(item, dict) else str(item)
            st.markdown(f"- ⚠️ {text}")

    assumptions = content.get("assumptions") or []
    if assumptions:
        with st.expander(f"Assumptions ({len(assumptions)})"):
            for item in assumptions:
                text = item.get("description") or item.get("text") or str(item) if isinstance(item, dict) else str(item)
                st.markdown(f"- {text}")

    open_q = content.get("open_questions") or []
    if open_q:
        with st.expander(f"Open questions ({len(open_q)})"):
            for item in open_q:
                text = item.get("question") or item.get("text") or str(item) if isinstance(item, dict) else str(item)
                st.markdown(f"- {text}")


def _render_adr_artifact(content: dict[str, Any]) -> None:
    title = content.get("title") or "Architecture Decision Record"
    status = content.get("status") or "Proposed"
    st.markdown(f"## {title}")
    st.caption(f"Status: **{status}**")

    for section_key, label in [
        ("context", "Context"),
        ("decision", "Decision"),
    ]:
        val = content.get(section_key)
        if val:
            st.markdown(f"### {label}")
            st.markdown(str(val))

    options = content.get("options_considered") or content.get("alternatives") or []
    if options:
        st.markdown("### Options Considered")
        for opt in options:
            if isinstance(opt, dict):
                name = opt.get("name") or opt.get("option") or "Option"
                with st.expander(name):
                    for k in ("pros", "advantages"):
                        if opt.get(k):
                            st.markdown("**Pros:** " + ", ".join(opt[k]) if isinstance(opt[k], list) else str(opt[k]))
                    for k in ("cons", "disadvantages"):
                        if opt.get(k):
                            st.markdown("**Cons:** " + ", ".join(opt[k]) if isinstance(opt[k], list) else str(opt[k]))
            else:
                st.markdown(f"- {opt}")

    consequences = content.get("consequences") or {}
    if consequences:
        st.markdown("### Consequences")
        if isinstance(consequences, dict):
            for polarity, items in consequences.items():
                if items:
                    st.markdown(f"**{polarity.title()}:**")
                    for item in (items if isinstance(items, list) else [items]):
                        st.markdown(f"- {item}")
        else:
            st.markdown(str(consequences))

    for section_key, label in [
        ("blind_spots", "Blind Spots"),
        ("assumptions_documented", "Assumptions"),
    ]:
        val = content.get(section_key)
        if val:
            with st.expander(label):
                for item in (val if isinstance(val, list) else [val]):
                    st.markdown(f"- {item}")


_WAF_PILLAR_EMOJI = {
    "reliability": "🔄",
    "security": "🔒",
    "cost_optimization": "💰",
    "cost": "💰",
    "operational_excellence": "⚙️",
    "operations": "⚙️",
    "performance_efficiency": "⚡",
    "performance": "⚡",
}

_WAF_SEVERITY_COLOR = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


def _render_waf_artifact(content: dict[str, Any]) -> None:
    # Build per-pillar groups — LLM may return either a flat findings list
    # with a "pillar" field on each item, or a dict keyed by pillar name.
    pillar_order = [
        ("reliability", "🔄 Reliability"),
        ("security", "🔒 Security"),
        ("cost_optimization", "💰 Cost Optimization"),
        ("cost", "💰 Cost Optimization"),
        ("operational_excellence", "⚙️ Operational Excellence"),
        ("operations", "⚙️ Operational Excellence"),
        ("performance_efficiency", "⚡ Performance Efficiency"),
        ("performance", "⚡ Performance Efficiency"),
    ]

    # Normalise to {pillar_key: [findings]}
    grouped: dict[str, list] = {}

    flat_findings = content.get("findings") or []
    if flat_findings:
        # Flat list with pillar field on each finding
        for f in flat_findings:
            if not isinstance(f, dict):
                continue
            raw_pillar = (f.get("pillar") or "other").lower().replace(" ", "_")
            # Map common aliases
            alias = {"cost": "cost_optimization", "operations": "operational_excellence", "performance": "performance_efficiency"}
            key = alias.get(raw_pillar, raw_pillar)
            grouped.setdefault(key, []).append(f)
    else:
        # Per-pillar dict structure
        pillars_data = content.get("pillars") or content
        if isinstance(pillars_data, dict):
            for key, _ in pillar_order:
                pillar = pillars_data.get(key)
                if not pillar:
                    continue
                findings = pillar.get("findings") if isinstance(pillar, dict) else pillar
                if findings:
                    grouped[key] = findings if isinstance(findings, list) else [findings]

    if not grouped:
        st.json(content)
        return

    seen_labels: set[str] = set()
    for key, label in pillar_order:
        findings = grouped.get(key)
        if not findings or label in seen_labels:
            continue
        seen_labels.add(label)
        with st.expander(label, expanded=True):
            for finding in findings:
                if isinstance(finding, dict):
                    sev = (finding.get("severity") or "medium").lower()
                    dot = _WAF_SEVERITY_COLOR.get(sev, "⚪")
                    title_text = (
                        finding.get("title") or finding.get("description")
                        or finding.get("finding") or finding.get("recommendation") or str(finding)
                    )
                    rec = finding.get("recommendation") or finding.get("mitigation") or ""
                    st.markdown(f"{dot} `{sev.upper()}` **{title_text}**")
                    if rec and rec != title_text:
                        st.caption(f"→ {rec}")
                else:
                    st.markdown(f"- {finding}")


def _render_socrates_view() -> None:
    artifact = st.session_state.artifacts.get("socratic_review")
    if not artifact:
        st.caption("Socrates output will appear after the Socratic Review stage.")
        return
    _render_socratic_artifact(artifact.get("content") or {})


def _render_socratic_artifact(content: dict[str, Any]) -> None:
    review = content.get("socratic_review", content)
    synthesis = review.get("synthesis", {}) if isinstance(review, dict) else {}
    persona_analyses = review.get("persona_analyses", []) if isinstance(review, dict) else []
    if not synthesis and not persona_analyses:
        summary = review.get("summary") if isinstance(review, dict) else None
        if summary:
            st.markdown(str(summary))
        if isinstance(review, dict):
            st.json(review)
        else:
            st.write(review)
        return

    if synthesis:
        st.metric("Recommended option", synthesis.get("recommended_option_id") or "Pending")
        st.progress(float(synthesis.get("confidence") or 0.0))
        st.write(synthesis.get("rationale", ""))
        cols = st.columns(2)
        with cols[0]:
            st.markdown("**Blind spots**")
            for item in synthesis.get("blind_spots", []):
                st.write(f"- {item}")
        with cols[1]:
            st.markdown("**Pre-mortem**")
            for item in synthesis.get("premortem_scenarios", []):
                st.write(f"- {item}")
    for analysis in persona_analyses:
        with st.expander(str(analysis.get("persona", "Persona"))):
            st.write(analysis.get("summary", ""))
            for finding in analysis.get("findings", []):
                st.markdown(f"- `{finding.get('severity', 'medium')}` {finding.get('finding')}")


def _render_evidence_audit_artifact(content: dict[str, Any]) -> None:
    report = content.get("evidence_audit", content)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Quality", report.get("overall_evidence_quality", "unknown"))
    c2.metric("Recommendation", report.get("recommendation", "unknown"))
    c3.metric("Claims", report.get("total_claims", 0))
    c4.metric("Warnings", len(report.get("warnings", [])))
    for finding in report.get("findings", []):
        with st.expander(f"{finding.get('severity')} · {finding.get('category')}"):
            st.write(finding.get("description"))
            if finding.get("recommendation"):
                st.caption(finding["recommendation"])


def _render_evidence_view(client: ArchimedesApiClient) -> None:
    if not st.session_state.session_id:
        st.caption("No evidence yet.")
        return
    if not _has_any_artifact():
        st.caption("Evidence will appear after the first pipeline stage completes.")
        return

    session_id = st.session_state.session_id

    # --- Unresolved assumptions requiring user action ---
    pending = _safe_call(
        lambda: client.get_claims(session_id, requires_user_validation=True),
        default={"items": []},
    ).get("items", [])
    unresolved = [c for c in pending if c.get("validated_at") is None]
    if unresolved:
        st.markdown(f"### ✋ {len(unresolved)} assumption(s) need your review")
        for claim in unresolved:
            claim_id = claim.get("claim_id", "")
            question = claim.get("validation_question") or claim.get("claim") or "Review this assumption."
            stage = claim.get("stage") or ""
            with st.expander(f"`{stage}` — {question[:100]}"):
                st.write(question)
                comment = st.text_input("Comment (optional)", key=f"comment_{claim_id}")
                col_a, col_r = st.columns(2)
                with col_a:
                    if st.button("✅ Accept", key=f"accept_{claim_id}", width="stretch"):
                        _safe_call(
                            lambda: client.validate_claim(session_id, claim_id, accepted=True, comment=comment or None),
                            default=None,
                        )
                        st.rerun()
                with col_r:
                    if st.button("❌ Reject", key=f"reject_{claim_id}", width="stretch"):
                        _safe_call(
                            lambda: client.validate_claim(session_id, claim_id, accepted=False, comment=comment or None),
                            default=None,
                        )
                        st.rerun()
        st.divider()

    # --- All claims + evidence tables ---
    claims = _safe_call(lambda: client.get_claims(session_id), default={"items": []})
    evidence = _safe_call(lambda: client.get_evidence(session_id), default={"items": []})
    st.markdown("**Claims**")
    st.dataframe(claims.get("items", []), use_container_width=True)
    st.markdown("**Evidence Sources**")
    st.dataframe(evidence.get("items", []), use_container_width=True)


def _render_diff_view(client: ArchimedesApiClient) -> None:
    if not st.session_state.session_id:
        st.caption("Diffs appear after multiple artifact versions exist.")
        return
    stage = st.selectbox("Artifact stage", [stage for stage, _ in ARTIFACT_STAGES])
    left, right = st.columns(2)
    with left:
        v1 = st.number_input("Before version", min_value=1, value=1, step=1)
    with right:
        v2 = st.number_input("After version", min_value=1, value=2, step=1)
    if st.button("Load diff", width="stretch"):
        diff = client.get_artifact_diff(st.session_state.session_id, stage, int(v1), int(v2))
        st.session_state["last_diff"] = diff
    diff = st.session_state.get("last_diff")
    if not diff:
        st.caption("No diff loaded.")
        return
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Added**")
        st.json(diff.get("added", {}))
    with cols[1]:
        st.markdown("**Removed**")
        st.json(diff.get("removed", {}))
    with cols[2]:
        st.markdown("**Modified**")
        st.json(diff.get("modified", {}))


def _render_mermaid_from_content(content: dict[str, Any]) -> bool:
    diagram = _find_mermaid(content)
    if not diagram:
        return False
    _render_mermaid_block(diagram)
    return True


_MERMAID_DIAGRAM_STARTERS = ("flowchart", "graph", "C4Context", "C4Container", "sequenceDiagram", "classDiagram", "erDiagram", "gantt", "stateDiagram")


def _strip_mermaid_fence(text: str) -> str | None:
    """Return diagram source with any ```mermaid ... ``` fences removed."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # drop opening fence line and closing fence line
        inner = "\n".join(lines[1:])
        if inner.endswith("```"):
            inner = inner[: inner.rfind("```")].rstrip()
        return inner.strip()
    return None


def _find_mermaid(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(_MERMAID_DIAGRAM_STARTERS):
            return stripped
        # Handle ```mermaid ... ``` fences the LLM sometimes wraps diagrams in
        if stripped.startswith("```"):
            inner = _strip_mermaid_fence(stripped)
            if inner and inner.startswith(_MERMAID_DIAGRAM_STARTERS):
                return inner
    if isinstance(value, dict):
        for key in ("system_context", "mermaid_source", "diagram", "source"):
            found = _find_mermaid(value.get(key))
            if found:
                return found
        for child in value.values():
            found = _find_mermaid(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _find_mermaid(child)
            if found:
                return found
    return None


def _create_session(client: ArchimedesApiClient, business_need: str, *, title: str | None = None, domain: str | None = None) -> None:
    try:
        session = client.create_session(business_need, title=title, domain=domain)
        st.session_state.session_id = session["session_id"]
        st.session_state.session = session
        st.session_state.last_error = None
        _refresh_session_state(client)
    except ArchimedesApiError as exc:
        st.session_state.last_error = exc.detail


def _send_message(client: ArchimedesApiClient, prompt: str) -> None:
    try:
        response = client.send_message(
            st.session_state.session_id,
            prompt,
            idempotency_key=_idempotency_key(prompt),
        )
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": _format_orchestrator_response(response),
            }
        )
        st.session_state.last_error = None
    except ArchimedesApiError as exc:
        st.session_state.last_error = exc.detail
        st.session_state.messages.append({"role": "assistant", "content": f"API error: {exc.detail}"})


def _format_orchestrator_response(response: dict[str, Any]) -> str:
    stage = response.get("current_stage") or "unknown"
    status = response.get("stage_status") or "unknown"
    artifacts = response.get("artifacts_produced") or []
    gate = response.get("quality_gate_result") or {}
    gate_status = gate.get("status", "")
    warnings = gate.get("warnings") or []
    blocking = gate.get("blocking_failures") or []
    evidence_count = response.get("evidence_count") or 0
    change_detected = response.get("change_detected", False)
    impacted = response.get("impacted_stages") or []
    prompt = response.get("next_prompt_for_user") or ""

    lines: list[str] = []

    # --- Stage + gate status header ---
    gate_badge = {
        "passed": "[gate: PASSED]",
        "passed_with_warnings": "[gate: WARNINGS]",
        "failed": "[gate: FAILED]",
    }.get(gate_status, "")
    header = f"**Stage `{stage}`** — {status}"
    if gate_badge:
        header += f"  {gate_badge}"
    lines.append(header)

    # --- Artifacts ---
    if artifacts:
        lines.append("Produced: " + ", ".join(f"`{a}`" for a in artifacts))

    # --- Evidence retrieval summary ---
    if evidence_count > 0:
        lines.append(f"Retrieved **{evidence_count}** knowledge base source(s) from Azure AI Search.")

    # --- Requirement change detection ---
    if change_detected and impacted:
        lines.append(
            "Requirement change detected. Re-ran: "
            + ", ".join(f"`{s}`" for s in impacted)
        )

    # --- Gate warnings ---
    if warnings:
        lines.append("\n**Quality gate warnings:**")
        for w in warnings[:4]:
            lines.append(f"- {w}")

    # --- Gate blocking failures ---
    if blocking:
        lines.append("\n**Blocking failures (review required):**")
        for b in blocking[:4]:
            lines.append(f"- {b}")

    # --- Next action prompt ---
    if prompt:
        lines.append(f"\n{prompt}")

    return "\n".join(lines)


def _refresh_all(client: ArchimedesApiClient) -> None:
    _refresh_session_state(client)
    _refresh_available_artifacts(client)


def _refresh_session_state(client: ArchimedesApiClient) -> None:
    session_id = st.session_state.session_id
    if not session_id:
        return
    st.session_state.session = _safe_call(lambda: client.get_session(session_id), default=st.session_state.session)
    st.session_state.pipeline = _safe_call(lambda: client.get_pipeline_status(session_id), default={"stages": []})


def _refresh_available_artifacts(client: ArchimedesApiClient) -> None:
    session_id = st.session_state.session_id
    if not session_id:
        return
    for stage, _label in ARTIFACT_STAGES:
        if not _stage_has_artifact(stage):
            continue
        artifact = client.get_latest_artifact(session_id, stage)
        if artifact:
            st.session_state.artifacts[stage] = artifact


def _load_artifact(client: ArchimedesApiClient, stage: str) -> dict[str, Any] | None:
    cached = st.session_state.artifacts.get(stage)
    if cached:
        return cached
    if not st.session_state.session_id:
        return None
    if not _stage_has_artifact(stage):
        return None
    artifact = client.get_latest_artifact(st.session_state.session_id, stage)
    if artifact:
        st.session_state.artifacts[stage] = artifact
    return artifact


def _pipeline_stage_versions() -> dict[str, int]:
    versions: dict[str, int] = {}
    for item in st.session_state.pipeline.get("stages", []):
        stage = item.get("stage")
        version = item.get("artifact_version")
        if stage and version:
            versions[str(stage)] = int(version)
    return versions


def _stage_has_artifact(stage: str) -> bool:
    return stage in _pipeline_stage_versions()


def _has_any_artifact() -> bool:
    return bool(_pipeline_stage_versions())


def _safe_call(func, *, default):
    try:
        return func()
    except ArchimedesApiError as exc:
        st.session_state.last_error = exc.detail
        return default


def _pending_stage_label() -> str:
    session = st.session_state.get("session") or {}
    pending = session.get("pending_next_stage") or session.get("current_stage") or ""
    labels = dict(STAGES)
    return labels.get(pending, pending.replace("_", " ").title()) if pending else "current stage"


def _derive_title(prompt: str) -> str:
    words = prompt.strip().split()
    return " ".join(words[:6]) if words else "Architecture session"


def _idempotency_key(prompt: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    return f"ui-{hash((prompt, now))}"


def _reset_session() -> None:
    for key in [
        "session_id",
        "session",
        "pipeline",
        "artifacts",
        "last_error",
        "last_diff",
        "is_processing",
        "pending_prompt",
    ]:
        st.session_state.pop(key, None)
    st.session_state.messages = []
    _ensure_state()


if __name__ == "__main__":
    main()

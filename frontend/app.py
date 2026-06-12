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

        st.divider()
        _render_session_summary()
        st.divider()
        _render_timeline()

        if st.button("Refresh status", width="stretch", disabled=not st.session_state.session_id):
            _refresh_session_state(client)
            st.rerun()


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
            st.write(message["content"])

    prompt = st.chat_input("Describe the architecture need or send the next instruction")
    if prompt:
        if not st.session_state.session_id:
            _create_session(client, prompt, title=_derive_title(prompt))
            if not st.session_state.session_id:
                st.rerun()
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Archimedes is working through the current stage..."):
            _send_message(client, prompt)
            _refresh_all(client)
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
        if _render_mermaid_from_content(content):
            return
    summary = content.get("summary") if isinstance(content, dict) else None
    if summary:
        st.markdown(str(summary))
    if isinstance(content, dict):
        st.json(content)
    else:
        st.write(content)


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
    claims = _safe_call(lambda: client.get_claims(st.session_state.session_id), default={"items": []})
    evidence = _safe_call(lambda: client.get_evidence(st.session_state.session_id), default={"items": []})
    st.markdown("**Claims**")
    st.dataframe(claims.get("items", []), width="stretch")
    st.markdown("**Evidence**")
    st.dataframe(evidence.get("items", []), width="stretch")


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
    escaped = html.escape(diagram)
    components.html(
        f"""
        <div class="mermaid">{escaped}</div>
        <script type="module">
          import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
          mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose' }});
        </script>
        """,
        height=420,
        scrolling=True,
    )
    with st.expander("Mermaid source"):
        st.code(diagram, language="mermaid")
    return True


def _find_mermaid(value: Any) -> str | None:
    if isinstance(value, str) and value.strip().startswith(("flowchart", "graph", "C4Context", "sequenceDiagram")):
        return value
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
    stage = response.get("current_stage")
    status = response.get("stage_status")
    prompt = response.get("next_prompt_for_user") or ""
    artifacts = ", ".join(response.get("artifacts_produced", [])) or "No artifacts"
    return f"Stage `{stage}` {status}. Produced: {artifacts}. {prompt}".strip()


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
    ]:
        st.session_state.pop(key, None)
    st.session_state.messages = []
    _ensure_state()


if __name__ == "__main__":
    main()

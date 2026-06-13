from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "frontend"))

import app
from app import (
    _c4_flowchart_fallback,
    _HLD_C4_DIAGRAM_KEYS,
    _is_proceed_prompt,
    _parse_c4_diagram,
    _pending_stage_label,
    _sanitize_mermaid,
)


def test_c4_flowchart_fallback_converts_context_diagram():
    diagram = """C4Context
  Person(user, "Payment Service User")
  System(payment_system, "Fraud Detection Processing Platform")
  SystemDb(cosmosdb, "Cosmos DB Audit Store")
  System(eventhubs, "Azure Event Hubs")
  Rel(user, payment_system, "Sends transactions for processing")
  Rel(payment_system, eventhubs, "Ingests transaction events")
"""

    fallback = _c4_flowchart_fallback(diagram)

    assert fallback is not None
    assert fallback.startswith("flowchart TB")
    assert 'user["Payment Service User"]' in fallback
    assert 'cosmosdb["Cosmos DB Audit Store"]' in fallback
    assert "user -->|Sends transactions for processing| payment_system" in fallback


def test_parse_c4_diagram_extracts_nodes_and_relationships():
    diagram = """C4Container
  Container(api, "API", "FastAPI")
  ContainerDb(store, "Cosmos DB", "Audit store")
  Rel(api, store, "Writes decisions")
"""

    parsed = _parse_c4_diagram(diagram)

    assert parsed is not None
    nodes, edges = parsed
    assert nodes["api"] == ("Container", "API")
    assert nodes["store"] == ("ContainerDb", "Cosmos DB")
    assert edges == [("api", "store", "Writes decisions", False)]


def test_hld_c4_keys_route_to_simple_renderer_inputs():
    artifact_diagrams = {
        "system_context_diagram": """C4Context
  Person(user, "Payment Service User")
  System(payment_system, "Fraud Detection Processing Platform")
  Rel(user, payment_system, "Sends transactions for processing")
""",
        "container_diagram": """C4Container
  Container(api, "API", "FastAPI")
  ContainerDb(store, "Cosmos DB", "Audit store")
  Rel(api, store, "Writes decisions")
""",
    }

    assert set(artifact_diagrams) == _HLD_C4_DIAGRAM_KEYS
    for diagram in artifact_diagrams.values():
        assert _parse_c4_diagram(_sanitize_mermaid(diagram)) is not None


def test_pending_stage_label_uses_current_stage_for_refinement(monkeypatch):
    monkeypatch.setattr(
        app.st,
        "session_state",
        {"session": {"current_stage": "intake", "pending_next_stage": "requirements_extraction"}},
    )

    assert _pending_stage_label("make some assumptions about open questions") == "Intake"


def test_pending_stage_label_uses_next_stage_for_proceed(monkeypatch):
    monkeypatch.setattr(
        app.st,
        "session_state",
        {"session": {"current_stage": "intake", "pending_next_stage": "requirements_extraction"}},
    )

    assert _is_proceed_prompt("proceed")
    assert _pending_stage_label("proceed") == "Requirements"

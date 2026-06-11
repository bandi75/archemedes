from archimedes.tools.adr_formatter import format_adr_markdown
from archimedes.tools.cost_estimator import estimate_azure_cost
from archimedes.tools.mermaid_check import mermaid_render_check
from archimedes.tools.stride_mapper import map_stride_threats


def test_mermaid_render_check_detects_valid_flowchart():
    diagram = """
flowchart TB
    A[Client] --> B[API]
    B --> C[(DB)]
""".strip()

    result = mermaid_render_check(diagram, "flowchart")

    assert result.valid is True
    assert result.errors == []


def test_cost_estimator_returns_expected_range_for_known_services():
    estimate = estimate_azure_cost(
        [
            {"service": "Event Hubs", "sku": "Standard", "region": "eastus", "quantity": 2},
            {"service": "Cosmos DB", "sku": "Serverless", "region": "eastus", "quantity": 1},
        ]
    )

    assert estimate.monthly_range["expected"] > 0
    assert estimate.monthly_range["high"] >= estimate.monthly_range["expected"]
    assert estimate.annual_range["expected"] == round(estimate.monthly_range["expected"] * 12, 2)


def test_adr_formatter_outputs_required_sections():
    markdown = format_adr_markdown(
        adr_id="001",
        title="Adopt Event-Driven Core",
        status="Proposed",
        context="Need near real-time fraud detection.",
        decision="Use Event Hubs + Stream Analytics + Functions.",
        consequences="Improves responsiveness, increases operations complexity.",
        alternatives=[{"option": "Batch only", "pros": "Lower ops", "cons": "Higher latency"}],
        references=["https://learn.microsoft.com/azure/architecture"],
    )

    assert "## Context" in markdown
    assert "## Decision" in markdown
    assert "## Consequences" in markdown


def test_stride_mapper_detects_multiple_categories():
    text = "Use managed identity auth with token validation and centralized audit logs and rbac policies"
    threats = map_stride_threats(text)

    categories = {item.category for item in threats}
    assert "Spoofing" in categories
    assert "Repudiation" in categories
    assert "Elevation of Privilege" in categories

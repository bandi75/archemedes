from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from archimedes.agents.schemas import HLDArtifact, RequirementsArtifact
from archimedes.models.enums import EvidenceRetrievalMethod, StageName
from archimedes.models.evidence import EvidenceSource
from archimedes.agents.maf_factory import MAFAgentFactory


def test_maf_factory_uses_openai_client_when_api_key_is_configured(monkeypatch):
    openai_module = pytest.importorskip("agent_framework_openai")
    captured = {}

    class FakeOpenAIChatClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(openai_module, "OpenAIChatClient", FakeOpenAIChatClient)
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example.services.ai.azure.com/api/project")
    monkeypatch.setenv("FOUNDRY_API_KEY", "test-key")

    factory = MAFAgentFactory(prompts_root=Path("prompts"))

    _ = factory.maf_client

    assert captured["base_url"] == "https://example.services.ai.azure.com/api/project/openai/v1"
    assert captured["api_key"] == "test-key"
    assert captured["model"] == "gpt-4.1"


def test_maf_factory_fallback_retrieves_evidence_when_agent_skips_tool(monkeypatch):
    pytest.importorskip("agent_framework")
    captured = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            pass

        async def run(self, user_message):
            class Result:
                text = (
                    '{"status":"complete","refined_business_need":"Build fraud detection",'
                    '"domain":"fintech","scale_hint":"10K TPS","timeline_hint":"",'
                    '"compliance_flags":["PCI-DSS"],"open_questions":[]}'
                )

            return Result()

    class FakeKB:
        def __init__(self):
            self.queries = []

        def retrieve(self, *, query, top_k, session_id):
            self.queries.append((query, top_k, session_id))
            return [
                EvidenceSource(
                    session_id=session_id,
                    source="Azure Architecture Center",
                    retrieved_via=EvidenceRetrievalMethod.FOUNDRY_IQ,
                    excerpt="Reference guidance",
                )
            ]

    import agent_framework

    monkeypatch.setattr(agent_framework, "Agent", FakeAgent)
    kb = FakeKB()
    factory = MAFAgentFactory(prompts_root=Path("prompts"), kb_adapter=kb)
    factory._maf_client = object()

    patch = factory.run_stage(
        "IntakeAgent",
        session_id="session_test",
        stage=StageName.INTAKE,
        base_version=0,
        user_message="Build a fraud platform for 10K TPS with PCI-DSS.",
    )

    assert kb.queries
    assert "architecture intake business need" in kb.queries[0][0]
    assert "Return ONLY a valid JSON object" in captured["instructions"]
    assert "refined_business_need" in captured["instructions"]
    assert patch.evidence_sources
    assert patch.claims[0].evidence_ids == [patch.evidence_sources[0].evidence_id]


def test_requirements_schema_rejects_claims_only_payload():
    with pytest.raises(ValidationError):
        RequirementsArtifact.model_validate(
            {
                "claims": [
                    {
                        "type": "fact",
                        "label": "throughput",
                        "value": "10,000 TPS",
                    }
                ],
                "quality_checklist": {},
                "open_questions": [],
            }
        )


def test_maf_factory_rejects_invalid_requirements_payload(monkeypatch):
    pytest.importorskip("agent_framework")

    class FakeAgent:
        def __init__(self, **kwargs):
            pass

        async def run(self, user_message):
            class Result:
                text = (
                    '{"claims":[{"type":"fact","label":"throughput","value":"10,000 TPS"}],'
                    '"quality_checklist":{},"open_questions":[]}'
                )

            return Result()

    class FakeKB:
        def retrieve(self, *, query, top_k, session_id):
            return [
                EvidenceSource(
                    session_id=session_id,
                    source="Azure Architecture Center",
                    retrieved_via=EvidenceRetrievalMethod.FOUNDRY_IQ,
                    excerpt="Reference guidance",
                )
            ]

    import agent_framework

    monkeypatch.setattr(agent_framework, "Agent", FakeAgent)
    factory = MAFAgentFactory(prompts_root=Path("prompts"), kb_adapter=FakeKB())
    factory._maf_client = object()

    with pytest.raises(ValueError, match="RequirementsEngineer returned schema-invalid JSON"):
        factory.run_stage(
            "RequirementsEngineer",
            session_id="session_test",
            stage=StageName.REQUIREMENTS_EXTRACTION,
            base_version=1,
            user_message="Extract requirements from the intake artifact.",
        )


def test_hld_schema_accepts_prompt_documented_component_and_risk_shape():
    artifact = HLDArtifact.model_validate(
        {
            "system_context_diagram": "C4Context\nPerson(user, \"User\")",
            "container_diagram": "C4Container\nContainer(api, \"API\", \"FastAPI\")",
            "data_flow_diagram": "flowchart TB\nA[Ingress] --> B[Scoring]",
            "network_topology_diagram": "flowchart TB\nsubgraph Private [Private - VNet Zone]\nA[API]\nend",
            "components": [
                {
                    "name": "Event Hubs",
                    "azure_service": "Azure Event Hubs",
                    "role": "Transaction event ingestion",
                    "sku_tier": "Premium",
                }
            ],
            "integration_points": [
                {
                    "source": "Payment Front End",
                    "target": "Event Hubs",
                    "protocol": "HTTPS",
                    "description": "Publishes transaction events.",
                }
            ],
            "assumptions": ["PCI scope is limited to tokenized transaction events."],
            "key_risks": [
                {
                    "risk": "Streaming job capacity may lag peak TPS.",
                    "mitigation": "Load test and pre-scale streaming units.",
                }
            ],
            "quality_checklist": {},
        }
    )

    assert artifact.components[0].azure_service == "Azure Event Hubs"
    assert artifact.key_risks[0].risk == "Streaming job capacity may lag peak TPS."

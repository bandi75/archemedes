from __future__ import annotations

from archimedes.tools.foundry_iq import FoundryIQRetriever
from archimedes.tools.mock_foundry_iq import MockFoundryIQAdapter


def test_mock_foundry_adapter_returns_required_fixture_fields():
    adapter = MockFoundryIQAdapter()

    results = adapter.retrieve(
        query="Event Hubs partition throughput limits for fraud events",
        top_k=3,
        session_id="session_mock_test",
    )

    assert results
    first = results[0]
    assert first.session_id == "session_mock_test"
    assert first.retrieved_via == "mock"
    assert first.kb_name == "mock-kb"
    assert first.kb_version == "fixture-v1"
    assert first.trust_level == "medium"
    assert first.is_fixture is True


def test_mock_foundry_adapter_honors_top_k_and_fallback():
    adapter = MockFoundryIQAdapter()

    no_match = adapter.retrieve(query="some unknown enterprise architecture query", top_k=1)

    assert len(no_match) == 1
    assert no_match[0].kb_name == "mock-kb"


def test_foundry_retriever_uses_mock_when_env_enabled(monkeypatch):
    monkeypatch.setenv("USE_MOCK_KB", "true")
    retriever = FoundryIQRetriever(default_session_id="session_from_retriever")

    results = retriever.retrieve(query="AKS Container Apps tradeoff", top_k=2)

    assert results
    assert all(item.retrieved_via == "mock" for item in results)
    assert all(item.session_id == "session_from_retriever" for item in results)

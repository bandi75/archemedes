from __future__ import annotations

import os
import re

import pytest

from archimedes.tools.foundry_iq import (
    knowledge_base_retrieve,
    parse_kb_response_to_evidence_source,
)


REQUIRED_ENV_VARS = ("ARCH_SEARCH_API_KEY",)

TEST_QUERIES = [
    "real-time streaming reference architecture on Azure",
    "Event Hubs throughput limits and partitions",
    "Cosmos DB SLA and throughput guidance",
    "WAF reliability recommendations for Event Hubs and Cosmos DB",
    "Azure Functions and Stream Analytics limits for fraud detection",
]


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z]{4,}", text)}


def _has_relevance_overlap(query: str, top_item: dict) -> bool:
    query_tokens = _tokenize(query)
    candidate_text = " ".join(
        [
            str(top_item.get("source_document", "")),
            str(top_item.get("excerpt", "")),
        ]
    )
    candidate_tokens = _tokenize(candidate_text)
    return len(query_tokens.intersection(candidate_tokens)) > 0


@pytest.mark.integration
def test_knowledge_base_retrieve_end_to_end_and_parseable():
    missing = [env_name for env_name in REQUIRED_ENV_VARS if not os.getenv(env_name)]
    if missing:
        pytest.skip(f"Missing env vars for integration test: {', '.join(missing)}")

    session_id = "session_foundry_iq_test"

    for query in TEST_QUERIES:
        results = knowledge_base_retrieve(query=query, top_k=3)
        assert results, f"No results returned for query: {query}"

        top_item = results[0]
        assert top_item.get("source_url"), f"Missing citation/source_url for query: {query}"
        assert _has_relevance_overlap(query, top_item), (
            f"Top result does not appear relevant for query: {query}; "
            f"top source={top_item.get('source_document')}"
        )

        for raw in results:
            evidence = parse_kb_response_to_evidence_source(raw, session_id=session_id)
            assert evidence.session_id == session_id
            assert evidence.retrieved_via == "foundry_iq"
            assert evidence.kb_name

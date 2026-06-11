from __future__ import annotations

import os
from typing import Any

import httpx

from archimedes.models.evidence import EvidenceSource


def _search_endpoint() -> str:
    endpoint = os.getenv("ARCH_SEARCH_ENDPOINT")
    if endpoint:
        return endpoint.rstrip("/")

    service_name = os.getenv("ARCH_SEARCH_SERVICE_NAME")
    if not service_name:
        raise ValueError(
            "Missing search endpoint configuration. Set ARCH_SEARCH_ENDPOINT "
            "or ARCH_SEARCH_SERVICE_NAME."
        )
    return f"https://{service_name}.search.windows.net"


def _search_api_key() -> str:
    api_key = os.getenv("ARCH_SEARCH_API_KEY")
    if not api_key:
        raise ValueError("Missing ARCH_SEARCH_API_KEY for knowledge retrieval.")
    return api_key


def knowledge_base_retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Retrieve relevant chunks from the configured KB-backed Azure AI Search index."""

    endpoint = _search_endpoint()
    api_key = _search_api_key()
    index_name = os.getenv("ARCH_KB_INDEX", "archimedes-arch-idx")
    kb_name = os.getenv("ARCH_KB_NAME", "azure-architecture-kb")
    kb_version = os.getenv("ARCH_KB_VERSION", "v1")

    url = f"{endpoint}/indexes/{index_name}/docs/search"
    params = {"api-version": "2024-07-01"}
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "search": query,
        "queryType": "semantic",
        "semanticConfiguration": "semantic-default",
        "captions": "extractive",
        "answers": "extractive|count-3",
        "top": top_k,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, params=params, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()

    results: list[dict[str, Any]] = []
    for item in body.get("value", []):
        results.append(
            {
                "source_document": item.get("title") or item.get("metadata_storage_name"),
                "source_url": item.get("source_path"),
                "excerpt": item.get("content", "")[:1200],
                "chunk_id": item.get("id"),
                "score": item.get("@search.score"),
                "captions": item.get("@search.captions", []),
                "kb_name": kb_name,
                "kb_version": kb_version,
                "raw": item,
            }
        )
    return results


def parse_kb_response_to_evidence_source(raw_response: dict[str, Any], session_id: str) -> EvidenceSource:
    """Map a retrieval result into a validated EvidenceSource object."""

    source_name = raw_response.get("source_document") or "kb_document"
    source_url = raw_response.get("source_url")
    excerpt = raw_response.get("excerpt")

    return EvidenceSource(
        session_id=session_id,
        source=source_name,
        source_url=source_url,
        retrieved_via="foundry_iq",
        excerpt=excerpt,
        chunk_id=raw_response.get("chunk_id"),
        kb_name=raw_response.get("kb_name"),
        kb_version=raw_response.get("kb_version"),
    )

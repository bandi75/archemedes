from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv

from archimedes.models.evidence import EvidenceSource

load_dotenv()

logger = logging.getLogger(__name__)


def _use_mock_kb() -> bool:
    return os.getenv("USE_MOCK_KB", "false").strip().lower() in {"1", "true", "yes", "on"}


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

    logger.info(
        "[azure-search] POST %s | index=%s kb=%s@%s top_k=%d | query=%r",
        url,
        index_name,
        kb_name,
        kb_version,
        top_k,
        query[:120],
    )

    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, params=params, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "[azure-search] HTTP %s from %s — %s",
            exc.response.status_code,
            url,
            exc.response.text[:300],
        )
        raise
    except httpx.RequestError as exc:
        logger.error("[azure-search] Request failed: %s", exc)
        raise

    elapsed_ms = (time.perf_counter() - t0) * 1000
    hits = body.get("value", [])
    logger.info(
        "[azure-search] %d result(s) in %.0f ms | scores=%s",
        len(hits),
        elapsed_ms,
        [round(h.get("@search.score", 0), 3) for h in hits],
    )

    results: list[dict[str, Any]] = []
    for item in hits:
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


class FoundryIQRetriever:
    """Adapter layer for knowledge retrieval with optional mock fallback."""

    def __init__(self, default_session_id: str = "session_runtime"):
        self.default_session_id = default_session_id

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        *,
        session_id: str | None = None,
    ) -> list[EvidenceSource]:
        resolved_session_id = session_id or self.default_session_id

        if _use_mock_kb():
            logger.info("[kb-retriever] USE_MOCK_KB=true — returning fixture data (no Azure call)")
            from .mock_foundry_iq import MockFoundryIQAdapter

            return MockFoundryIQAdapter().retrieve(
                query=query,
                top_k=top_k,
                session_id=resolved_session_id,
            )

        logger.info("[kb-retriever] USE_MOCK_KB=false — calling Azure AI Search")
        raw_items = knowledge_base_retrieve(query=query, top_k=top_k)
        evidence = [
            parse_kb_response_to_evidence_source(raw_item, session_id=resolved_session_id)
            for raw_item in raw_items
        ]
        logger.info(
            "[kb-retriever] Retrieved %d evidence item(s) | sources=%s",
            len(evidence),
            [e.source for e in evidence],
        )
        return evidence


def retrieve_evidence(query: str, top_k: int = 5, session_id: str = "session_runtime") -> list[EvidenceSource]:
    """Convenience function used by specialist routines for retrieval."""

    return FoundryIQRetriever(default_session_id=session_id).retrieve(
        query=query,
        top_k=top_k,
        session_id=session_id,
    )

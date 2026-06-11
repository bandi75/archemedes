from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from archimedes.models.enums import ClaimType, QualityGateStatus, StageName
from archimedes.models.claims import ClaimRecord
from archimedes.models.patches import StagePatch
from archimedes.models.quality_gates import QualityGateResult


KNOWN_PATTERNS: dict[str, dict[str, list[str] | str]] = {
    "real_time_streaming": {
        "keywords": ["real-time", "stream", "event", "latency", "tps", "fraud"],
        "typical_pipeline": "ingestion -> enrichment -> scoring -> action",
        "azure_services_to_explore": ["Event Hubs", "Stream Analytics", "Azure Functions", "Cosmos DB"],
        "pattern_specific_nfrs": ["event ordering", "backpressure", "replay strategy"],
    },
    "event_driven": {
        "keywords": ["event-driven", "pub/sub", "queue", "topic", "asynchronous"],
        "typical_pipeline": "publish -> route -> process -> store",
        "azure_services_to_explore": ["Event Grid", "Service Bus", "Event Hubs"],
        "pattern_specific_nfrs": ["idempotency", "ordering guarantees", "dead-letter handling"],
    },
    "microservices": {
        "keywords": ["microservice", "service mesh", "bounded context", "api gateway"],
        "typical_pipeline": "api gateway -> service mesh -> domain services",
        "azure_services_to_explore": ["AKS", "Container Apps", "API Management"],
        "pattern_specific_nfrs": ["service isolation", "observability", "resilience"],
    },
    "serverless": {
        "keywords": ["serverless", "functions", "consumption", "event trigger"],
        "typical_pipeline": "trigger -> function execution -> persistence",
        "azure_services_to_explore": ["Azure Functions", "Logic Apps", "Container Apps jobs"],
        "pattern_specific_nfrs": ["cold start", "retry policy", "execution limits"],
    },
    "batch_analytics": {
        "keywords": ["batch", "etl", "warehouse", "nightly", "spark"],
        "typical_pipeline": "ingest -> transform -> aggregate -> serve",
        "azure_services_to_explore": ["Data Factory", "Synapse", "Databricks"],
        "pattern_specific_nfrs": ["batch windows", "cost optimization", "data quality"],
    },
    "ml_platform": {
        "keywords": ["ml", "model", "feature", "training", "inference"],
        "typical_pipeline": "feature ingestion -> model scoring -> feedback loop",
        "azure_services_to_explore": ["Azure ML", "AKS", "Managed online endpoints"],
        "pattern_specific_nfrs": ["model drift", "explainability", "feature freshness"],
    },
    "web_api": {
        "keywords": ["api", "rest", "http", "frontend", "web"],
        "typical_pipeline": "client -> gateway -> api -> datastore",
        "azure_services_to_explore": ["API Management", "App Service", "Container Apps"],
        "pattern_specific_nfrs": ["authn/authz", "rate limiting", "availability"],
    },
    "data_warehouse": {
        "keywords": ["warehouse", "bi", "analytics", "reporting", "olap"],
        "typical_pipeline": "source systems -> warehouse -> semantic model -> reporting",
        "azure_services_to_explore": ["Synapse", "Fabric", "SQL Database"],
        "pattern_specific_nfrs": ["query performance", "governance", "data retention"],
    },
}


@dataclass(slots=True)
class PatternDetector:
    confidence_threshold: float = 0.55

    def detect(
        self,
        *,
        session_id: str,
        stage_run_id: str,
        base_version: int,
        requirements_text: str,
    ) -> StagePatch:
        scores = self._score_patterns(requirements_text)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top = [(name, score) for name, score in ranked if score > 0][:3]

        if not top:
            gate = QualityGateResult(
                status=QualityGateStatus.FAILED,
                blocking_failures=["No primary architecture pattern identified."],
                user_override_allowed=False,
            )
            patch_payload = {
                "primary_pattern": None,
                "secondary_patterns": [],
                "confidence": 0.0,
                "signals": [],
                "typical_pipeline": None,
                "azure_services_to_explore": [],
                "pattern_specific_nfrs": [],
            }
        else:
            primary_name, primary_score = top[0]
            secondary = [name for name, _ in top[1:]]
            primary_meta = KNOWN_PATTERNS[primary_name]
            confidence = min(1.0, max(0.0, primary_score))

            warnings: list[str] = []
            if len(top) > 1:
                warnings.append("Multiple patterns detected; confirm primary pattern with user.")
            if confidence < self.confidence_threshold:
                warnings.append("Pattern confidence below threshold; validation needed.")

            gate = QualityGateResult(
                status=(
                    QualityGateStatus.PASSED_WITH_WARNINGS
                    if warnings
                    else QualityGateStatus.PASSED
                ),
                warnings=warnings,
                user_override_allowed=True,
            )
            patch_payload = {
                "primary_pattern": primary_name,
                "secondary_patterns": secondary,
                "confidence": round(confidence, 3),
                "signals": self._extract_signals(requirements_text, primary_name),
                "typical_pipeline": primary_meta["typical_pipeline"],
                "azure_services_to_explore": primary_meta["azure_services_to_explore"],
                "pattern_specific_nfrs": primary_meta["pattern_specific_nfrs"],
                "all_detected_patterns": [
                    {
                        "pattern": name,
                        "confidence_score": round(score, 3),
                    }
                    for name, score in top
                ],
            }

        patch_hash = self._compute_hash(patch_payload)
        claim = ClaimRecord(
            session_id=session_id,
            claim=(
                "Pattern detector identified the most likely architecture pattern from requirements "
                "signals using deterministic scoring."
            ),
            type=ClaimType.RECOMMENDATION,
            confidence=0.78,
            stage=StageName.PATTERN_DETECTION,
            evidence_ids=[],
        )
        idempotency_key = hashlib.sha256(
            f"{session_id}:{StageName.PATTERN_DETECTION.value}:{stage_run_id}:{patch_hash}".encode("utf-8")
        ).hexdigest()

        return StagePatch(
            session_id=session_id,
            stage=StageName.PATTERN_DETECTION,
            stage_run_id=stage_run_id,
            base_version=base_version,
            target_version=base_version + 1,
            idempotency_key=idempotency_key,
            patch_hash=patch_hash,
            patch=patch_payload,
            claims=[claim],
            evidence_sources=[],
            quality_gate_result=gate,
        )

    def _score_patterns(self, text: str) -> dict[str, float]:
        lowered = text.lower()
        scores: dict[str, float] = {}
        for name, meta in KNOWN_PATTERNS.items():
            keywords = meta["keywords"]
            assert isinstance(keywords, list)
            hits = sum(1 for keyword in keywords if keyword in lowered)
            scores[name] = hits / max(len(keywords), 1)
        return scores

    @staticmethod
    def _extract_signals(text: str, primary_pattern: str) -> list[str]:
        signals: list[str] = []
        lowered = text.lower()
        keywords = KNOWN_PATTERNS[primary_pattern]["keywords"]
        assert isinstance(keywords, list)
        for keyword in keywords:
            if keyword in lowered:
                signals.append(keyword)
        return signals[:6]

    @staticmethod
    def _compute_hash(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

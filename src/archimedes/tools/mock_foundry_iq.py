from __future__ import annotations

from dataclasses import dataclass

from archimedes.models.evidence import EvidenceSource


@dataclass(frozen=True)
class MockEvidenceFixture:
    source: str
    source_url: str
    excerpt: str
    chunk_id: str


class MockFoundryIQAdapter:
    """Fixture-backed adapter used when live Foundry IQ retrieval is disabled."""

    def __init__(self) -> None:
        self._fixture_map: dict[tuple[str, ...], list[MockEvidenceFixture]] = {
            ("event", "hubs", "partition", "throughput"): [
                MockEvidenceFixture(
                    source="Event Hubs limits and quotas",
                    source_url="https://learn.microsoft.com/azure/event-hubs/event-hubs-quotas",
                    excerpt=(
                        "Throughput capacity is governed by throughput units or processing units, "
                        "with partition count and ingress limits shaping sustained event rate."
                    ),
                    chunk_id="mock_event_hubs_limits_01",
                ),
            ],
            ("cosmos", "throughput", "ru", "write"): [
                MockEvidenceFixture(
                    source="Cosmos DB throughput and partitioning guidance",
                    source_url="https://learn.microsoft.com/azure/cosmos-db/partitioning-overview",
                    excerpt=(
                        "Provisioned throughput in RU/s should align to partition strategy to avoid hot "
                        "partitions and maintain predictable write performance."
                    ),
                    chunk_id="mock_cosmos_throughput_01",
                ),
            ],
            ("pci", "compliance", "security"): [
                MockEvidenceFixture(
                    source="Azure compliance offerings",
                    source_url="https://learn.microsoft.com/azure/compliance/offerings/offering-pci-dss",
                    excerpt=(
                        "Azure provides PCI DSS attestation details that should be mapped to workload scope, "
                        "shared responsibility, and compensating controls."
                    ),
                    chunk_id="mock_pci_dss_01",
                ),
            ],
            ("99.95", "sla", "availability"): [
                MockEvidenceFixture(
                    source="Azure architecture reliability considerations",
                    source_url=(
                        "https://learn.microsoft.com/azure/well-architected/reliability/principles"
                    ),
                    excerpt=(
                        "Meeting a 99.95 percent target usually requires multi-zone or multi-region patterns, "
                        "plus resilient dependency design and health-based failover."
                    ),
                    chunk_id="mock_sla_reliability_01",
                ),
            ],
            ("real-time", "stream", "analytics", "event"): [
                MockEvidenceFixture(
                    source="Real-time analytics architecture on Azure",
                    source_url=(
                        "https://learn.microsoft.com/azure/architecture/reference-architectures/data/real-time-analytics"
                    ),
                    excerpt=(
                        "Event Hubs, Stream Analytics, and downstream storage/serving layers are common for "
                        "real-time detection and alerting pipelines."
                    ),
                    chunk_id="mock_realtime_pipeline_01",
                ),
            ],
            ("aks", "container", "apps", "tradeoff"): [
                MockEvidenceFixture(
                    source="AKS versus Azure Container Apps",
                    source_url=(
                        "https://learn.microsoft.com/azure/container-apps/compare-options"
                    ),
                    excerpt=(
                        "AKS provides deeper Kubernetes control, while Container Apps reduces operational burden "
                        "for event-driven and microservice workloads."
                    ),
                    chunk_id="mock_aks_vs_aca_01",
                ),
            ],
        }

        self._fallback_fixtures: list[MockEvidenceFixture] = [
            MockEvidenceFixture(
                source="Azure Architecture Center overview",
                source_url="https://learn.microsoft.com/azure/architecture/",
                excerpt=(
                    "Use architecture guidance as a baseline and validate assumptions against service-specific "
                    "limits, reliability, and security guidance."
                ),
                chunk_id="mock_architecture_center_01",
            )
        ]

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        *,
        session_id: str = "session_mock",
    ) -> list[EvidenceSource]:
        normalized_query = query.lower()
        selected: list[MockEvidenceFixture] = []

        for keyword_group, fixtures in self._fixture_map.items():
            if all(keyword in normalized_query for keyword in keyword_group):
                selected.extend(fixtures)

        if not selected:
            selected = list(self._fallback_fixtures)

        evidence_items = [
            EvidenceSource(
                session_id=session_id,
                source=fixture.source,
                source_url=fixture.source_url,
                retrieved_via="mock",
                excerpt=fixture.excerpt,
                chunk_id=fixture.chunk_id,
                kb_name="mock-kb",
                kb_version="fixture-v1",
                is_fixture=True,
            )
            for fixture in selected[: max(top_k, 0)]
        ]
        return evidence_items

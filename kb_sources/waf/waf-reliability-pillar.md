<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/reliability/overview -->
<!-- publication_date: 2025-11-01 -->
<!-- category: waf -->

# Azure Well-Architected Framework — Reliability Pillar

The Reliability pillar of the Azure Well-Architected Framework ensures your workload can **meet commitments to your customers** around availability and recoverability. A reliable workload is resilient — it handles failures gracefully — and available — it operates at its intended capacity when customers need it.

## Design Principles

### 1. Design for Business Requirements
- Define clear availability targets (e.g., 99.95%, 99.99%) tied to business impact
- Establish recovery time objectives (RTO) and recovery point objectives (RPO) per component
- Differentiate critical path components from non-critical ones — not everything needs 99.999%

### 2. Design for Resilience
- Assume all components will eventually fail
- Eliminate single points of failure at every tier (compute, data, network, identity)
- Use redundancy: active-active for highest availability, active-passive for lower cost
- Apply bulkhead pattern: isolate failures to prevent cascade

### 3. Design for Recovery
- Automate recovery where possible (self-healing, auto-restart, auto-failover)
- Test recovery procedures regularly — untested recovery is not recovery
- Use chaos engineering to find weaknesses before they become incidents

### 4. Design for Observability
- Instrument every component with health signals, metrics, and logs
- Define actionable health model: green/yellow/red for each component
- Alert on symptoms (user-visible impact), not just causes (CPU spikes)

### 5. Keep It Simple
- Complexity is the enemy of reliability — every dependency is a potential failure point
- Use managed services over custom infrastructure where possible
- Avoid distributed transactions; use eventual consistency and compensation

## Key Reliability Metrics

| Metric | Definition | Formula |
|---|---|---|
| **Availability** | % of time the system operates as intended | Uptime / (Uptime + Downtime) × 100 |
| **MTBF** | Mean Time Between Failures | Average time between failures |
| **MTTR** | Mean Time To Recovery | Average time to restore service |
| **RTO** | Recovery Time Objective | Max acceptable downtime per incident |
| **RPO** | Recovery Point Objective | Max acceptable data loss (time) |

### SLA Nines Reference

| SLA | Monthly downtime | Annual downtime |
|---|---|---|
| 99% | 7.2 hours | 87.6 hours |
| 99.5% | 3.6 hours | 43.8 hours |
| 99.9% | 43.8 min | 8.76 hours |
| 99.95% | 21.9 min | 4.38 hours |
| 99.99% | 4.38 min | 52.6 min |
| 99.999% | 26.3 sec | 5.26 min |

## Reliability Patterns

### Retry
Automatically retry transient failures with exponential backoff and jitter. Most Azure SDK clients implement retry by default.

### Circuit Breaker
Stop calling a failing dependency temporarily to allow it to recover. Prevents cascade failures. Implement with Polly (.NET) or equivalent libraries.

### Bulkhead
Isolate components so a failure in one does not exhaust shared resources (thread pools, connections) and take down others.

### Health Endpoint Monitoring
Expose a `/health` endpoint that checks downstream dependencies. Used by load balancers, Kubernetes liveness/readiness probes, and Azure Container Apps.

### Queue-Based Load Leveling
Use a queue (Event Hubs, Service Bus) to buffer load spikes. Consumers process at a sustainable rate regardless of producer spikes.

### Geodes / Active-Active Multi-Region
Deploy the workload to multiple regions simultaneously. Route traffic to the nearest healthy region. Highest availability; highest cost and complexity.

## Azure Reliability Features by Service

| Service | Key Reliability Features |
|---|---|
| **Event Hubs** | Zone redundancy (auto, Standard+), Geo-DR namespace pairing, Geo-replication (Premium/Dedicated) |
| **Cosmos DB** | 99.999% SLA (multi-region writes), automatic failover, zone redundancy, multi-master writes |
| **AKS** | Availability zone node pools, pod disruption budgets, node auto-repair |
| **Azure Functions** | Zone-redundant Premium plan, Flex Consumption plan scaling to 1,000 instances |
| **Stream Analytics** | Zone-redundant deployment (automatic in supported regions), exactly-once processing |
| **Azure Monitor** | 99.9% SLA for query and ingestion, zone-redundant Log Analytics workspaces |

## Reliability Checklist for Fraud Detection Architectures

- [ ] **Availability target defined**: Is the required SLA documented (e.g., 99.95%)?
- [ ] **No single points of failure**: Are all critical components zone-redundant or multi-instance?
- [ ] **Event Hubs geo-DR configured**: Is there a paired namespace in a secondary region?
- [ ] **Cosmos DB multi-region writes**: Is active-active replication enabled for 99.999% SLA?
- [ ] **AKS node pool across zones**: Are system and user node pools spread across 3 availability zones?
- [ ] **Stream Analytics SU headroom**: Is SU% < 80% under peak load?
- [ ] **Retry policies implemented**: Do all SDK clients have retry + circuit breaker configured?
- [ ] **Health endpoints exposed**: Do all services expose health probes consumed by load balancers/probes?
- [ ] **Chaos engineering**: Has at least one failure mode been tested (AZ failure, dependency unavailability)?
- [ ] **RTO/RPO tested**: Has the recovery procedure been exercised within the defined RTO?

## Fraud Detection Specific Reliability Concerns

1. **Event Hubs partition limits**: At 10K TPS with Standard tier, monitor for partition hot-spotting if partition key has low cardinality. At 100K TPS, Standard tier TU limits may be exceeded — use Premium tier.

2. **Stream Analytics at scale**: Temporal joins require the join window to fit in memory. Large windows (> 1 hour) at high TPS may cause SU exhaustion. Monitor `InputEventBytes` and `SU%` metrics.

3. **Cosmos DB write throughput**: Hot partitions cause 429 (throttling) errors. Choose partition key carefully; use autoscale to absorb spikes. Monitor `NormalizedRUConsumption` metric — alert at > 80%.

4. **AKS node failure recovery**: Use pod disruption budgets (PDB) to prevent all pods from being evicted simultaneously during node maintenance. Set `minAvailable: 1` at minimum.

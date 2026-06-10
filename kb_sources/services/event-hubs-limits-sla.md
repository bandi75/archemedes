<!-- source_url: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-quotas -->
<!-- publication_date: 2026-02-05 -->
<!-- category: services -->

# Azure Event Hubs — Service Limits and SLA

## SLA

| Tier | Monthly Uptime SLA |
|---|---|
| Basic | 99.95% |
| Standard | 99.95% |
| Premium | 99.99% |
| Dedicated | 99.99% |

99.95% = up to 21.9 minutes downtime/month  
99.99% = up to 4.4 minutes downtime/month

SLA covers ability to send and receive events. Excludes force majeure, customer configuration errors, and scheduled maintenance.

---

## Common Limits (All Tiers)

| Quota | Limit |
|---|---|
| Event Hubs namespaces per subscription per region | 100 (soft limit; can be increased) |
| Event Hubs per namespace | 10 (Basic), 10 (Standard), 100 (Premium), 1,024 (Dedicated) |
| Maximum event size | 1 MB |
| Maximum metadata size | 64 KB |
| Consumer groups per event hub | 1 (Basic), 20 (Standard), 100 (Premium), 1,000 (Dedicated) |
| Concurrent AMQP connections per namespace | 100 (Basic), 5,000 (Standard), 10,000 (Premium), 100,000 (Dedicated) |
| Maximum message retention | 1 day (Basic), 7 days (Standard), 90 days (Premium/Dedicated) |
| Maximum throughput units / processing units | 100 TU (Basic/Standard), 16 PU (Premium), N/A (Dedicated — reserved) |

---

## Tier-Specific Limits

### Basic Tier
| Feature | Limit |
|---|---|
| Throughput units (TU) | 1–100 per namespace |
| 1 TU ingress | 1 MB/s or 1,000 events/s (whichever comes first) |
| 1 TU egress | 2 MB/s |
| Partitions per event hub | 32 |
| Retention | 1 day |
| Consumer groups | 1 per event hub |
| Schema Registry | Not available |
| Capture (auto-archive) | Not available |
| Auto-inflate | Not available |

### Standard Tier
| Feature | Limit |
|---|---|
| Throughput units (TU) | 1–100 per namespace (up to 200 with quota increase) |
| 1 TU ingress | 1 MB/s or 1,000 events/s |
| 1 TU egress | 2 MB/s |
| Partitions per event hub | 32 |
| Retention | 1–7 days |
| Consumer groups | 20 per event hub |
| Schema Registry | Yes |
| Capture (auto-archive to Blob/ADLS) | Yes |
| Auto-inflate | Yes (TUs scale automatically up to configured maximum) |
| Kafka endpoint | Yes |
| Private Link | Yes |

### Premium Tier
| Feature | Limit |
|---|---|
| Processing units (PU) | 1–16 per namespace |
| 1 PU ingress | ~100 MB/s (dedicated compute, higher burst capacity) |
| Partitions per event hub | 100 |
| Retention | 1–90 days |
| Consumer groups | 100 per event hub |
| Concurrent connections | 10,000 per namespace |
| Geo-replication | Yes (cross-region data replication) |
| Private Link | Yes |
| Customer-managed keys | Yes |

### Dedicated Tier (Capacity Units)
| Feature | Limit |
|---|---|
| Capacity units (CU) | 1–20 (each CU adds dedicated resources) |
| Partitions per event hub | 1,024 |
| Event Hubs per namespace | 1,024 |
| Retention | 1–90 days |
| Consumer groups | 1,000 per event hub |
| Dedicated single-tenant cluster | Yes (no noisy neighbor) |

---

## Throughput Calculations

### Standard Tier Sizing

| TPS | Avg Event Size | Required Ingress MB/s | Min TUs | Recommended TUs (with buffer) |
|---|---|---|---|---|
| 1,000 TPS | 512 B | 0.5 MB/s | 1 TU | 2 TU |
| 10,000 TPS | 512 B | 5 MB/s | 5 TU | 10 TU |
| 10,000 TPS | 1 KB | 10 MB/s | 10 TU | 15 TU |
| 50,000 TPS | 512 B | 25 MB/s | 25 TU | 35 TU |

For 10K TPS with 512-byte events: **10 TUs with auto-inflate to 20 TUs** is the recommended Standard tier configuration.

### When to Upgrade to Premium
- Ingress consistently > 50 MB/s (> 50 TU sustained)
- Need > 32 partitions
- Need > 7-day retention
- Need Geo-replication (event data replication, not just metadata)
- Need dedicated compute for predictable latency

### When 100K TPS Requires Premium
- 100,000 TPS × 512 B = ~50 MB/s ingress → at the top of Standard tier capacity
- Burst events or larger payloads will exceed Standard limits immediately
- **Recommendation**: Premium tier, 4–8 PUs, 100 partitions for 100K TPS workloads

---

## Partitions

- Partition count is set at **event hub creation time**
- Standard: cannot be decreased; can be increased (up to 32) after creation
- Premium/Dedicated: can be increased up to tier maximum
- Consumer parallelism is bounded by partition count — you cannot have more active consumers than partitions per consumer group
- **Rule of thumb**: set partitions = expected maximum consumer instances

## Auto-inflate (Standard Tier Only)

Auto-inflate automatically increases TU count when:
- The namespace is being throttled (incoming data exceeds current TU capacity)
- Usage has exceeded 75% of current TU limit for 15+ minutes

Configure: enable auto-inflate, set maximum TU count. Recommended: set maximum to 3–5× baseline.

## Retention and Capture

- Events are retained for the configured retention period regardless of whether they've been consumed
- After retention expires, events are permanently deleted
- **Event Hubs Capture**: automatically archives raw events to Azure Blob Storage or ADLS Gen2
  - Format: Apache Avro
  - Minimum capture interval: 5 minutes or 500 MB (whichever comes first)
  - Enables long-term storage at storage costs (~$0.02/GB) instead of Event Hubs retention costs

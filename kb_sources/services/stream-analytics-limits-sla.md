<!-- source_url: https://learn.microsoft.com/en-us/azure/stream-analytics/stream-analytics-quota-policy -->
<!-- publication_date: 2026-02-05 -->
<!-- category: services -->

# Azure Stream Analytics — Service Limits and SLA

## SLA

| Service | SLA |
|---|---|
| Azure Stream Analytics (Cloud) | 99.9% monthly uptime |
| Azure Stream Analytics on IoT Edge | No SLA (depends on edge device) |

99.9% = up to 43.8 minutes downtime/month

SLA covers job availability — the ability to submit, start, and run streaming jobs. Does not cover data loss due to customer-side issues (output sink unavailability, incorrect query logic).

---

## Streaming Units (SU) Limits

Streaming Units (SUs) represent the computing resources allocated to a Stream Analytics job. Each SU provides approximately 1 MB/s of throughput (varies by query complexity).

| Limit | Value |
|---|---|
| Minimum SUs per job | 1 SU |
| Maximum SUs per job (standard) | 192 SUs |
| Maximum SUs per job (with quota increase) | 528 SUs |
| SU increment | 1, 3, 6, 12, 18, 24, 30, 36, 48, 60, 72, 84, 96, 120, 144, 168, 192 |
| Maximum jobs per subscription per region | 200 (soft limit; can be increased) |

**Note**: SU count must be set to specific supported values. The step increments above reflect the supported SU configurations.

---

## Input and Output Limits

| Limit | Value |
|---|---|
| Maximum inputs per job | 60 |
| Maximum outputs per job | 60 |
| Maximum functions per job (UDFs, UDAs, ML) | 60 |
| Maximum reference data inputs | 5 per job |
| Maximum reference data size | 300 MB per reference data set |
| Maximum reference data refresh rate | Once per minute |

---

## Query and Processing Limits

| Limit | Value |
|---|---|
| Maximum query complexity | Limited by allocated SUs |
| Maximum event size | 1 MB (events larger than 1 MB are dropped) |
| Maximum event batch size for ingestion | 64 MB per read |
| Maximum late arrival tolerance | 21 days |
| Maximum out-of-order tolerance | 21 days |
| Maximum window duration (time-based windows) | 7 days |
| Maximum window duration (count-based windows) | No hard limit (bound by memory) |
| Maximum query result size per output write | Depends on output sink limits |

---

## Windowing Function Limits

| Window Type | Maximum Duration |
|---|---|
| TumblingWindow | 7 days |
| HoppingWindow | 7 days total window size |
| SlidingWindow | 7 days |
| SessionWindow | 7 days per session (inactivity gap configurable) |

For fraud detection velocity checks: 15-minute hopping windows are well within limits.

---

## State and Checkpoint Limits

| Limit | Value |
|---|---|
| Maximum in-memory state per SU | ~50 MB per SU (approximate) |
| Checkpoint frequency | Every 3 minutes (approximate) |
| Recovery time after failure | Typically < 3 minutes (resumes from last checkpoint) |
| Maximum temporal join window | 7 days |

---

## SU Consumption by Query Type (Reference)

| Query Pattern | Typical SU per Partition |
|---|---|
| Simple filter / projection | 1 SU |
| Single-stream aggregation (tumbling window) | 1–3 SU |
| Multi-stream temporal join | 3–6 SU |
| Anomaly detection functions | 3–6 SU |
| Complex CEP with multiple joins | 6–12 SU |
| Full fraud detection pipeline | 12–24+ SU (depends on partition count) |

**Alert threshold**: Investigate and add SUs when sustained `SU%` metric > 80%.

---

## Parallelization

Stream Analytics jobs scale by parallelizing query steps across streaming nodes:

- Use `PARTITION BY PartitionId` to match Event Hubs partition count
- A fully parallelized job on 32-partition Event Hub: each partition processed independently
- Non-parallelizable steps (e.g., `GROUP BY` without `PARTITION BY`) run on a single node and become bottlenecks

### Parallel Job Sizing (Fraud Detection, 32 partitions)

| Scenario | Recommended SUs |
|---|---|
| 10K TPS, simple filter + window | 12 SUs (6 per 16 partitions) |
| 10K TPS, temporal join + anomaly detection | 24–36 SUs |
| 100K TPS, temporal join + anomaly detection | 96–192 SUs |

For 100K TPS, consider:
1. Upgrading to ASA with 96–192 SUs, OR
2. Replacing ASA with Apache Spark on AKS (more control, higher operational complexity)

---

## Inputs: Event Hubs Specifics

| Limit | Value |
|---|---|
| Maximum consumer groups used by ASA per Event Hub | 1 per ASA job (configure a dedicated consumer group) |
| Maximum Event Hubs inputs per job | 60 |
| Partition alignment | ASA partitions should match Event Hub partitions for full parallelism |
| Supported authentication | SAS (connection string) or managed identity |

**Best practice**: Create a dedicated Event Hubs consumer group per Stream Analytics job (e.g., `$asa-fraud-detection`). Never share consumer groups between jobs.

---

## Outputs: Cosmos DB Specifics

| Limit | Value |
|---|---|
| Maximum throughput for Cosmos DB output | Bound by Cosmos DB provisioned RU/s |
| Batch size to Cosmos DB | Configurable (default: 10,000 records per write batch) |
| Retry on 429 (throttling) | Automatic retry with exponential backoff |
| Partition key specification | Required; set to match Cosmos DB container partition key |

---

## Monitoring Metrics

| Metric | Description | Alert Threshold |
|---|---|---|
| `SU (%)` | % of allocated SUs being used | > 80% sustained → add SUs |
| `InputEventBytes` | Bytes read from inputs per second | Monitor for unexpected drops |
| `InputEvents` | Event count read from inputs | Drop to 0 for > 5 min → check input |
| `OutputEvents` | Event count written to outputs | Drop when input is flowing → check query/output |
| `WatermarkDelaySeconds` | How far behind the job is | Growing → job cannot keep up |
| `EarlyInputEvents` | Events arriving before expected time | Informational |
| `LateInputEvents` | Events arriving after window closes | High count → increase late arrival tolerance |
| `DroppedOrAdjustedEvents` | Events dropped due to policy | Any non-zero → investigate |

---

## Cluster Mode (Stream Analytics Cluster)

For workloads requiring VNet isolation or > 192 SUs across multiple jobs:

| Limit | Value |
|---|---|
| Minimum cluster SUs | 36 SUs |
| Maximum cluster SUs | 528 SUs |
| Maximum jobs per cluster | No hard limit |
| VNet integration | Yes (cluster runs inside your VNet) |
| Private endpoints | Yes |

Stream Analytics Cluster is the recommended approach when:
- Output or input services are in a VNet with no public access
- You need more than 192 SUs in a single job
- You want to consolidate multiple jobs with shared resources

---

## Pricing

| Item | Price (East US, approximate) |
|---|---|
| Streaming Units | $0.11/SU/hour |
| Standard job, 6 SUs, 24/7 | ~$475/month |
| Standard job, 24 SUs, 24/7 | ~$1,900/month |
| Cluster (36 SUs min), 24/7 | ~$2,850/month |

Stopped jobs do not incur SU charges. Cost stops when the job is stopped, not just when there are no events.

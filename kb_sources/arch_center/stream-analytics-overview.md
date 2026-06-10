<!-- source_url: https://learn.microsoft.com/en-us/azure/stream-analytics/stream-analytics-introduction -->
<!-- publication_date: 2026-02-05 -->
<!-- category: arch_center -->

# Azure Stream Analytics Overview

Azure Stream Analytics is a fully managed stream processing engine that analyzes and processes large volumes of streaming data with submillisecond latencies. You can build a streaming data pipeline by using Stream Analytics to identify patterns and relationships in data that originates from various input sources including applications, devices, sensors, clickstreams, and social media feeds.

## Key Use Cases

- Anomaly detection in sensor data to detect spikes, dips, and slow positive and negative changes
- Geo-spatial analytics for fleet management and driverless vehicles
- Remote monitoring and predictive maintenance of high value assets
- Clickstream analytics to determine customer behavior
- Real-time telemetry streams and logs from applications and IoT devices
- **Real-time fraud detection**: correlate transaction streams with account activity, detect velocity anomalies

## Fully Managed Service

Stream Analytics is a fully managed (PaaS) offering on Azure. You do not provision hardware or infrastructure, update OS, or manage software. The service handles all infrastructure concerns, letting you focus on your business logic.

## Query Language

Stream Analytics uses a **SQL query language augmented with temporal constraints** to analyze data in motion. Key capabilities:

- Complex Event Processing (CEP) with windowing functions
- Temporal joins across multiple input streams
- Built-in anomaly detection functions
- Geospatial functions
- Pattern matching
- Reference data joins (static lookup tables)
- JavaScript and C# User-Defined Functions (UDFs)
- Azure Machine Learning integration for custom models

### Windowing Functions

| Function | Description | Use case |
|---|---|---|
| `TumblingWindow` | Fixed, non-overlapping time windows | Per-minute aggregation |
| `HoppingWindow` | Overlapping windows with configurable hop | Rolling averages |
| `SlidingWindow` | Event-driven windows that slide continuously | Detect events within N minutes of each other |
| `SessionWindow` | Variable-length windows based on activity gaps | User session analytics |
| `SnapshotWindow` | Groups events with same timestamp | Batch-style processing |

### Anomaly Detection

Built-in functions for time-series anomaly detection:
- `AnomalyDetection_SpikeAndDip`: detects temporary anomalies (spikes and dips)
- `AnomalyDetection_ChangePoint`: detects persistent changes in the level or trend of a time series

## Inputs and Outputs

### Inputs
- Azure Event Hubs (primary streaming source)
- Azure IoT Hub
- Azure Blob Storage / Data Lake Storage Gen2 (batch reference data or historical replay)
- Azure SQL Database (reference data for enrichment)

### Outputs
- Azure Cosmos DB
- Azure SQL Database
- Azure Blob Storage / Data Lake Storage Gen2
- Azure Event Hubs (chained pipelines)
- Azure Service Bus
- Power BI (real-time dashboards)
- Azure Synapse Analytics
- Azure Functions (serverless triggers)

## Scaling: Streaming Units (SUs)

Computing resources allocated to a Stream Analytics job are measured in **Streaming Units (SUs)**:

- 1 SU ≈ 1 MB/s throughput (approximate; depends on query complexity)
- Jobs scale best when fully parallelized using `PARTITION BY`
- Partitioned jobs distribute work across streaming nodes matching Event Hubs partitions
- Windowing functions and temporal joins require more SUs
- Auto-scale: available in ASA for Cloud jobs

### Scaling Guidelines

| Query Type | SU Recommendation |
|---|---|
| Simple pass-through or filter | 1–3 SUs per partition |
| Single-stream aggregation with window | 3–6 SUs |
| Multi-stream temporal join | 6–12 SUs |
| Complex CEP with multiple joins + anomaly detection | 12–24+ SUs |

**Warning threshold**: Investigate and scale when sustained SU% > 80%.

## Reliability

- **Exactly-once event processing** guaranteed with selected outputs
- **At-least-once delivery** for all outputs
- Built-in checkpointing maintains job state for recovery
- **Availability zones**: automatically distributes job resources across zones in supported regions — no extra configuration or cost required
- **SLA**: 99.9% availability at minute-level granularity

## Security

- All incoming and outgoing communications encrypted (TLS 1.2)
- Built-in checkpoints also encrypted
- No data stored at rest (all processing in-memory)
- Azure Virtual Networks support in Stream Analytics Clusters
- Managed identity for authenticated access to Event Hubs, Cosmos DB, and other outputs — no secrets in configuration

## Performance

- Processes millions of events per second
- Submillisecond latency achievable at scale
- Parallelism via `PARTITION BY` for horizontal scaling
- Built on Trill, a high-performance in-memory streaming analytics engine

## Pricing

- Pay only for Streaming Units consumed (no upfront costs)
- Standard: ~$0.11/SU/hour (East US, approximate)
- No cluster provisioning required
- Scale the job up or down based on workload

## IoT Edge

Stream Analytics can run on IoT Edge devices for ultra-low latency analytics at the device level. Same query language as cloud, enabling hybrid edge + cloud architectures.

## Next Steps

For fraud detection architecture using Stream Analytics:
- Configure Event Hubs input with `PARTITION BY PartitionId`
- Use `HoppingWindow` for velocity-based fraud signals
- Join transaction stream with account activity stream using temporal join (5-minute window)
- Output alerts to Cosmos DB and forward high-confidence fraud signals to Event Hubs for downstream action

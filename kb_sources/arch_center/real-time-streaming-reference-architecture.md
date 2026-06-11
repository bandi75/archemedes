<!-- source_url: https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/data/stream-processing-stream-analytics -->
<!-- publication_date: 2026-02-05 -->
<!-- category: arch_center -->

# Real-Time Stream Processing with Azure Stream Analytics

This reference architecture shows an end-to-end stream processing pipeline. The pipeline ingests data from two sources, correlates records in the two streams, and calculates a rolling average across a time window. The results are stored for further analysis.

## Architecture

The architecture consists of the following components:

**Data sources**: Two data sources generate data streams in real time. The first stream contains ride information, and the second contains fare information. In a real application, data sources would be IoT devices or application services generating high-velocity event streams.

**Azure Event Hubs**: An event ingestion service. This architecture uses two event hub instances, one for each data source. Each data source sends a stream of data to the associated event hub.

**Azure Stream Analytics**: An event-processing engine. A Stream Analytics job reads the data streams from the two event hubs and performs stream processing.

**Azure Cosmos DB**: The output from the Stream Analytics job is a series of records, which are written as JSON documents to a Cosmos DB document database.

**Azure Monitor**: Collects performance metrics about the Azure services deployed in the solution.

## Workflow

1. Producers send events to Event Hubs partitions using a partition key (e.g., device ID or entity ID) to ensure correlated events land on the same partition.
2. Stream Analytics reads from Event Hubs using consumer groups, one per job.
3. The ASA job performs temporal joins, windowed aggregations, and anomaly detection using SQL-like query language.
4. Results are written to Cosmos DB, Power BI, or other sinks.
5. Azure Monitor surfaces throughput, latency, and error metrics.

## Scenario Details

**Fraud Detection Use Case**: A financial platform collects transaction events and account state events from separate producers. The pipeline:
- Ingests transaction events (amount, merchant, location, timestamp) via one Event Hub
- Ingests account activity events (login, device fingerprint, velocity signals) via a second Event Hub
- Joins the two streams within a temporal window (e.g., 5 minutes) on account ID
- Computes rolling fraud signals (velocity, geo-distance, amount deviation) using hopping windows
- Emits alerts and enriched transaction records to Cosmos DB for downstream action

## Data Ingestion

Event Hubs uses **partitions** to segment the data. Partitions allow consumers to read each partition in parallel. Specifying a partition key ensures correlated events (e.g., all events for the same customer) land on the same partition, enabling stateful joins without cross-partition shuffles.

For fraud detection, the partition key should be the customer or account ID to co-locate all signals for a given customer.

## Stream Processing with ASA

The Stream Analytics SQL query language supports:
- `PARTITION BY` for parallel execution across partitions
- Temporal joins: `JOIN ... ON ... AND DATEDIFF(minute, streamA, streamB) BETWEEN 0 AND 5`
- Windowing functions: `TumblingWindow`, `HoppingWindow`, `SlidingWindow`, `SessionWindow`
- Anomaly detection: `AnomalyDetection_SpikeAndDip`, `AnomalyDetection_ChangePoint`
- Reference data joins for static lookup tables (e.g., merchant risk scores, geo-blocklists)

Example query for rolling average tip per mile:
```sql
SELECT System.Timestamp AS WindowTime,
       SUM(tr.TipAmount) / SUM(tr.TripDistanceInMiles) AS AverageTipPerMile
  INTO [TaxiDrain]
  FROM [Step3] tr
  GROUP BY HoppingWindow(Duration(minute, 5), Hop(minute, 1))
```

## Performance Considerations

### Event Hubs
- Throughput capacity is measured in **throughput units** (Standard) or **processing units** (Premium).
- Enable **auto-inflate** to automatically scale throughput units up to a configured maximum.
- Monitor for throttling: consistent throttling means the event hub needs more throughput units.

### Stream Analytics
- Computing resources are measured in **Streaming Units (SU)**.
- Jobs scale best when parallelized using `PARTITION BY` matching the Event Hubs partition count.
- Windowing functions and temporal joins require additional SUs.
- Use the Stream Analytics job diagram to see partition assignments per step.
- Warning threshold: investigate when SU consumption exceeds 80%.

### Cosmos DB
- Throughput is measured in **Request Units (RU/s)**.
- Choose a partition key that spreads both storage and request volume evenly to avoid hot partitions.
- A single physical partition serves up to 10,000 RU/s.

## Monitoring Signals

| Signal | Threshold | Action |
|---|---|---|
| Event Hubs throttled requests | Any sustained throttling | Increase throughput units or enable auto-inflate |
| Stream Analytics SU% | > 80% | Add more Streaming Units |
| Cosmos DB throttled requests (429) | Any sustained 429s | Increase RU/s provisioning |
| End-to-end latency | > SLA target | Review windowing size and partition strategy |

## WAF Considerations

### Reliability
- Event Hubs provides geo-disaster recovery (Geo-DR) pairing for namespace failover.
- Stream Analytics supports availability zone-redundant deployment in supported regions (automatic, no extra config).
- Cosmos DB provides 99.999% SLA with multi-region writes enabled.

### Security
- Use managed identity for Stream Analytics to authenticate to Event Hubs and Cosmos DB — no secrets in config.
- Enable Private Endpoints for all services to keep traffic off the public internet.
- Cosmos DB: enable IP firewall rules; restrict access to the Stream Analytics subnet.

### Cost Optimization
- Stream Analytics: priced per Streaming Unit-hour (~$0.11/SU/hour). Scale SUs down during off-peak if workload permits.
- Event Hubs: priced per throughput unit-hour. Enable auto-inflate to avoid over-provisioning.
- Cosmos DB: use autoscale provisioned throughput for variable workloads; serverless for development/test.

## Related Resources

- [Azure Event Hubs overview](event-hubs-overview.md)
- [Azure Stream Analytics overview](stream-analytics-overview.md)
- [Azure Cosmos DB for high-throughput workloads](cosmos-db-for-high-throughput.md)
- [Event-driven architecture on Azure](event-driven-architecture-azure.md)

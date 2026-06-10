<!-- source_url: https://learn.microsoft.com/en-us/azure/cosmos-db/introduction -->
<!-- publication_date: 2026-02-05 -->
<!-- category: arch_center -->

# Azure Cosmos DB for High-Throughput Workloads

Azure Cosmos DB is a fully managed, globally distributed NoSQL and relational database service. It is designed for mission-critical applications that require low latency, high availability, and elastic scalability at any scale.

## Key Value Propositions

- **Single-digit millisecond latency** at the 99th percentile for reads and writes, globally
- **99.999% availability SLA** for multi-region accounts with multi-region writes
- **Elastic and instant scalability**: scale throughput and storage independently
- **Multiple consistency models**: five consistency levels from strong to eventual
- **Multi-API support**: NoSQL (SQL), MongoDB, Cassandra, Gremlin (graph), Table

## Core Concepts

### Request Units (RUs)

Throughput in Cosmos DB is measured in **Request Units per second (RU/s)**:
- 1 RU = cost to read a 1 KB item by its ID (point read)
- Write operations cost more (typically 5–7× a read)
- Complex queries cost more based on data scanned
- All operations (read, write, query, upsert, delete) are measured in RUs

RU consumption examples (approximate):
| Operation | RU cost |
|---|---|
| Point read (1 KB item) | 1 RU |
| Point write (1 KB item) | ~5 RU |
| Query (returns 10 items, 1 KB each) | 10–50 RU |
| Cross-partition query | Higher (avoid in hot paths) |

### Partitioning

Cosmos DB distributes data across logical and physical partitions:
- **Logical partition**: defined by partition key value; max 20 GB
- **Physical partition**: Azure-managed unit; serves ≤ 10,000 RU/s and ≤ 50 GB
- Data is automatically distributed across physical partitions based on partition key
- **Choose a partition key with high cardinality and even distribution** to avoid hot partitions

For fraud detection:
- Good partition keys: `accountId`, `customerId`, `transactionId`
- Avoid: `status` (low cardinality), `merchantCategory` (may create hot partitions)

### Throughput Modes

| Mode | Description | Best for |
|---|---|---|
| **Provisioned Throughput** | Fixed RU/s assigned to container or database | Predictable, steady workloads |
| **Autoscale Provisioned** | Scales RU/s automatically 10%–100% of max | Variable workloads with spikes |
| **Serverless** | Pay per RU consumed, no provisioning | Dev/test, irregular workloads |

Autoscale example: set max 10,000 RU/s; system scales between 1,000–10,000 RU/s automatically.

## Consistency Levels

Cosmos DB offers five consistency levels, ordered from strongest to weakest:

| Level | Description | Latency | Availability | Use case |
|---|---|---|---|---|
| **Strong** | Linearizability; reads always see latest committed write | Highest | Lower | Financial ledgers, inventory |
| **Bounded Staleness** | Reads lag writes by at most K versions or T time | High | High | Leader-board, near-real-time |
| **Session** (default) | Consistent within a client session | Low | High | Shopping cart, user profile |
| **Consistent Prefix** | Reads never see out-of-order writes | Low | Highest | Social feeds, IoT telemetry |
| **Eventual** | No ordering guarantees; highest performance | Lowest | Highest | Non-critical aggregation |

For fraud detection recommendation: **Session** consistency balances low latency with read-your-writes guarantees for per-account processing.

## High Availability

### Multi-Region Writes
- Enable writes to any region simultaneously (active-active)
- **99.999% SLA** for read and write availability
- Data replicated synchronously (strong) or asynchronously (other levels) across regions
- Conflict resolution: last-write-wins (LWW) or custom merge policy

### Automatic Failover
- Cosmos DB automatically fails over to the next priority region if the primary region is unavailable
- RTO: typically < 5 seconds for automatic failover
- Manual failover available for testing

### Availability Zones
- Within a region, data replicated across 3+ availability zones
- No extra cost for zone redundancy in supported regions

## Global Distribution

- Deploy to up to 25 Azure regions simultaneously
- Add or remove regions at any time without downtime
- Azure backbone network for inter-region replication (typically < 100 ms for most region pairs)
- Transparent to application: single endpoint, Cosmos DB handles routing

## Sizing for Fraud Detection (10K TPS)

Assumptions:
- Average transaction size: 2 KB
- Mix: 70% writes, 30% reads
- Write cost: 10 RU (2 KB × 5 RU/KB)
- Read cost: 2 RU (point read by transactionId)

Per-second RU calculation:
- 7,000 writes/s × 10 RU = 70,000 RU/s
- 3,000 reads/s × 2 RU = 6,000 RU/s
- **Total: ~76,000 RU/s**
- With 50% safety buffer: **provision 120,000 RU/s** (or autoscale max 150,000 RU/s)

For 100K TPS:
- 10× scale = ~760,000 RU/s required
- Use autoscale with max 1,000,000 RU/s
- Ensure partition key distributes load evenly across logical partitions

## Security

- **Data encryption**: at rest (AES-256, service-managed or CMK), in transit (TLS 1.2)
- **Authentication**: Microsoft Entra ID (RBAC) or resource tokens; no shared master keys in production
- **Network isolation**: Private Endpoints, VNet service endpoints, IP firewall
- **Audit logging**: diagnostic logs to Azure Monitor
- **PCI-DSS, HIPAA, ISO 27001, SOC 1/2/3**: Cosmos DB is certified for all major compliance frameworks

## Integration with Azure Services

- **Azure Stream Analytics**: native Cosmos DB output connector
- **Azure Functions**: Cosmos DB Change Feed trigger for event-driven processing
- **Azure Synapse Link**: zero-ETL analytical queries over operational data (HTAP)
- **Azure Cognitive Search / AI Search**: index Cosmos DB data for full-text search

## Change Feed

The Cosmos DB Change Feed is an ordered log of all inserts and updates to a container:
- Enables real-time downstream processing (e.g., alerting, denormalization, cache invalidation)
- Read via Azure Functions trigger (easiest) or Change Feed Processor library
- Does **not** include deletes by default (use soft delete pattern)
- Critical for fraud detection: trigger downstream alert workflows when a fraud signal is written

<!-- source_url: https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-about -->
<!-- publication_date: 2026-02-05 -->
<!-- category: arch_center -->

# Azure Event Hubs Overview

Azure Event Hubs is a fully managed, real-time data streaming platform that can ingest millions of events per second with low latency. The service supports Apache Kafka natively, allowing existing Kafka workloads to run without code modifications.

## Key Capabilities

The platform excels at handling high-throughput scenarios including IoT telemetry, application logging, clickstream analytics, and financial transaction processing. It offers flexible scaling from megabytes to terabytes and maintains data for up to 7 days (Standard tier) or 90 days (Premium/Dedicated tiers).

## Core Concepts

### Namespace
An Event Hubs namespace is a management container for one or more event hubs. It provides DNS-integrated network endpoint and access control, IP filtering, VNet service endpoint, and Private Link features.

### Event Hub (Topic)
An event hub is analogous to a Kafka topic. Each event hub contains one or more partitions.

### Partitions
The ordered sequence of events held within an event hub. Partitions are the unit of parallelism for consumers. Key facts:
- Standard: up to 32 partitions per event hub
- Premium: up to 100 partitions
- Dedicated: up to 1,024 partitions
- Partition count is set at creation time and **cannot be decreased** (can be increased for Premium/Dedicated)
- All events with the same partition key go to the same partition — critical for ordered processing

### Throughput Units (Standard) / Processing Units (Premium)
- **1 Throughput Unit (TU)** = 1 MB/s ingress, 2 MB/s egress, up to 1,000 events/second ingress
- Standard: 1–40 TUs per namespace (up to 100 with quota increase)
- Premium: 1–16 Processing Units (PUs) per namespace; 1 PU ≈ same as multiple TUs but with dedicated resources
- **Auto-inflate**: automatically scales TUs up to a configured max when throughput is exceeded

### Consumer Groups
A consumer group is a view (state/position/offset) of an event hub. Multiple consumer groups allow multiple consuming applications to each read the event stream independently, at their own pace.
- Standard: up to 20 consumer groups per event hub
- Premium: up to 100 consumer groups

### Retention
- Basic: 1 day
- Standard: 1–7 days (default 1 day)
- Premium: 1–90 days
- Dedicated: 1–90 days

## Tiers Comparison

| Feature | Basic | Standard | Premium | Dedicated |
|---|---|---|---|---|
| Max TUs/PUs per namespace | 100 TU | 100 TU | 16 PU | N/A (reserved capacity) |
| Max partitions per event hub | 32 | 32 | 100 | 1,024 |
| Consumer groups per event hub | 1 | 20 | 100 | 1,000 |
| Brokered connections | 100 | 1,000 | 10,000 | 100,000 |
| Message retention (max) | 1 day | 7 days | 90 days | 90 days |
| Capture to Blob/ADLS | No | Yes | Yes | Yes |
| Schema Registry | No | Yes | Yes | Yes |
| Private Link | No | Yes | Yes | Yes |
| SLA | 99.95% | 99.95% | 99.99% | 99.99% |

## Sizing for Fraud Detection (10K TPS)

For a fraud detection platform processing 10,000 transactions per second:
- Assume average event size of 512 bytes: 10,000 × 512 B = ~5 MB/s ingress
- 1 TU = 1 MB/s ingress → need **5 TUs minimum** for ingress alone
- For safe headroom (50% buffer): **10 TUs**
- Recommended: Standard tier with auto-inflate enabled, max 20 TUs
- Partitions: set to 32 (Standard max) to maximize consumer parallelism

For 100K TPS with 512-byte events:
- ~50 MB/s ingress → 50+ TUs required → **Premium tier** recommended
- Premium PUs provide dedicated compute, predictable latency
- Partitions: use Premium's 100-partition maximum

## Enterprise Features

### Security
- **Authentication**: Microsoft Entra ID (RBAC) or Shared Access Signatures (SAS)
- **Network isolation**: Private Link, VNet service endpoints, IP firewall
- **Encryption**: at-rest (service-managed or customer-managed keys), in-transit (TLS 1.2+)

### High Availability
- **Zone redundancy**: automatically distributes replicas across availability zones in supported regions (Standard and above)
- **Geo-DR**: namespace-level pairing for cross-region failover; RPO = 0 for metadata; data in-flight may be lost
- **Geo-replication** (Premium/Dedicated): active-active replication of event data across regions

### Integration
- Apache Kafka protocol support (no code changes for Kafka producers/consumers)
- Native connectors: Azure Stream Analytics, Azure Functions, Azure Data Explorer, Synapse Analytics
- Event Hubs Capture: automatically deliver streaming data to Azure Blob Storage or Azure Data Lake Storage Gen2

## SLA

| Tier | SLA |
|---|---|
| Basic / Standard | 99.95% monthly uptime |
| Premium | 99.99% monthly uptime |
| Dedicated | 99.99% monthly uptime |

SLA applies to sending and receiving events. Does not cover data loss due to customer misconfiguration.

<!-- source_url: https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/event-driven -->
<!-- publication_date: 2026-01-15 -->
<!-- category: arch_center -->

# Event-Driven Architecture on Azure

An event-driven architecture consists of **event producers** that generate a stream of events, and **event consumers** that listen for the events. Events are delivered in near real time, so consumers can respond immediately as events occur.

Event-driven architectures are central to fraud detection, IoT platforms, financial transaction processing, and any system where something has happened and downstream components must react.

## Architecture Overview

```
Producers → Event Router / Message Broker → Consumers
```

Components:
- **Event producers**: generate events (applications, IoT devices, user interactions, database change feeds)
- **Event router**: ingests, filters, and routes events to consumers (Event Hubs, Event Grid, Service Bus)
- **Event consumers**: process events and take action (Azure Functions, Stream Analytics, microservices, Azure Logic Apps)

## Event vs Message

| Concept | Description | Azure Service |
|---|---|---|
| **Event** | Notification that something happened; lightweight, no expectation of action | Event Hubs, Event Grid |
| **Message** | Data sent for processing; producer expects consumer to act on it | Service Bus |

Use events for telemetry, streaming, and pub/sub fan-out. Use messages for reliable command dispatch and ordered workflows.

## Azure Services for Event-Driven Patterns

### Azure Event Hubs — High-Throughput Streaming

Best for: high-volume event ingestion (millions of events/second), streaming analytics, log aggregation

- Partitioned consumer model (like Apache Kafka)
- Multiple consumer groups allow independent downstream processing
- Retention: 1–90 days (tier-dependent)
- Native Kafka protocol support
- **Use for fraud detection**: ingest transaction and account events, feed Stream Analytics and ML pipelines

### Azure Event Grid — Reactive Event Routing

Best for: serverless event fan-out, resource lifecycle events, webhook delivery

- Push-based delivery to Azure services and custom webhooks
- Filtering by event type and subject
- At-least-once delivery with retry policy
- **Use for fraud detection**: route high-confidence fraud alerts to notification services, case management APIs

### Azure Service Bus — Reliable Messaging

Best for: enterprise messaging, decoupling microservices, guaranteed delivery, ordered processing

- Topics (pub/sub) and queues (point-to-point)
- Message sessions for ordered processing
- Dead-letter queue for poison messages
- **Use for fraud detection**: reliable command dispatch (e.g., block account, initiate review workflow)

## Design Patterns

### Competing Consumers
Multiple consumer instances read from the same event stream partition and divide work. Used by Stream Analytics and Azure Functions with Event Hubs trigger.

### Event Sourcing
The state of an entity is derived from a sequence of events rather than a current-state snapshot. All changes are persisted as immutable events. Enables full audit trail — critical for PCI-DSS compliance in fraud detection.

### CQRS (Command Query Responsibility Segregation)
Separate the read and write models. Writes go to an event store; reads come from a materialized view updated by a consumer. Enables high-write throughput without read bottlenecks.

### Outbox Pattern
Guarantee that a database write and an event publication happen atomically using the database's change feed (e.g., Cosmos DB Change Feed). Prevents dual-write inconsistencies.

### Dead-Letter Queue
Route events that fail processing after N retries to a dead-letter queue for inspection and replay. Essential for production fraud detection pipelines.

## When to Use Event-Driven Architecture

✅ High-volume, real-time data ingestion (IoT, clickstreams, financial transactions)  
✅ Loose coupling between microservices (services don't call each other directly)  
✅ Fan-out processing (same event consumed by multiple independent pipelines)  
✅ Temporal decoupling (producer and consumer don't need to be available simultaneously)  
✅ Audit trail requirements (event sourcing)  

❌ Avoid when: you need synchronous request/response, strong transactional guarantees across multiple entities, or very simple workflows where event complexity is overhead

## Benefits

- **Scalability**: producers and consumers scale independently
- **Resilience**: consumer failures don't block producers; events can be replayed
- **Extensibility**: add new consumers without modifying producers
- **Real-time**: sub-second event delivery enables immediate action on fraud signals

## Challenges

- **Eventual consistency**: consumers process events at different speeds; avoid assumptions about real-time state
- **Event ordering**: out-of-order events can occur across partitions; use partition keys to guarantee per-entity ordering
- **Debugging complexity**: distributed tracing (correlation IDs) required to trace an event across systems
- **Schema evolution**: producers and consumers must agree on event schema; use a Schema Registry

## Fraud Detection Reference Pattern

```
Transaction Service → Event Hubs (partitioned by accountId)
                   → Stream Analytics (velocity, geo, amount anomalies) → Cosmos DB (fraud signals)
                   → Azure Functions (real-time rule engine)             → Service Bus (block commands)
                   → ML Scoring Service (real-time inference)            → Event Grid (alert fan-out)
```

Key design decisions:
1. Partition by `accountId` to ensure all events for an account go to the same partition — enables stateful per-account processing
2. Use Event Hubs consumer groups: one for Stream Analytics, one for Functions, one for ML scoring — independent processing of the same stream
3. Use Cosmos DB Change Feed to trigger downstream workflows when fraud signals are written
4. Use Service Bus for reliable command dispatch (block account, flag for review) — guaranteed delivery, ordered processing per account session

## Related Architecture References

- [Real-time streaming with Stream Analytics](real-time-streaming-reference-architecture.md)
- [Event Hubs overview](event-hubs-overview.md)
- [Azure Cosmos DB for high-throughput workloads](cosmos-db-for-high-throughput.md)

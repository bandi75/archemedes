<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/service-guides/event-hubs -->
<!-- publication_date: 2025-10-01 -->
<!-- category: waf -->

# Azure Well-Architected Framework — Event Hubs Service Guide

This guide provides pillar-by-pillar WAF recommendations for Azure Event Hubs. Use it when Event Hubs is part of your architecture (e.g., real-time fraud detection, IoT ingestion, telemetry pipelines).

---

## Reliability

### Design Recommendations

**1. Use zone-redundant namespaces**
- Standard, Premium, and Dedicated tiers support availability zone redundancy automatically in supported regions
- Zone redundancy distributes Event Hubs brokers across 3 availability zones with no extra cost or configuration
- Verify the target region supports zones before selecting it (East US: supported)

**2. Enable Geo-Disaster Recovery (Geo-DR)**
- Configure a Geo-DR pairing between a primary and secondary namespace
- Geo-DR replicates namespace **metadata** (event hubs, consumer groups, authorization rules) to the secondary
- Data (events already ingested) is NOT replicated — for data replication, use Geo-replication (Premium/Dedicated)
- Initiate failover via the primary namespace; DNS CNAME switches to secondary; consumers reconnect
- RPO for metadata: near-zero; RPO for events: depends on retention

**3. Use Geo-replication for data-level protection (Premium/Dedicated)**
- Geo-replication replicates event data (not just metadata) to the secondary region
- Enables active-active reads from both regions
- Available only on Premium and Dedicated tiers
- Required for 99.99% SLA on both ingestion and consumption paths

**4. Set appropriate retention**
- Minimum retention: enough to recover from a downstream outage (consumer down for 24 h → need 24 h retention minimum)
- For fraud detection: set 7-day retention (Standard) to handle weekend outages without data loss
- Consumer group offsets are maintained by consumers (in Cosmos DB, Azure Storage, or Event Hubs SDK) — ensure offset storage is also highly available

**5. Implement consumer checkpointing**
- Consumers must checkpoint their offset (last processed event position) to durable storage
- Loss of checkpoint means reprocessing from last checkpoint, not from start (if retention allows)
- Use Azure Blob Storage for checkpoint storage in Event Processor Host or the Azure SDK EventProcessorClient

### Reliability Anti-Patterns
- ❌ Single namespace with no Geo-DR — single region failure takes down ingestion
- ❌ Retention shorter than downstream consumer recovery time — causes data loss after consumer outage
- ❌ No consumer group isolation — multiple consumers sharing one consumer group will miss events

---

## Security

### Design Recommendations

**1. Use managed identity for authentication**
- Prefer Entra ID RBAC over Shared Access Signatures (SAS) for service-to-service auth
- Assign `Azure Event Hubs Data Sender` to producer managed identities
- Assign `Azure Event Hubs Data Receiver` to consumer managed identities (ASA, Functions, AKS pods)
- Never embed SAS keys in code; if SAS is required, use short-lived keys stored in Key Vault

**2. Disable public network access**
- Enable private endpoints for Event Hubs in your VNet
- Set `publicNetworkAccess: Disabled` on the namespace after private endpoints are configured
- Use private DNS zone `privatelink.servicebus.windows.net` for name resolution

**3. Enable IP firewall for allowed ranges (if private endpoints not feasible)**
- Restrict ingress to known IP ranges or service tags
- Use VNet service endpoints as an intermediate option before full private endpoint migration

**4. Use customer-managed keys (PCI-DSS scope)**
- For PCI-DSS environments, configure CMK encryption for Event Hubs using Azure Key Vault
- Requires Premium or Dedicated tier
- Key Vault must have soft-delete and purge protection enabled

**5. Enable diagnostic logging**
- Enable `OperationalLogs`, `ArchiveLogs`, `AutoScaleLogs`, `KafkaCoordinatorLogs` diagnostic categories
- Route to Log Analytics for alerting and retention; route to Storage for long-term archival

### Security Anti-Patterns
- ❌ Using root namespace connection string — grants full admin access; use scoped SAS or managed identity
- ❌ Disabling TLS or allowing TLS < 1.2 — not permitted in PCI-DSS environments
- ❌ Public endpoint open to all IPs — unnecessary attack surface

---

## Cost Optimization

### Design Recommendations

**1. Right-size throughput units**
- 1 TU = 1 MB/s ingress, 2 MB/s egress
- Monitor `IncomingBytes` and `OutgoingBytes` metrics to measure actual throughput
- Start with minimum TUs; enable auto-inflate with a maximum that covers peak + 20% buffer

**2. Choose the right tier**
- Basic: only for very low volume (< 100 events/s), no consumer groups
- Standard: right for most production workloads up to ~50 MB/s; auto-inflate scales to 100 TUs
- Premium: required > 100 TUs, > 32 partitions, > 7-day retention, or when dedicated compute is needed
- Dedicated: only for very large organizations needing > 200 MB/s with fully isolated compute

**3. Archive with Capture**
- Event Hubs Capture writes events to Azure Blob Storage or ADLS Gen2 at low cost
- Cheaper than long retention within Event Hubs itself
- Enables batch analytics on historical events without re-reading from the live stream

**4. Delete unused consumer groups**
- Consumer groups have no direct cost, but they hold state (offsets); orphaned consumer groups cause confusion

### Cost Optimization Anti-Patterns
- ❌ Provisioning Premium tier when Standard + auto-inflate would suffice
- ❌ Long retention (90 days) without Capture — paying for hot storage when cold storage would do
- ❌ Using Dedicated tier for dev/test — pay per cluster regardless of usage

---

## Operational Excellence

### Design Recommendations

**1. Monitor key metrics**

| Metric | Alert Threshold | Action |
|---|---|---|
| `ThrottledRequests` | > 0 sustained | Increase TUs or enable auto-inflate |
| `IncomingMessages` | Drop to 0 for > 5 min | Check producer health |
| `OutgoingMessages` | Drop to 0 for > 5 min | Check consumer health |
| `ActiveConnections` | Near connection limit for tier | Check for connection leaks |
| `CaptureBacklog` | Growing | Capture not keeping up — check Capture config |
| `ConsumerLag` | Growing beyond threshold | Consumer falling behind; scale consumer |

**2. Set up Geo-DR failover runbook**
- Document the failover procedure: initiate via portal or CLI, verify DNS propagation, verify consumers reconnect
- Practice failover in staging environment at least quarterly
- Automate health checks that trigger an alert when primary region is unreachable

**3. Use Infrastructure as Code**
- Provision Event Hubs namespaces, event hubs, consumer groups, and auth rules via Bicep or Terraform
- Never configure auth rules manually in the portal — they will drift from IaC state

**4. Tag resources for cost attribution**
- Tag namespaces with `workload`, `environment`, `component`, `cost-center`

### Operational Anti-Patterns
- ❌ No consumer lag monitoring — consumer falling behind is a silent failure
- ❌ Manual Geo-DR failover with no runbook — during an incident, no one knows the steps

---

## Performance Efficiency

### Design Recommendations

**1. Maximize partition parallelism**
- Set partition count to at least equal to the number of consumer instances you plan to run
- Rule of thumb: partitions ≥ max expected concurrent consumers per consumer group
- For fraud detection at 10K TPS: 32 partitions (Standard max) allows up to 32 parallel consumers per consumer group

**2. Use batch publishing**
- Send events in batches (EventDataBatch) rather than one at a time
- Batch publishing dramatically improves throughput and reduces per-event overhead
- Max batch size: 1 MB (Standard/Premium); set to leave headroom for metadata

**3. Choose partition key carefully**
- Good partition key: `accountId` or `customerId` — high cardinality, even distribution
- Ensures all events for an account go to the same partition (enables stateful per-account processing)
- Avoid `eventType` (low cardinality → hot partitions) or random key (no ordering guarantee per entity)

**4. Monitor and act on throughput limits**
- Monitor `IncomingBytes` vs TU capacity; alert when consistently > 70% of TU capacity
- Enable auto-inflate before hitting limits — once throttled, events are rejected (not buffered)

### Performance Anti-Patterns
- ❌ Low partition count (e.g., 4) for a 100K TPS workload — limits consumer parallelism and throughput
- ❌ Sending events one at a time — 10–100× worse throughput than batching
- ❌ All events sharing the same partition key — one hot partition, all others idle

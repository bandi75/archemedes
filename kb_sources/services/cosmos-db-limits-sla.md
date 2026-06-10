<!-- source_url: https://learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits -->
<!-- publication_date: 2026-02-05 -->
<!-- category: services -->

# Azure Cosmos DB — Service Limits and SLA

## SLA

| Configuration | Read Availability SLA | Write Availability SLA |
|---|---|---|
| Single region, single write region | 99.99% | 99.99% |
| Multi-region, single write region | 99.999% | 99.99% |
| Multi-region, multi write regions (active-active) | 99.999% | 99.999% |

99.999% = up to 26.3 seconds downtime/month  
99.99% = up to 4.4 minutes downtime/month

Also covered by SLA:
- Latency: < 10 ms for reads at P99; < 15 ms for writes at P99 (single region)
- Throughput: guaranteed to deliver provisioned RU/s (no throttling if within provisioned capacity)
- Consistency: guaranteed to deliver the selected consistency level

---

## Account and Resource Limits

| Resource | Limit |
|---|---|
| Maximum Azure Cosmos DB accounts per Azure subscription | 50 (soft limit; can be increased) |
| Maximum databases per account | Unlimited |
| Maximum containers per database | Unlimited |
| Maximum shared throughput databases per account | 5 (can be increased) |
| Maximum regions per account | 25 |
| Maximum items per logical partition | Unlimited |
| Maximum logical partition size | 20 GB |
| Maximum item size | 2 MB |
| Maximum item property name length | 255 characters |
| Maximum levels of nesting in an item | 128 |

---

## Throughput Limits

### Provisioned Throughput

| Limit | Value |
|---|---|
| Minimum RU/s per container | 400 RU/s (100 RU/s with shared throughput) |
| Maximum RU/s per container | 1,000,000 RU/s (higher with quota increase) |
| Maximum RU/s per physical partition | 10,000 RU/s |
| Maximum storage per physical partition | 50 GB |
| Minimum RU/s for autoscale | 10% of max provisioned RU/s |

### Serverless

| Limit | Value |
|---|---|
| Maximum containers per serverless account | 25 |
| Maximum storage per container | 1 TB |
| Maximum RU/s burst | 5,000 RU/s per container |
| Maximum item size | 2 MB |

### Autoscale

| Limit | Value |
|---|---|
| Minimum autoscale max RU/s | 1,000 RU/s |
| Maximum autoscale max RU/s | 1,000,000 RU/s |
| Scale range | 10%–100% of max RU/s (automatic) |

---

## Request Unit (RU) Reference

| Operation | Approximate RU Cost |
|---|---|
| Point read (1 KB item, by ID + partition key) | 1 RU |
| Point write (1 KB item) | 5–7 RU |
| Point write (2 KB item) | 9–12 RU |
| Upsert (1 KB item, new) | 6–8 RU |
| Delete (1 KB item) | 5–7 RU |
| Query (returns 1 item, 1 KB) | 1–10 RU |
| Query (cross-partition, returns 100 items) | 100–500+ RU |
| Stored procedure (small) | 10–50 RU |

RU cost scales approximately linearly with item size for writes.

---

## Partitioning Limits

| Limit | Value |
|---|---|
| Maximum logical partitions per container | Unlimited |
| Maximum size per logical partition | 20 GB |
| Maximum RU/s per physical partition | 10,000 RU/s |
| Maximum storage per physical partition | 50 GB |

**Key insight**: Cosmos DB automatically splits physical partitions when either the 10,000 RU/s or 50 GB limit is reached. Choose a partition key that distributes both load and data evenly to avoid hotspots.

---

## Indexing

| Limit | Value |
|---|---|
| Maximum index size per item | 2 KB (approximate) |
| Maximum number of paths in an indexing policy | 100 |
| Maximum path length | 512 characters |

---

## Consistency Levels and Latency Guarantees

| Consistency Level | Read Latency (P99) | Write Latency (P99) | Availability |
|---|---|---|---|
| Strong | < 10 ms | < 15 ms | Lower (synchronous replication) |
| Bounded Staleness | < 10 ms | < 15 ms | High |
| Session (default) | < 10 ms | < 15 ms | High |
| Consistent Prefix | < 10 ms | < 15 ms | Highest |
| Eventual | < 10 ms | < 15 ms | Highest |

Latency SLA applies within a single region. Cross-region latency depends on physical distance.

---

## Global Distribution

| Limit | Value |
|---|---|
| Maximum regions per account | 25 |
| Add/remove region | Zero downtime |
| Automatic failover | Yes (configurable priority list) |
| Manual failover | Yes (for testing) |
| Typical RTO for automatic failover | < 30 seconds |
| Geo-redundant backup | Optional; point-in-time restore up to 30 days |

---

## Change Feed

| Limit | Value |
|---|---|
| Maximum change feed throughput | Bound by provisioned RU/s on the container |
| Change feed lease container required | Yes (for Change Feed Processor pattern) |
| Change feed retention | Same as container retention |
| Change feed includes deletes | No (use soft-delete pattern) |

---

## Storage Limits

| Limit | Value |
|---|---|
| Maximum storage per account | Unlimited (distributed across regions and partitions) |
| Maximum storage per container | Unlimited (partitions are auto-split) |
| Storage pricing | Per GB-month (Standard: ~$0.25/GB in East US) |
| Included storage with throughput | 1 GB per 100 RU/s provisioned |

---

## Backup and Restore

| Feature | Periodic Backup (Default) | Continuous Backup |
|---|---|---|
| Backup frequency | Every 1–24 hours (configurable) | Continuous |
| Backup retention | 2 backups kept | 30 days |
| Point-in-time restore | No | Yes |
| Cost | Included | Additional cost |

---

## Fraud Detection Sizing Example

**Scenario**: 10K transactions/second, 2 KB average size, 70% writes / 30% reads

RU calculation:
- 7,000 writes/s × 10 RU (2 KB write) = 70,000 RU/s
- 3,000 reads/s × 2 RU (point read by `transactionId`) = 6,000 RU/s
- Total: **76,000 RU/s**
- Recommended autoscale max: **100,000 RU/s** (includes 30% headroom)
- At $0.016/hour per 100 RU/s (autoscale): $0.016 × 1,000 × 24 × 30 = **~$11,520/month** for throughput alone

For 100K TPS:
- ~760,000 RU/s required
- Recommended autoscale max: **1,000,000 RU/s**
- Estimated cost: ~$115,200/month for throughput

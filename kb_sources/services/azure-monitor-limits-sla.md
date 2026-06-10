<!-- source_url: https://learn.microsoft.com/en-us/azure/azure-monitor/service-limits -->
<!-- publication_date: 2026-01-01 -->
<!-- category: services -->

# Azure Monitor — Service Limits and SLA

## SLA

| Component | SLA |
|---|---|
| Log Analytics (query and ingestion) | 99.9% monthly uptime |
| Application Insights | 99.9% monthly uptime |
| Azure Monitor Metrics | 99.9% monthly uptime |
| Alert Rules | 99.9% monthly uptime |

99.9% = up to 43.8 minutes downtime/month

---

## Log Analytics Workspace Limits

### Ingestion Limits

| Limit | Value |
|---|---|
| Default daily ingestion cap | 500 MB–1 GB per workspace (set by user; no hard default cap) |
| Maximum ingestion rate | 500 MB/min per workspace |
| Maximum event size | 32 KB per event |
| Maximum field value size | 32 KB |
| Maximum fields per event type | 500 fields |
| Maximum field name length | 500 characters |
| Ingestion lag | Typically < 3 minutes (data available for query) |

**Note**: There is no default daily cap on Log Analytics ingestion — you configure the cap as a cost control measure. Without a cap, ingestion is limited only by rate limits and billing.

### Storage and Retention

| Limit | Value |
|---|---|
| Interactive retention (default) | 30 days |
| Interactive retention (maximum) | 730 days (2 years) |
| Archive retention (after interactive period) | 7 years maximum |
| Data restore from archive | Supported (restore up to 14 days at a time) |
| Free tier retention | 7 days |

### Query Limits

| Limit | Value |
|---|---|
| Maximum time range for query | 30 days per query (standard); up to 7 years with archive access |
| Maximum query execution time | 10 minutes |
| Maximum query result size | 64 MB |
| Maximum concurrent queries per workspace | 40 |
| Maximum rows per query result | 500,000 |
| Cross-workspace query | Yes (up to 100 workspaces per query) |
| Query throttling | Triggered when concurrent queries exceed limits |

---

## Azure Monitor Metrics Limits

| Limit | Value |
|---|---|
| Metric retention (standard granularity) | 93 days |
| Metric retention (minute granularity) | 93 days |
| Metric retention (raw/1-second) | 93 days |
| Maximum custom metric dimensions | 10 per metric |
| Maximum custom metric name length | 256 characters |
| Maximum time series per resource | 10,000 |
| Metric ingestion lag | < 5 minutes for most platform metrics |

**Platform metrics** for Azure services (Event Hubs, Cosmos DB, AKS, etc.) are collected automatically at no charge. Custom metrics (sent via SDK or API) are charged per million data points.

---

## Alert Rules Limits

| Limit | Value |
|---|---|
| Maximum alert rules per subscription | 5,000 |
| Maximum alert rules per resource group | 800 |
| Maximum action groups per subscription | 2,000 |
| Maximum actions per action group | 10 of each type (email, SMS, webhook, etc.) |
| Alert rule evaluation frequency | 1 minute (minimum) |
| Maximum look-back period for alert queries | 14 days (Log Analytics query alerts) |
| Maximum dimension combinations per metric alert | 10,000 |

---

## Application Insights Limits

| Limit | Value |
|---|---|
| Maximum data ingestion rate | 32,000 events/second per instrumentation key |
| Daily data cap (configurable) | 100 GB/day (default cap for cost control) |
| Daily free data grant | 5 GB/day per billing account |
| Data retention (default) | 90 days (workspace-based) |
| Data retention (maximum) | 730 days |
| Maximum custom event name length | 512 characters |
| Maximum custom dimension count | 10 per event |
| Sampling | Adaptive (automatic) or fixed-rate (configurable) |

---

## Diagnostic Settings Limits

| Limit | Value |
|---|---|
| Maximum diagnostic settings per resource | 5 |
| Maximum destinations per diagnostic setting | 1 Log Analytics workspace + 1 Storage account + 1 Event Hub (can combine) |
| Ingestion latency (to Log Analytics) | < 3 minutes typically; up to 30 minutes in some cases |

---

## Key Metrics for Fraud Detection Architecture

### Event Hubs Metrics to Monitor

| Metric | Alert Condition | Action |
|---|---|---|
| `ThrottledRequests` | > 0 for sustained 5 minutes | Increase TUs or enable auto-inflate |
| `IncomingMessages` | Drop > 50% vs baseline | Investigate producer health |
| `ActiveConnections` | > 80% of tier limit | Check for connection leaks |

### Cosmos DB Metrics to Monitor

| Metric | Alert Condition | Action |
|---|---|---|
| `NormalizedRUConsumption` | > 80% sustained | Increase provisioned RU/s |
| `TotalRequestUnits` | Unexpected spike | Investigate hot partition or query explosion |
| `ServerSideLatency` | P99 > 10 ms | Investigate query patterns, missing indexes |
| `MongoRequestsCount` (if MongoDB API) | N/A | Monitor for unexpected operations |

### AKS Metrics to Monitor

| Metric | Alert Condition | Action |
|---|---|---|
| `kube_node_status_condition` (NotReady) | Any node NotReady > 5 min | Investigate node health |
| `kube_pod_status_phase` (Failed) | Any critical pod Failed | Check pod logs |
| Node CPU utilization | > 80% sustained | Scale out node pool |
| Node memory utilization | > 80% sustained | Scale out or right-size VMs |

### Stream Analytics Metrics to Monitor

| Metric | Alert Condition | Action |
|---|---|---|
| `SU (%)` | > 80% sustained | Add SUs |
| `WatermarkDelaySeconds` | Growing over time | Job cannot keep up; add SUs or optimize query |
| `DroppedOrAdjustedEvents` | > 0 | Investigate event format or policy issues |

---

## Pricing Summary

| Component | Pricing Model | Approximate Cost |
|---|---|---|
| Log Analytics ingestion | Per GB | $2.30/GB (East US) |
| Log Analytics retention (> 30 days) | Per GB/month | $0.10/GB/month |
| Log Analytics archive (> 730 days) | Per GB/month | $0.025/GB/month |
| Platform metrics | Free | — |
| Custom metrics | Per million data points | $0.10/million |
| Alert rules (multi-dimension metric) | Per rule/month | $0.10/rule/month |
| Alert rules (Log Analytics query) | Per rule/month | $1.50/rule/month |
| Application Insights (workspace-based) | Per GB (shares workspace pricing) | $2.30/GB |

### Fraud Detection Monitoring Cost Estimate

Assume 50 GB/day Log Analytics ingestion (platform logs, diagnostic logs, custom telemetry):
- 50 GB × $2.30 × 30 days = **$3,450/month** (ingestion)
- Plus retention beyond 30 days: 50 GB × 30 × $0.10 = **$150/month**
- 100 alert rules: ~$150/month
- Total: **~$3,750/month** for monitoring

Cost optimization tips:
- Use sampling on Application Insights (adaptive sampling at 10% for debug events)
- Route verbose diagnostic logs to Azure Storage (cheap) rather than Log Analytics (query-optimized but expensive)
- Set workspace daily cap at 150% of expected volume to prevent runaway costs during incidents

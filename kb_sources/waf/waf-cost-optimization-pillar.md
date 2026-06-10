<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/cost-optimization/overview -->
<!-- publication_date: 2025-11-01 -->
<!-- category: waf -->

# Azure Well-Architected Framework — Cost Optimization Pillar

The Cost Optimization pillar of the Azure Well-Architected Framework focuses on **maximizing the business value of your workload while minimizing waste**. Cost optimization is not about spending as little as possible — it is about spending the right amount to achieve your business goals.

## Design Principles

### 1. Develop Your Cost Management Discipline
- Assign an owner for cloud cost governance
- Define a cost budget per workload/environment
- Review cost reports weekly during development; monthly in production

### 2. Design with a Cost-Efficiency Mindset
- Start with the cheapest tier that meets requirements; scale up when proven necessary
- Prefer managed services over self-managed (they abstract operational overhead at a premium worth paying)
- Use the Azure Pricing Calculator before committing to an architecture

### 3. Optimize Over Time
- Track actual vs. expected spend continuously
- Use Azure Cost Management + Billing for visibility and alerts
- Right-size after observing actual usage (not hypothetical peaks)

### 4. Align Costs to Business Value
- Correlate cost to business metric (cost per transaction, cost per API call)
- Identify and eliminate idle resources
- Use tagging strategy to attribute costs to teams, features, or customers

## Cost Drivers in Fraud Detection Architectures

### Azure Event Hubs

| Tier | Pricing Model | Key Cost Drivers |
|---|---|---|
| Standard | Per TU-hour + per million events | TU-hours × hours/month; event count |
| Premium | Per PU-hour | PU-hours × hours/month (higher unit price, dedicated resources) |
| Dedicated | Reserved capacity (cluster-hour) | Fixed monthly cost regardless of usage |

**Cost optimization tips**:
- Enable auto-inflate for Standard tier to avoid over-provisioning TUs
- Use Event Hubs Capture to Archive to Blob (cheap) rather than keeping long retention in Event Hubs
- Dedicate a separate namespace for dev/test at lower tier

### Azure Stream Analytics

| Item | Pricing |
|---|---|
| Streaming Units (SU) | ~$0.11/SU/hour (East US) |

**Cost optimization tips**:
- Tune query parallelism: a fully parallelized job needs fewer SUs
- Turn off non-production jobs overnight (SU billing stops when job is stopped)
- Use the auto-scale feature to scale SUs based on load
- Start with the minimum SUs and scale up; monitor SU% metric

### Azure Cosmos DB

| Mode | Pricing Model | Best for |
|---|---|---|
| Provisioned Throughput | Per 100 RU/s per hour | Steady, predictable workloads |
| Autoscale | Per max 100 RU/s per hour (billed on peak reached) | Variable workloads with occasional spikes |
| Serverless | Per RU consumed | Low-throughput or dev/test |

**Cost optimization tips**:
- Use autoscale for production fraud detection (handles TPS spikes without over-provisioning)
- Monitor `NormalizedRUConsumption` — sustained < 50% means over-provisioned; reduce max RU/s
- Use Cosmos DB Synapse Link for analytics instead of separate ETL copies
- Delete TTL-expired documents to reduce storage costs

### Azure Kubernetes Service (AKS)

| Item | Pricing |
|---|---|
| Node VMs | Standard VM rates per node |
| System node pool | Min 1 node × VM cost always running |
| Control plane | Free (standard tier) or $0.10/hour (uptime SLA tier) |

**Cost optimization tips**:
- Use Cluster Autoscaler to scale node counts based on pod demand
- Use spot node pools for stateless, fault-tolerant workloads (up to 90% discount)
- Right-size nodes: use `kubectl top nodes` to find oversized VMs
- Use Azure Reserved VM Instances (1-year or 3-year) for baseline node capacity (up to 72% savings)
- Separate system pool (small, reliable) from user pool (scalable, spot-eligible)

### Azure Functions

| Plan | Pricing Model |
|---|---|
| Flex Consumption | Per execution + per GB-s memory used + always-ready instances |
| Premium | Per vCPU-s + per GB-s (pre-warmed instances) |
| Dedicated | Included in App Service Plan |

**Cost optimization tips**:
- Flex Consumption is cheapest for event-driven fraud signal processing at low-to-medium volume
- Premium plan justified only if cold starts are unacceptable and volume is high
- Set function timeout low to avoid runaway functions consuming RU budget

### Azure Monitor

| Item | Pricing |
|---|---|
| Log Analytics ingestion | Per GB ingested |
| Log Analytics retention | Free up to 31 days; per GB/month after |
| Metrics | Free for standard platform metrics |
| Application Insights | Per GB ingested (5 GB/month free) |

**Cost optimization tips**:
- Use diagnostic settings sampling (not all logs need 100% sampling)
- Route verbose debug logs to Storage (cheap archival) rather than Log Analytics (premium query)
- Set daily ingestion cap on non-production workspaces
- Use workspace-based Application Insights (shared workspace pricing) vs classic instances

## Cost Estimation: Fraud Detection at 10K TPS (East US, Monthly)

| Component | Configuration | Est. Monthly Cost |
|---|---|---|
| Event Hubs | Standard, 10 TU, ~24 h/day | ~$220 |
| Stream Analytics | 6 SUs × 24 h × 30 days | ~$475 |
| Cosmos DB | Autoscale max 150K RU/s, ~2 TB storage | ~$2,400 |
| AKS | 3× D4s_v5 nodes (system) + 6× D8s_v5 (user) | ~$2,100 |
| Azure Functions | Flex Consumption, ~1M executions/day | ~$150 |
| Azure Monitor | ~50 GB/day ingestion | ~$750 |
| **Total (approximate)** | | **~$6,100/month** |

*Note: Highly approximate; actual costs depend on query complexity, data sizes, and region. Use Azure Pricing Calculator for accurate estimates.*

## Cost Estimation: Scale to 100K TPS (delta from 10K)

| Component | Change | Delta |
|---|---|---|
| Event Hubs | Upgrade to Premium, 8 PUs | +$1,800 |
| Stream Analytics | Scale from 6 to 60 SUs | +$4,750 |
| Cosmos DB | Scale max RU/s to 1,000K | +$13,600 |
| AKS | Double user node pool | +$2,100 |
| Azure Monitor | 5× log volume | +$3,000 |
| **Total increase** | | **~+$25,250/month** |

## Cost Governance

### Tagging Strategy
Tag all resources with:
- `environment`: prod / staging / dev
- `workload`: fraud-detection
- `component`: event-ingestion / stream-processing / state-store / api
- `cost-center`: team or business unit

### Budgets and Alerts
- Set Azure Cost Management budget alerts at 80% and 100% of monthly budget
- Configure anomaly alerts to catch unexpected spikes (e.g., accidental test load on production)

### Showback / Chargeback
- Use Cost Management views filtered by tag to generate per-team cost reports
- Review "cost per 1M transactions" monthly — this is your unit economics metric

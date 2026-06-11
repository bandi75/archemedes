<!-- source_url: https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale -->
<!-- publication_date: 2025-12-09 -->
<!-- category: services -->

# Azure Functions — Service Limits and SLA

## SLA

| Hosting Plan | SLA |
|---|---|
| Flex Consumption | 99.95% |
| Premium | 99.95% |
| Dedicated (App Service) | 99.95% |
| Container Apps | 99.95% |
| Consumption (legacy) | 99.95% |

SLA applies to function execution availability. Does not cover application bugs or user-induced errors.

---

## Hosting Plans Overview

| Plan | Billing | Cold Start | Max Scale-Out | VNet Support |
|---|---|---|---|---|
| **Flex Consumption** | Per execution + memory | Improved (configurable always-ready) | 1,000 instances | Yes |
| **Premium** | Per vCPU-s + GB-s | None (pre-warmed) | 100 (Windows), 20–100 (Linux) | Yes |
| **Dedicated** | App Service Plan rates | None (always-on) | Manual / App Service autoscale | Yes |
| **Container Apps** | Per consumption or dedicated | Depends on min replicas | 300–1,000 | Yes |
| **Consumption (legacy)** | Per execution | Yes | 200 (Windows), 100 (Linux) | Limited |

---

## Function Execution Limits

### Timeout Duration

| Plan | Default Timeout | Maximum Timeout |
|---|---|---|
| Flex Consumption | 30 minutes | Unlimited (unbounded, 60 min grace period on scale-in) |
| Premium | 30 minutes | Unlimited (unbounded, 60 min grace period on scale-in) |
| Dedicated | 30 minutes | Unlimited (requires Always On) |
| Container Apps | 30 minutes | Unlimited (depends on min replicas) |
| Consumption (legacy) | 5 minutes | 10 minutes |

**Note**: HTTP-triggered functions have a **hard maximum of 230 seconds** (3.8 min) to respond due to Azure Load Balancer idle timeout, regardless of function timeout setting. For longer processing, use Durable Functions or return a 202 Accepted with polling.

### Invocation Limits

| Limit | Value |
|---|---|
| Maximum request body size (HTTP trigger) | 100 MB |
| Maximum URL length (HTTP trigger) | 4 KB |
| Maximum request timeout (HTTP, all plans) | 230 seconds (Load Balancer limit) |
| Maximum outbound connections per instance | 600 (active); 1,200 (total) |
| Maximum concurrent executions per instance | Configurable (default: unbounded for most triggers) |

---

## Scale-Out Limits

| Plan | Max Instances | Scale Basis |
|---|---|---|
| Flex Consumption | 1,000 | Per-function scaling |
| Premium | 100 (Windows) / 20–100 (Linux) | Per-plan scaling |
| Dedicated | 10–30 (ASP); 100 (ASE) | Manual or autoscale |
| Container Apps | 300–1,000 | Event-driven |
| Consumption (legacy) | 200 (Windows) / 100 (Linux) | Event-driven |

**Flex Consumption per-function scaling**: Each function in the app scales independently based on its own trigger. HTTP triggers in an app scale together as a group. This is the most efficient scaling model for mixed workloads.

---

## Cold Start Behavior

| Plan | Cold Start Mitigation |
|---|---|
| Flex Consumption | Configurable always-ready instances; improved warm-up |
| Premium | Always-ready instances (perpetually warm); no cold starts |
| Dedicated | No cold start (runs continuously with Always On enabled) |
| Container Apps | Depends on min replicas; 0 min replicas = cold start possible |
| Consumption (legacy) | Cold start possible; reduced by pre-warmed placeholder instances |

---

## Storage Limits

| Resource | Limit |
|---|---|
| Maximum deployment package size (zip deploy) | 500 MB (code + dependencies) |
| Maximum temporary storage per instance | 500 MB (Consumption/Flex); 21–140 GB (Premium, depends on plan size) |
| Maximum content share size (Azure Files, Consumption) | 5 TB |

---

## Networking Limits

| Feature | Flex Consumption | Premium | Dedicated | Container Apps |
|---|---|---|---|---|
| VNet integration (outbound) | Yes | Yes | Yes | Yes |
| Private endpoints (inbound) | Yes | Yes | Yes | Yes |
| Inbound IP restrictions | Yes | Yes | Yes | Yes |

---

## Memory and Compute

### Flex Consumption
| Instance Size | Memory | vCPUs |
|---|---|---|
| 512 MB | 512 MB | ~0.5 vCPU |
| 2,048 MB | 2,048 MB | ~2 vCPU |
| 4,096 MB | 4,096 MB | ~4 vCPU |

### Premium Plan Sizes
| SKU | Memory | vCPUs |
|---|---|---|
| EP1 | 3.5 GB | 1 vCPU |
| EP2 | 7 GB | 2 vCPUs |
| EP3 | 14 GB | 4 vCPUs |

---

## Event Hubs Trigger Limits (Relevant for Fraud Detection)

| Limit | Value |
|---|---|
| Maximum batch size | 10,000 events per invocation (configurable) |
| Partition-level parallelism | 1 function instance per partition |
| Consumer group | 1 per function app (configurable) |
| Checkpoint storage | Azure Storage (required) |
| Scale-out max | Bounded by Event Hubs partition count |

**Important**: With Consumption/Flex plans, the maximum concurrent instances for an Event Hubs trigger is bounded by the number of partitions. For a 32-partition event hub, max 32 instances will process events simultaneously.

---

## Pricing Summary

### Flex Consumption
- Per execution: $0.20 per million executions (after free grant)
- Per GB-second: $0.000016 per GB-second
- Always-ready instances: $0.0648/GB-hour (memory size × hours)
- Free grant: 100,000 executions and 100,000 GB-seconds per month per subscription

### Premium (EP1)
- $0.173/hour per pre-warmed instance (Linux East US)
- Billed per second; minimum 1 always-ready instance

### Consumption (Legacy)
- $0.20 per million executions
- $0.000016 per GB-second

---

## Fraud Detection Use Case Sizing

### Rule Engine (Event-Driven)
- Pattern: Event Hubs trigger, process one event, write to Cosmos DB
- Execution time: ~50ms per event
- At 10K TPS: 10,000 executions/s × 0.05s × 0.5 GB = 250 GB-s/s → ~$0.004/second = ~$10,000/month
- **Recommendation**: Use Premium EP1 plan or Flex Consumption with 2,048 MB instances
- At 100K TPS: 100,000 executions/s → exceeds single function app limits; fan out across multiple apps or use AKS instead

### Anomaly Notification (Low Volume)
- Pattern: Cosmos DB Change Feed trigger, send alert when fraud signal written
- Execution time: ~200ms (includes call to notification API)
- Volume: ~100–1,000 alerts/minute
- **Recommendation**: Flex Consumption — very low cost for this trigger pattern (~$20/month)

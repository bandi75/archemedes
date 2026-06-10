<!-- source_url: https://learn.microsoft.com/en-us/azure/aks/quotas-skus-regions -->
<!-- publication_date: 2026-01-15 -->
<!-- category: services -->

# Azure Kubernetes Service (AKS) — Service Limits and SLA

## SLA

| Tier | Control Plane Uptime SLA |
|---|---|
| Free tier | No SLA (best-effort) |
| Standard tier (Uptime SLA) | 99.95% with availability zones; 99.9% without |
| Premium tier | 99.95% with availability zones |

Note: The SLA covers the **Kubernetes API server** (control plane) availability. Node availability depends on the underlying VM SLA (~99.9% for single VM, 99.95% for VMs across availability zones).

**Recommended for production**: Standard tier with availability zones = 99.95% SLA

---

## Cluster Limits

| Resource | Limit |
|---|---|
| Maximum clusters per subscription | 5,000 |
| Maximum nodes per cluster | 5,000 (Linux node pools) |
| Maximum nodes per cluster | 200 (Windows node pools) |
| Maximum node pools per cluster | 100 |
| Maximum nodes per node pool | 1,000 |
| Maximum pods per node (default) | 30 (Azure CNI legacy), 110 (kubenet / Azure CNI Overlay) |
| Maximum pods per node (configurable max) | 250 |
| Maximum pods per cluster | 300,000 |
| Maximum containers per pod | 40 |
| Maximum services per cluster | 10,000 |
| Maximum namespaces per cluster | No hard limit (recommend < 1,000 for management) |

---

## Node Pool Limits

| Resource | Limit |
|---|---|
| Minimum nodes per system node pool | 1 (highly available: 2 recommended) |
| Maximum nodes per node pool | 1,000 |
| Minimum nodes per user node pool | 0 (can scale to zero) |
| Maximum node pools per cluster | 100 |
| Availability zones supported | Yes (1, 2, or 3 zones per node pool) |
| Spot node pools | Yes (for user node pools only; not supported for system node pools) |
| Node pool OS | Linux (Ubuntu or Azure Linux) or Windows Server |

**For production fraud detection**: Use 3 availability zones per node pool to ensure pods survive a single zone failure.

---

## Pod and Container Limits

| Resource | Limit |
|---|---|
| Maximum pods per node | 110 (default); up to 250 with `--max-pods` configuration |
| Maximum containers per pod | 40 |
| Maximum init containers per pod | 20 |
| Maximum volumes per pod | 256 (Azure Disk limit per VM applies) |

---

## Networking Limits

| Resource | Limit |
|---|---|
| Maximum services of type LoadBalancer | Depends on subscription (default: 100 public IPs per region) |
| Maximum rules per Load Balancer | 512 per frontend |
| Maximum IPs per Load Balancer frontend | 600 (Standard SKU) |
| VNet CIDR range supported | /8 minimum, /12 recommended for large clusters |
| Subnet for nodes | /24 minimum recommended (256 IPs) |
| Maximum NICs per node | Depends on VM size (D8s_v5: 8 NICs) |

---

## VM Size Recommendations for Fraud Detection

| Use Case | Recommended VM SKU | vCPUs | RAM | Notes |
|---|---|---|---|---|
| System node pool | D4s_v5 | 4 | 16 GB | Dedicated to kube-system pods; 2–3 nodes across zones |
| Stream processing workloads | D8s_v5 | 8 | 32 GB | Balanced compute/memory for real-time processing |
| ML inference (if on AKS) | F16s_v2 | 16 | 32 GB | CPU-optimized for inference |
| Memory-intensive workloads | E8s_v5 | 8 | 64 GB | For in-memory state stores, large caches |
| GPU inference | NC6s_v3 | 6 | 112 GB + 1 GPU | For deep learning fraud models |

---

## Scaling Limits

### Horizontal Pod Autoscaler (HPA)
| Resource | Limit |
|---|---|
| Minimum replicas | 1 (recommended; 0 requires KEDA) |
| Maximum replicas | Bound by cluster node capacity |
| Scale up cooldown | Default: 15 seconds |
| Scale down cooldown | Default: 5 minutes |
| Metrics supported | CPU, memory (built-in); custom metrics via KEDA |

### Cluster Autoscaler
| Resource | Limit |
|---|---|
| Minimum nodes per pool | 0 (scale to zero supported) |
| Maximum nodes per pool | 1,000 |
| Scale up speed | New nodes typically available in 3–5 minutes |
| Scale down cooldown | Default: 10 minutes |

### KEDA (Kubernetes Event-Driven Autoscaling)
- Scales pods based on external metrics: Event Hubs consumer lag, Service Bus queue depth, custom metrics
- Supports scale-to-zero for event-driven workloads
- **Critical for fraud detection**: scale processing pods based on Event Hubs backlog size
- Supported scalers: Azure Event Hubs, Azure Service Bus, Azure Monitor, Prometheus, and 60+ others

---

## Storage Limits

| Resource | Limit |
|---|---|
| Maximum Azure Disks per node | Depends on VM size (D8s_v5: 16 data disks) |
| Maximum Azure Files shares mountable | No hard limit |
| Maximum persistent volume claims per cluster | No hard limit |
| Ephemeral disk size | Bounded by VM temp disk size |

---

## Kubernetes Version Support

| Policy | Details |
|---|---|
| Supported minor versions | N, N-1, N-2 (3 minor versions at any time) |
| Version support duration | ~12 months per minor version |
| End of support notification | 12 months advance notice |
| Auto-upgrade channels | `none`, `patch`, `stable`, `rapid`, `node-image` |

**Recommendation**: Use `stable` auto-upgrade channel for production to stay current and receive security patches automatically.

---

## Availability Zone Configuration

For fraud detection workloads requiring 99.95%+ availability:
```
System node pool: 3 nodes across 3 zones (1 per zone)
User node pool: min 3, max 30 nodes across 3 zones (Cluster Autoscaler enabled)
Pod topology spread: maxSkew: 1, topologyKey: topology.kubernetes.io/zone
Pod disruption budget: minAvailable: 1 for all critical deployments
```

---

## Key Quotas That Affect Scale

| Quota | Default | Increase Path |
|---|---|---|
| vCPU cores per region | 10 (new subscriptions) | Support request |
| Standard DSv5 vCPUs per region | 10 | Support request |
| Public IP addresses per region | 100 | Support request |
| Network interfaces per region | 1,000 | Support request |

**Important**: Request vCPU quota increases in your target region before starting AKS deployment for fraud detection — 10 vCPU default is insufficient for production clusters.

<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-event-hubs -->
<!-- publication_date: 2025-10-01 -->
<!-- category: waf -->

# Architecture Best Practices for Azure Event Hubs — Well-Architected Framework Service Guide

Azure Event Hubs is a real-time data streaming platform and event ingestion service that can receive and process millions of events per second. It provides a unified streaming platform with time-retention buffer, decoupling event producers from event consumers. Event Hubs natively integrates with Azure analytics services and supports multiple protocols including AMQP, Apache Kafka, and HTTPS.

---

## Reliability

The purpose of the Reliability pillar is to provide continued functionality by **building enough resilience and the ability to recover fast from failures**.

### Workload Design Checklist

- **Review quotas and limits that might restrict your design**: Analyze quotas and limits that affect architecture decisions. For large-scale scenarios, be aware of the partition limits associated with different service tiers as they differ significantly. Determine how many throughput units or processing units you need. These settings define message ingestion capacity and establish scaling boundaries. Keep payloads within the maximum message size for your chosen tier. Choose appropriate message retention periods that match the service tier and meet recovery and replay requirements. Plan your application architecture around consumer group limits for each namespace.

- **Anticipate potential failures through failure mode analysis**:

  | Failure | Mitigation |
  |---|---|
  | Namespace unavailable | Implement monitoring and alerting for early detection. Plan for cross-region failover capabilities. |
  | Partition unavailable | Design partition distribution strategies to prevent single points of failure. Implement retry logic with exponential backoff in producers and consumers. |
  | High message volumes exceed throughput limits | Plan for capacity scaling to handle traffic spikes. Implement client-side throttling protection by using circuit breaker patterns. |

- **Define reliability targets for event streaming workloads**: Set clear reliability targets to guide architecture decisions. Define SLOs that include message ingestion availability, consumer processing latency, and end-to-end delivery performance. Set availability targets that align with SLA guarantees of 99.95% for the Standard tier and 99.99% for the Dedicated tier.

- **Implement redundancy strategies to eliminate single points of failure**: Add multiple redundancy layers, including availability zones, geo-replication, and partition distribution. Enable zone-level redundancy in Premium and Dedicated tiers for automatic replication across availability zones with transparent failover within the same region. Use geo-replication for Dedicated tier namespaces to enable real-time asynchronous replication of events and metadata across multiple regions.

- **Design for reliable scaling to handle variable workloads**: Configure infrastructure scaling through auto-inflate in the Standard and Premium tiers. This feature automatically scales throughput units during traffic spikes. Use the Dedicated tier for predictable performance with reserved capacity. Plan partition scaling carefully because you can't decrease the partition count after creation.

- **Implement monitoring and alerting for reliability**: Configure Azure Monitor to collect metrics. Track message ingestion volume, throughput utilization, and consumer lag. Configure thresholds that align with SLOs and business impact severity.

- **Configure Event Hubs for self-preservation and graceful degradation**: Event Hubs doesn't include a built-in dead-letter queue. Implement custom patterns to handle poison messages, and use circuit breaker patterns to protect traffic during recovery scenarios. Isolate consumers by creating separate consumer groups with only one active receiver for each group. Enable the capture feature to provide durable storage for event replay and recovery scenarios.

- **Do reliability testing to validate resilience**: Test partition availability, consumer lag recovery, and throughput scaling under realistic streaming conditions. Run stress testing to validate performance under expected and peak traffic conditions. Test the solution's resilience with chaos engineering and by introducing intentional failures. Perform failover testing to verify geo-disaster recovery and zone redundancy capabilities.

- **Design disaster recovery strategy for business continuity**: Use geo-disaster recovery for Standard and Premium tiers or geo-replication for the Dedicated tier to provide regional failover capabilities. Define your recovery time objective (RTO) and recovery point objective (RPO) based on business requirements. Choose DR patterns, like active-passive for cost optimization or active-active for minimal RTO.

### Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Enable availability zone redundancy when you create a namespace by selecting an Azure region with availability zone support. | Provides automatic datacenter-level failover with minimal recovery time and no application changes. |
| Enable geo-replication for Dedicated tier namespaces to replicate events and metadata across multiple regions in real time. Configure primary and secondary regions with appropriate network connectivity and monitor replication lag metrics. | Enables regional failover capabilities and minimal data loss during regional outages. |
| Set up geo-disaster recovery pairing between primary and secondary namespaces, then configure an alias for the namespace pair. Update connection strings to use the alias for transparent failover capabilities. | Enables cross-region failover capability with transparent client failover. Ensures business continuity during regional outages. |
| Implement hash-based partition keys for event distribution and set the appropriate partition count during event hub creation. Monitor partition-level metrics for hotspot detection and load balancing validation. | Prevents partition hotspots and enables horizontal scaling through balanced load distribution across partitions. |
| Enable auto-inflate for Standard tier namespaces and set maximum throughput units based on peak load projections. Use the Premium tier for sustained high-throughput workloads that require predictable performance. | Prevents ingestion throttling through automatic capacity scaling and maintains consistent availability during load variations without manual intervention. |
| Configure Event Hubs alerts in Azure Monitor for consumer lag, throughput utilization, and throttling events. Set thresholds that align with SLOs. Enable alerts for connection and authentication failures, then create alert action groups for incident response. | Enables early problem detection, reduces incident response time, and provides capacity planning insights. |

---

## Security

The purpose of the Security pillar is to provide **confidentiality, integrity, and availability** guarantees to the workload.

### Workload Design Checklist

- **Establish a security baseline for Event Hubs workloads**: Review the Event Hubs security baseline that addresses key security domains. Apply Microsoft Cloud Security Benchmark controls for Event Hubs that cover encryption for data at rest and in transit, network isolation capabilities, and granular access control mechanisms.

- **Implement segmentation strategies to isolate Event Hubs resources and control access boundaries**: Use Microsoft Entra ID with RBAC to create logical access control boundaries. Set up network segmentation to isolate streaming traffic. Use virtual network integration and private connectivity options to prevent public internet exposure.

- **Set up identity and access management**: Use Microsoft Entra ID as the trusted identity provider for centralized authentication and authorization. Configure role-based authorization for granular access controls through SendOnly and ListenOnly policies. Use managed identities to remove credential management overhead for service-to-service communication patterns.

- **Add network security controls to protect Event Hubs traffic and connectivity**: Use private endpoints, service endpoints, and IP firewall rules to secure streaming traffic from unauthorized access. Configure private endpoints to eliminate internet exposure. Enable service endpoints to provide secure virtual network connectivity without public routing.

- **Configure data encryption for Event Hubs event streams and metadata**: Enable customer-managed keys for enhanced encryption control and regulatory compliance. Use double encryption for scenarios that need extra protection. Set TLS 1.2 as the minimum configuration for secure client connections and inter-service communication. Establish key rotation strategies with operational procedures for customer-managed keys.

- **Harden Event Hubs namespace and entity configurations to reduce attack surface**: Turn off auto-inflate when you don't need it for capacity management. Disable other unused features and protocols to remove potential attack vectors. Remove unused consumer groups and event hubs.

- **Secure Event Hubs connection strings and access keys through proper secret management**: Use managed identities as the preferred authentication method. When you must use connection strings or SAS tokens, store them securely and rotate them regularly. Store Event Hubs connection strings in Azure Key Vault. Deploy short-lived SAS tokens to reduce security exposure risk.

- **Implement security monitoring and logging**: Configure diagnostic logging to capture authentication events, data plane access patterns, and configuration changes. Monitor network access patterns to detect unauthorized access. Enable threat detection to alert you about suspicious activity including unusual access volumes or unknown sources.

### Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Use Microsoft Entra ID to authorize access to Event Hubs resources. Assign built-in roles including Data Owner, Data Sender, and Data Receiver at appropriate scope levels. Scope assignments at namespace, event hub, or consumer group levels for granular access control. | Provides granular access control across scopes and clearly separates producer, consumer, and administrative operations. |
| Deploy private endpoints within dedicated subnets for network isolation and configure NSGs to control traffic flow. Alternatively, apply IP firewall rules at the namespace level for known source networks. | Removes public internet exposure through private connectivity and aligns network-level traffic control with organizational security zones. |
| Enable Microsoft Entra ID authentication at the namespace level and disable SAS authentication where managed identities are available. Create conditional access policies that require compliant devices. | Namespace-level enablement centralizes authentication configuration across Event Hubs entities. Disabling SAS removes shared credential management overhead. |
| Set the minimum TLS version to 1.2 at the namespace scope to block older, vulnerable protocols. Enable diagnostic logging and query for TLS version violations in Log Analytics to identify non-compliant clients. | TLS 1.2 prevents the exploitation of legacy SSL or TLS vulnerabilities that can compromise data in transit. |
| Create an RSA 2048 key in Key Vault and assign the Key Vault Crypto Service Encryption User role to the namespace managed identity. Configure the namespace to use a customer-managed key and set a 90-day rotation policy in Key Vault. Enable double encryption when you create a namespace because you can't add this capability later. | CMK configuration provides regulatory compliance for data sovereignty requirements. The 90-day rotation policy balances security with operational stability. Double encryption at creation time provides an extra layer of protection from the start. |
| Store connection strings in Key Vault with a 90-day expiration date set. If you need SAS tokens, generate entity-level tokens with a one-hour expiry time and use Send or Listen permissions only. | 90-day expiration enforces regular credential rotation. One-hour SAS token expiry limits the credential exposure window. Send/Listen-only permissions reduce blast radius in case of a token compromise. |
| Send diagnostic logs to a Log Analytics workspace and add the Event Hubs data connector in Microsoft Sentinel. Create an alert for the `RequestsAuthenticationError` metric with a threshold more than 10 per hour to detect authentication attacks. | The Microsoft Sentinel connector centralizes Event Hubs security events. The `RequestsAuthenticationError` metric alert notifies you of authentication attacks in real time. |

---

## Cost Optimization

Cost Optimization focuses on **detecting spend patterns, prioritizing investments in critical areas, and optimizing in others** to meet the organization's budget.

### Workload Design Checklist

- **Create and maintain a cost model for Event Hubs workloads**: Assess throughput unit or processing unit requirements based on peak and average traffic patterns for accurate capacity planning. Include auto-inflate costs and an analysis of service tiers—Basic, Standard, Premium, and Dedicated. Calculate message retention storage costs based on retention periods and message volumes. Include Event Hubs Capture costs for operation and destination storage.

- **Implement cost monitoring and budget alerting**: Configure Microsoft Cost Management for granular cost tracking and analysis. Apply resource tagging for accurate cost allocation across workloads and business units. Activate cost anomaly detection to flag unexpected spending patterns. Monitor throughput unit utilization and message retention storage costs.

- **Optimize Event Hubs capacity planning and autoscaling configuration for cost efficiency**: Analyze traffic patterns to determine optimal throughput unit or processing unit allocation. Monitor partition utilization for optimization opportunities. Set auto-inflate maximum limits in Standard tier deployments to prevent unexpected cost increases. Fine-tune partition count for efficient throughput utilization and consumer scaling. Use load testing to validate capacity assumptions.

- **Establish cost guardrails and governance policies**: Create Azure Policy definitions that enforce throughput unit limits and restrict service tier choices. Define retention period policies to prevent long-term storage cost growth. Set up approval workflows for high-capacity deployments and tier upgrades.

- **Optimize development and testing environments to reduce costs**: Use the Basic or Standard tier with minimal throughput units and shorter retention periods for development and testing scenarios. Implement automated lifecycle management to schedule shutdowns during non-business hours.

### Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Configure Cost Management for granular cost tracking. Create budgets with 50%, 75%, 90%, and 100% alert thresholds for multi-stage cost control warnings. Set up automated cost reports on weekly and monthly schedules. | Enables accurate cost allocation and chargeback, and provides early warnings for cost overruns through multi-level alerting. |
| Select the right service tier (Basic, Standard, Premium, or Dedicated) based on economic analysis. Configure auto-inflate with maximum throughput unit limits based on budget constraints. | Matching the tier to workload needs optimizes costs. Setting a maximum for auto-inflate prevents unexpected cost increases. |
| Configure retention periods aligned with data access patterns and compliance requirements. Enable Event Hubs Capture to use Azure Blob Storage or Azure Data Lake Store for long-term storage. Choose Cool or Archive storage tiers for captured data that you rarely access. | Reduces storage costs through optimized retention policies and provides affordable long-term archival options. |
| Deploy Azure Policy definitions that set throughput-unit caps and restrict allowed tiers to enforce cost controls. Set up a policy-exemption approval workflow for controlled flexibility. | Provides automated cost governance through policy-based controls and reduces cost-overrun risks. |
| Create Automation runbooks to shut down lower environments on weeknights and weekends to reduce runtime costs. | Reduces development and testing costs through automated lifecycle management. |

---

## Operational Excellence

Operational Excellence primarily focuses on procedures for **development practices, observability, and release management**.

### Key Checklist Items

- Apply safe deployment practices for configuration changes (blue-green, canary deployments)
- Design IaC strategies for resource management (Bicep or Terraform)
- Establish CI/CD pipelines for Event Hubs infrastructure, applications, and schemas
- Implement monitoring with custom dashboards, diagnostic logging with correlation IDs, and Application Insights distributed tracing
- Design operational runbooks and incident response procedures for specific Event Hubs failure scenarios
- Automate consumer group management, partition scaling analysis, throughput unit adjustments, and consumer lag monitoring

### Key Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Create IaC templates in Bicep or Terraform that define the Event Hubs namespace, event hub configurations, partition counts, throughput units, and consumer groups. | Ensures consistent deployment across environments. Reduces manual configuration errors and enables version-controlled infrastructure changes. |
| Configure Azure Monitor through custom dashboards, diagnostic logging with structured correlation IDs, and Application Insights integration for end-to-end transaction tracing. | Provides operational visibility and real-time monitoring capabilities. Supports efficient troubleshooting with distributed tracing, auditing, and anomaly detection. |
| Develop operational runbooks using Azure Monitor workbooks. Document consumer group management, throughput scaling steps, partition rebalancing procedures, and troubleshooting steps for consumer lag remediation. | Standardizes operational procedures. Speeds up incident response, ensures consistent practices across operational teams. |

---

## Performance Efficiency

Performance Efficiency is about **maintaining user experience even when there's an increase in load** by managing capacity.

### Key Checklist Items

- Plan capacity for Event Hubs workload requirements (assess peak ingestion rates, concurrent producers, consumer throughput)
- Choose Event Hubs tier and SKU based on performance needs (Standard: 32 partitions, 1–7 day retention; Premium: enhanced networking, improved SLA; Dedicated: up to 1,024 partitions, 90-day retention)
- Design Event Hubs scaling strategy (throughput unit scaling vs. partition scaling)
- Implement performance monitoring (baseline ingestion rates, consumer lag, throughput unit utilization)
- Conduct performance testing (realistic producer event rates, consumer patterns, partition key distribution)
- Optimize configuration and design patterns (connection pooling, batch sizes, compression, retry policies)

### Key Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Set initial throughput units based on capacity planning estimates. Enable auto-inflation. Configure maximum throughput unit limits for cost control and set utilization threshold triggers at 80–90% utilization. | Automatic scaling removes manual intervention during traffic spikes and optimizes costs based on demand. |
| Implement the event processor host or Azure Functions to manage partitions automatically and avoid manual assignment. Configure prefetch settings to improve throughput. Monitor consumer lag metrics per partition to identify processing bottlenecks. | Automatic partition distribution across consumer instances simplifies scaling. Consumer lag visibility identifies processing bottlenecks for targeted optimization. |
| Configure dedicated consumer groups for Stream Analytics and Azure Functions to optimize downstream processing. Tune checkpoint frequency based on processing patterns. | Dedicated consumer groups optimize downstream processing. Optimized checkpointing balances resilience and performance requirements. |
| Configure batch sizes, prefetch values, and retry policies in SDK settings to improve producer and consumer performance. Use connection pooling to reduce overhead and enable compression with schema registry integration. | Batching and prefetch tuning optimizes throughput. Connection pooling and compression reduce network overhead. |

---

## Azure Policies

Built-in Azure Policy definitions for Event Hubs you can audit:
- Event Hubs namespace uses a customer-managed key for encryption
- Event Hubs namespaces have double encryption enabled
- Resource logs in Event Hubs are enabled

## Related Resources

- [Event Hubs overview](/azure/event-hubs/event-hubs-about)
- [Stream processing with Azure Stream Analytics](/azure/architecture/reference-architectures/data/stream-processing-stream-analytics)
- [Event Hubs monitoring](/azure/event-hubs/monitor-event-hubs)

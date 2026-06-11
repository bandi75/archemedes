<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/service-guides/cosmos-db -->
<!-- publication_date: 2025-11-21 -->
<!-- category: waf -->

# Architecture Best Practices for Azure Cosmos DB for NoSQL — Well-Architected Framework Service Guide

Azure Cosmos DB is a fully managed database solution that can host multiple database types like NoSQL, relational, vector, and table databases. This guidance focuses on the Azure Cosmos DB for NoSQL variant and is mapped to the principles of the Well-Architected Framework pillars.

---

## Reliability

The purpose of the Reliability pillar is to provide continued functionality by **building enough resilience and the ability to recover fast from failures**.

### Workload Design Checklist

- **Choose a simple design and avoid unnecessary features**: Don't adopt functionality that unnecessarily adds complexity, like multiple-primary writes and custom indexing, unless your workload truly requires it. Offload cross-cutting concerns to other services such as Microsoft Entra ID for authentication and Azure Monitor for monitoring.

- **Identify and prioritize workload flows**: Not all flows are equally important. Identify the critical paths and assign priorities to each flow. Some flows might require higher throughput or be more sensitive to latency. Some solution flows might require different transaction consistency levels.

- **Use failure mode analysis to identify potential failures**:

  | Failure | Mitigation |
  |---|---|
  | High latency and timeouts after rollout to users in a new geographical region | Enable multiple-region replication to an Azure region that's closer to the new users. |
  | Throttling because of exceeding request units (RUs) | Implement retry logic. Monitor RU consumption and adjust throughput settings as needed. |
  | Azure Cosmos DB service failure in a single zone in a single Azure region | Configure availability zone support when you create a database. |

- **Always use the SDK to access your databases**: Use the Cosmos DB SDK in your clients and tune client-side error handling parameters for both reads and writes. The SDK has built-in transient fault handling. The SDK also allows you to capture rich diagnostics logs on the client to provide reliability observability.

- **Build redundancy to improve resiliency and help meet reliability targets**: Design your database account deployment so it spans at least two regions in Azure. Distribute your account across multiple availability zones if your Azure region supports it. Evaluate the multiple-region and single-region write strategies for your workload. For single-region write, design your workload to have at least a second read region for failover. Enable automatic failover for single-region write and multiple-region read scenarios.

- **Use native disaster recovery and backup features**: Implement database and container backups and restores to meet your requirements. Configure your account with continuous backup. Choose the appropriate retention period based on your business requirements.

### Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Distribute your Azure Cosmos DB account across availability zones when available. | Availability zones provide segregated power, networking, and cooling, which helps isolate hardware failures to a subset of your replicas. |
| Configure your Azure Cosmos DB account to span at least two regions. | Spanning multiple regions helps ensure that your workload is resilient to regional outages. If there is a failure in a write region, you can read from another replica. |
| Enable service-managed failover for your account. | Service-managed failover allows Azure Cosmos DB to automatically change the write region of a multiple-region account to preserve availability. This change occurs without user interaction. |

---

## Security

The purpose of the Security pillar is to provide **confidentiality, integrity, and availability** guarantees to the workload.

### Workload Design Checklist

- **Review security baselines**: Review the security checklist for Azure databases and the security baseline for Azure Cosmos DB. Implement the data protection and identity management security baselines at minimum. Assess service-level compliance and certifications in the context of current global personal data requirements.

- **Implement strict, conditional, and auditable identity and access management**: Use Microsoft Entra ID for your workload's authentication and authorization needs. For control plane and data plane access to your account, create roles, groups, and assignments based on the principle of least-privilege access. Consider disabling key-based authentication.

- **Encrypt data**: Encrypt data at rest and data in motion by using service-managed keys or customer-managed keys.

- **Apply network segmentation and security controls**: Create intentional segmentation and perimeters in your network design. Reduce the surface attack area by using private endpoints in accordance with the security baseline for Azure Cosmos DB.

- **Implement a holistic security monitoring strategy**: Audit user access, security breaches, and resource operations by using control plane logs. Monitor data egress, data changes, usage, and latency by using data plane metrics.

- **Use secure development and testing practices**: Follow secure coding practices and perform secure code reviews when developing applications that interact with Azure Cosmos DB.

### Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Disable public endpoints and use private endpoints whenever possible. | Using private networking through private endpoints reduces the surface area susceptible to attacks on your account. |
| Use role-based access control (RBAC) to limit control-plane access to specific identities and groups within well-defined assignments. | Using RBAC helps prevent unauthorized access to your account. Assign appropriate roles and permissions based on the principle of least privilege. |
| Create virtual network endpoints and rules to limit access to the account. Use network security groups (NSGs) to control traffic to and from Azure Cosmos DB resources. | Virtual network service endpoints, NSGs, and firewall rules help restrict access to your Azure Cosmos DB account and help protect your data from unauthorized access. |
| Monitor control plane logs to detect unauthorized modifications to your Azure Cosmos DB account. | Monitoring helps you track access patterns and audit logs to ensure that your database remains secure and compliant with relevant data protection regulations. |
| Enable Microsoft Defender for Azure Cosmos DB to trigger security alerts when anomalous activities occur. | Microsoft Defender detects attempts to exploit databases in your account, including potential SQL injections, suspicious access patterns, and other potential exploitation activities. |

---

## Cost Optimization

Cost Optimization focuses on **detecting spend patterns, prioritizing investments in critical areas, and optimizing in others** to meet the organization's budget.

### Workload Design Checklist

- **Optimize your Azure Cosmos DB scaling strategy**: Understand how Azure Cosmos DB handles storage and throughput scaling. Select a throughput allocation schema that suits your workload — review the benefits of standard and autoscale throughput distributed at the database or container level. Also, consider serverless options when appropriate. Analyze your workload's traffic patterns to select the most suitable throughput allocation scheme.

- **Optimize your Azure Cosmos DB data costs**: Take an inventory of data and calculate the expected overall data storage. The size of both items and indexes influence your data storage cost. Calculate the impact of replication and backup on storage costs. Create a strategy to automatically remove older items that are no longer used (TTL).

- **Optimize your queries for cost**: Evaluate your most common queries that minimize cross-partition lookups. Use projection to reduce throughput costs of large query result sets. Avoid using unbounded cross-partition queries — ensure queries search within a single logical partition whenever possible. Design an indexing policy that considers the common operations and queries in your workload.

### Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Monitor the usage and patterns of RUs per second. Use queries and other data research techniques to find antipatterns in your application code. | Using metrics to monitor RU consumption starting early helps you identify inefficient queries and operations that consume excessive RUs. You can optimize queries to lower costs. |
| Customize your indexing policy to align with your workload. Use an indexing policy based on only the paths that you need to index for your common queries. For write-heavy workloads, disable automatic indexing of columns not used in queries. | The default indexing policy indexes all paths in an item and can significantly affect RU consumption and costs. Customizing allows you to tailor the indexing strategy to your specific requirements. |
| Select partition keys for your workload that evenly distribute throughput consumption and data storage across logical partitions. Avoid hot partitions that receive a disproportionate amount of traffic. | Choosing the right partition key evenly distributes data, which reduces the likelihood of hot partitions and optimizes throughput consumption. |
| Select the right provisioned throughput option (serverless or provisioned throughput; manual provisioning or autoscale). Apply at the database or container level, depending on the specific needs of your workload. | Selecting the right option helps optimize cost by avoiding over-provisioning or under-provisioning. |
| Configure the default consistency level for your application. Consider the higher costs associated with reads at stronger consistency levels. | Choosing the right consistency level ensures you achieve the desired balance between data consistency, availability, performance, and cost. |
| Use the Azure Cosmos DB emulator for dev/test workloads. | The emulator reduces costs for dev/test and continuous integration use cases. |
| Implement time-to-live (TTL) to automatically delete unnecessary data. Export the expired data to a lower-cost storage solution if needed. | Using TTL ensures that your database remains clutter free, which optimizes storage costs. |
| Consider an analytical store for heavy aggregations using Azure Synapse Link. | Azure Cosmos DB analytical store automatically syncs your data to a separate column store to optimize for large aggregations, reporting, and analytical queries. |

---

## Operational Excellence

Operational Excellence primarily focuses on procedures for **development practices, observability, and release management**.

### Key Checklist Items

- **Monitor your Azure Cosmos DB instances**: Include Azure Cosmos DB instances across regions in your workload monitoring solution. Create identifiers in the client application to differentiate workloads. Draft a log and metrics monitoring strategy to differentiate between different workloads, flag exceptional scenarios, track patterns in exceptions and errors, and track host machine performance. Define multiple alerts to monitor throttling, analyze throughput allocation, and track the size of your data.

- **Automate deployments through IaC**: Incorporate all Azure Cosmos DB changes, including infrastructure deployments and configuration changes, in your code deployment practices. Create and enforce best practices to automate the deployment of your Azure Cosmos DB for NoSQL account and resources. Ensure that your team uses the same templates to deploy to other nonproduction environments.

### Key Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Ensure that application developers use the latest version of the developer SDK. | Using the latest versions of the developer SDKs helps maintain the performance, security, and compatibility of your applications. |
| Capture supplemental diagnostics by using the diagnostics injection techniques for each SDK. | By injecting diagnostics, you can capture custom metrics, traces, and logs to improve troubleshooting and optimize your applications. |
| Create alerts for throughput throttling by using metrics like the normalized RU consumption. This metric measures the percentage usage of provisioned throughput. | If throughput throttling is consistently at 100%, requests likely return a transient error. By creating alerts, you can receive notifications when the usage exceeds your defined thresholds and take corrective actions. |
| Use query performance metrics to track the performance of your top queries over time. | Performance metrics allow you to better understand how your queries run and where potential bottlenecks exist. |

---

## Performance Efficiency

Performance Efficiency is about **maintaining user experience even when there's an increase in load** by managing capacity.

### Key Checklist Items

- **Plan and proactively manage capacity**: Define a performance baseline. Measure how many concurrent users and transactions you might need to handle. Research target users and determine which Azure regions are closest to them.

- **Optimize your data design**: Design items so their corresponding JSON documents are as small as possible. Keep items less than **100 KB** in size. Larger items consume more throughput for common read and write operations.

- **Optimize queries for performance**: Review the query performance tips. Identify queries that use one or more ordering fields. Include these fields explicitly in the indexing policy design. Design large workloads to use bulk operations whenever possible.

- **Optimize code logic**: Use the singleton pattern for the `CosmosClient` class in most SDKs. Constantly creating and disposing instances can result in reduced performance.

### Key Configuration Recommendations

| Recommendation | Benefit |
|---|---|
| Use the capacity calculator to determine the amount of throughput required for your performance baseline. Use autoscale to scale your actual throughput to more closely match your actual workload. | Using the capacity calculator helps you make informed decisions about provisioning resources initially. Autoscale throughput automatically adjusts provisioned throughput to match actual workload needs. |
| Use global distribution and deploy Azure Cosmos DB instances in all regions closest to your end users. | Deploying your database to the regions closest to your end users helps reduce read latency which can improve user experience. |
| Use multi-region writes if your clients are geographically distributed. | Reduces write latency by allowing the client to write to a region that is closest to it. |
| Configure the SDK for Direct mode for the best performance. This mode allows your client to open TCP connections directly to partitions in the service and send requests directly with no intermediary gateway. | Direct mode provides better performance because there are fewer network hops. |
| Use the bulk feature of client SDKs in scenarios that require high throughput. The bulk feature automatically manages and batches operations to maximize throughput. | Using the bulk feature reduces the number of back-end requests and efficiently distributes tasks across partitions. This approach improves performance and resource usage. |
| Disable indexing for bulk operations. If there are several insert, replace, or upsert operations, disable indexing to improve the speed of the operation while using the bulk support of the corresponding SDK. You can immediately reenable indexing later. | Disabling indexing during bulk operations reduces the overhead associated with maintaining the index. |
| Create composite indexes for fields in complex operations. Consider using composite indexes for `ORDER BY` statements that have multiple fields. | Composite indexes can increase the efficiency of operations on multiple fields, which makes data retrieval fast and efficient. |

---

## Azure Policies

Built-in Azure Policy definitions for Azure Cosmos DB you can audit:
- The Azure Cosmos DB account is deployed to at least two regions
- Azure Cosmos DB database accounts are appropriately configured for zone redundancy
- Azure Cosmos DB database accounts should have local authentication methods disabled (requiring Microsoft Entra ID)
- Public network access is disabled so your Azure Cosmos DB account isn't exposed on the public internet
- The maximum throughput should be restricted when creating Azure Cosmos DB databases and containers through the resource provider

## Related Resources

- [Multitenancy and Azure Cosmos DB](/azure/architecture/guide/multitenant/service/cosmos-db)
- [Common Azure Cosmos DB use cases](/azure/cosmos-db/use-cases)
- [Serverless database computing by using Azure Cosmos DB](/azure/architecture/solution-ideas/articles/serverless-apps-using-cosmos-db)

<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/what-is-well-architected-framework -->
<!-- publication_date: 2025-11-01 -->
<!-- category: waf -->

# Azure Well-Architected Framework Overview

The Azure Well-Architected Framework is a design framework that can improve the quality of a workload by helping it to:

- Be reliable and resilient, meeting your availability and recovery targets
- Be as secure as you need it to be
- Deliver a sufficient return on investment by optimizing costs
- Support responsible operations and deployments
- Achieve its performance targets efficiently

The framework is organized around **five pillars of architectural excellence**:

| Pillar | Focus |
|---|---|
| **Reliability** | Resilience, availability, and recoverability |
| **Security** | Protection from threats; confidentiality, integrity, availability of data |
| **Cost Optimization** | Maximize business value; minimize waste |
| **Operational Excellence** | DevOps practices, monitoring, safe deployments |
| **Performance Efficiency** | Efficient scaling to meet demand |

## Who Should Use It

The framework applies to everyone who has decision-making authority within the scope of a workload:
- Architects (primary audience)
- Developers
- Operators/SREs
- Business stakeholders evaluating trade-offs

## How to Apply the Framework

The recommended approach:

1. **Master design principles** for each pillar relevant to your workload
2. **Prioritize checklist items** based on your business goals and risk tolerance
3. **Understand trade-offs** — optimizing one pillar often involves trade-offs with others
4. **Match to your scenario** — use service-specific WAF guides for Azure services in your architecture
5. **Configure Azure services** according to WAF recommendations for each service

## Maturity Model

The framework uses a five-level maturity progression:

| Level | Description |
|---|---|
| 1 — Foundation | Basic practices established; manual processes |
| 2 — Managed | Repeatable processes; some automation |
| 3 — Defined | Standardized across the organization; metrics tracked |
| 4 — Quantitatively Managed | Data-driven decisions; advanced monitoring |
| 5 — Optimizing | Continuous improvement; predictive capabilities |

## Pillar Interaction and Trade-offs

The pillars interact and sometimes conflict:

- **Reliability vs Cost**: Multi-region redundancy improves reliability but increases cost
- **Security vs Performance**: Encryption and authorization checks add latency overhead
- **Reliability vs Operational Excellence**: More automated recovery means more complex runbooks
- **Cost vs Performance**: Right-sizing reduces cost but may hit performance ceilings under load

The framework helps teams make deliberate, documented trade-offs rather than accidental ones.

## Well-Architected Review

Microsoft offers a **Well-Architected Review** assessment tool at [aka.ms/assessments](https://aka.ms/assessments). The tool:
- Asks questions across all five pillars
- Scores your workload per pillar (0–100)
- Provides prioritized recommendations
- Links to detailed implementation guidance

## Service-Specific Guides

The WAF includes service-specific guidance for every major Azure service. These guides provide pillar-by-pillar recommendations specific to how you configure and use each service. Key guides relevant to fraud detection architectures:

- [Event Hubs WAF guide](waf-event-hubs-service-guide.md)
- Azure Stream Analytics WAF guide
- Azure Cosmos DB WAF guide
- Azure Kubernetes Service WAF guide
- Azure Monitor WAF guide

## Design Principles Summary

### Reliability
- Design for failure; assume components will fail
- Use redundancy at every tier (compute, data, network)
- Test failure modes proactively (chaos engineering)
- Define and measure availability targets (SLOs)

### Security
- Apply zero trust (verify explicitly, least privilege, assume breach)
- Protect data at rest and in transit
- Use identity as the primary security perimeter
- Implement defense in depth

### Cost Optimization
- Align spending with business value
- Right-size resources; avoid over-provisioning
- Use reserved instances and savings plans for stable workloads
- Continuously monitor and optimize

### Operational Excellence
- Automate deployments (IaC, CI/CD pipelines)
- Instrument everything; set actionable alerts
- Practice safe deployment (blue/green, canary)
- Run and improve runbooks for common failure scenarios

### Performance Efficiency
- Design for horizontal scale (stateless services)
- Cache aggressively at the appropriate layer
- Optimize data access patterns (partition keys, indexes)
- Load test before production; monitor after deployment

<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/reliability/principles -->
<!-- publication_date: 2025-09-30 -->
<!-- category: waf -->

# Reliability Design Principles — Azure Well-Architected Framework

A reliable workload must survive outages and malfunctions and **continue to consistently provide its intended functionality**. It must be **resilient** so that it can detect and withstand faults while continuing to operate. It must be **recoverable** so that, if a disruption exceeds resiliency measures, the workload can be restored within agreed recovery targets. It must also be **available** so that users can access the workload during the promised time period at the promised quality level.

Workload architectures should have **reliability assurances in application code, infrastructure, and operations**.

---

## Design for Business Requirements

> **Goal**: Get clarity on the workload's scope, user growth, and promises made to external customers and internal stakeholders.

Design isn't guesswork based on undefined or vague outcomes. Reliability requires a deliberate activity that achieves alignment on acceptable user experience, design constraints, and on what success looks like and how it's measured.

| Approach | Benefit |
|---|---|
| Focus on gathering information needed to define the **scope and depth of the solution**. Clarify constraints that influence business goals. What level of resiliency, recovery, observability, and simplicity is required? Are there defined constraints related to cost, compliance, geography, or latency? | Understanding goals and boundaries will prevent guesswork. Otherwise, you might be stuck in an iterative design loop, resulting in wasted efforts and unnecessary costs. |
| Translate business goals into **shared understanding of architectural trade-offs** within real constraints. Present options that impact: Financial cost, Engineering complexity, Security considerations, Operational overhead | This will help stakeholders understand the cost, complexity, and operational implications of their asks, guiding them toward realistic, aligned outcomes. |
| **Prioritize defining reliability outcomes for each critical user flow** over generic measurements, such as uptime. Identify the user-facing capabilities and flows through the system, and for each one, assess its business value, usage patterns, and resilience requirements. | This conversation helps shift stakeholders away from untenable statements, like "the site must always be up," to practical, achievable expectations tied to real functionality and outcomes. |
| **Anchor design choices around time horizons**. Define the usage expectations with realistic forecasting. For example, what's the expected user load at launch? Is user growth expected to be linear, exponential, or uncertain? | This information will help you design an architecture that will address near-term reliability needs while avoiding design decisions that will require significant rework to handle future horizons. |
| **Factor in dependencies** that might limit the autonomy of the design, like organizational constraints. Be aware of centralized infrastructure, security mandates, network routing policies, or platform decisions that directly impact what you can promise in terms of resiliency, availability, and recovery. | Understanding your dependency on services outside of your control helps you design with realistic expectations for reliability. |

---

## Design for Resilience

> **Goal**: The workload must continue to operate with full or reduced functionality.

Expect that component malfunctions, platform outages, performance degradations, limited resource availability, and other faults will occur. Build resiliency in the system so that it's *fault-tolerant and can degrade gracefully*.

| Approach | Benefit |
|---|---|
| **Distinguish components that are on the critical path** from those that can function in a degraded state. | Not all components of the workload need to be equally reliable. Determining criticality helps you design according to the criticality of each component. You won't overengineer resiliency for components that could slightly deteriorate the user experience, as opposed to components that can cause end-to-end problems if they fail. |
| **Identify potential failure points in the system**, especially for the critical components, and determine the effect on user flows. | You can analyze the failure cases, blast radius, and intensity of fault: full or partial outage. This analysis influences the design of error handling capabilities at the component level. |
| **Build self-preservation capabilities** by using design patterns correctly and modularizing the design to isolate faults. | The system will be able to prevent a problem from affecting downstream components. The system will be able to mitigate transient and permanent failures, performance bottlenecks, and other problems that might affect reliability. You'll also be able to minimize the blast radius. |
| **Add the capability to scale out the critical components** (application and infrastructure) by considering the capacity constraints of services in the supported regions. | The workload will be able to handle variable capacity spikes and fluctuations. This capability is crucial when there's an unexpected load on the system, like a surge in valid usage. |
| **Build redundancy in layers and resiliency on various application tiers.** Aim for redundancy in physical utilities and immediate data replication. Also aim for redundancy in the functional layer that covers services, operations, and personnel. | Redundancy helps minimize single points of failure. For example, if there's a component, availability zone, or regional outage, redundant deployment (in active-active or active-passive) allows you to meet uptime targets. |
| **Overprovision to immediately mitigate individual failure** of redundant instances and to buffer against runaway resource consumption. | Higher investment in overprovisioning increases resiliency. The system will continue to operate at full utility during an active failure even before scaling operations can start to remediate the failure. |

---

## Design for Recovery

> **Goal**: The workload must be able to anticipate and recover from most failures, of all magnitudes, with minimal disruption to the user experience and business objectives.

Even highly resilient systems need *disaster preparedness approaches*, in both architecture design and workload operations. On the data layer, you should have strategies that can repair workload state in case of corruption.

| Approach | Benefit |
|---|---|
| **Have structured, tested, and documented recovery plans** that are aligned with the negotiated recovery targets. Plans must cover all components in addition to the system as a whole. | A well-defined process leads to a quick recovery that can prevent negative impact on the finances and reputation of your business. Conducting regular recovery drills tests the process of recovering system components, data, and failover and failback steps to avoid confusion when time and data integrity are key measures of success. |
| Ensure that you can **repair data** of all stateful components within your recovery targets. | Backups are essential to getting the system back to a working state by using a trusted recovery point, like the last-known good state. Immutable and transactionally consistent backups ensure that data can't be altered, and that the restored data isn't corrupted. |
| Implement **automated self-healing capabilities** in the design. | This automation reduces risks from external factors, like human intervention, and shortens the break-fix cycle. |
| Replace stateless components with **immutable ephemeral units**. | Building ephemeral units that you can spin up and destroy on demand provides repeatability and consistency. Use side-by-side deployment models to make the transition to the new units incremental, minimizing disruptions. |

---

## Design for Operations

> **Goal**: Shift left in operations to anticipate failure conditions.

*Test failures early and often* in the development lifecycle, and determine the impact of performance on reliability. For the sake of root cause analysis and postmortems, you need to have shared visibility, across teams, of dependency status and ongoing failures.

| Approach | Benefit |
|---|---|
| **Build observable systems** that can correlate telemetry. | Monitoring and diagnostics are crucial operations. If something fails, you need to know that it failed, when it failed, and why it failed. Observability at the component level is fundamental, but aggregated observability of components and correlated user flows provides a holistic view of health status. |
| **Predict potential malfunctions and anomalous behavior.** Make active reliability failures visible by using prioritized and actionable alerts. Invest in reliable processes and infrastructure that leads to quicker triage. | Site reliability engineers can be notified immediately so that they can mitigate ongoing live site incidents and proactively mitigate potential failures identified by predictive alerts before they become live incidents. |
| **Simulate failures** and run tests in production and pre-production environments. | It's beneficial to experience failures in production so you can set realistic expectations for recovery. This allows you to make design choices that gracefully respond to failures. |
| Build components with **automation in mind**, and automate as much as you can. | Automation minimizes the potential for human error, bringing consistency to testing, deployment, and operations. |
| Factor in **routine operations and their impact** on the stability of the system. | The workload might be subject to ongoing operations, like application revisions, security and compliance audits, component upgrades, and backup processes. Scrutinizing those changes ensures the stability of the system. |
| Continuously **learn from incidents in production**. | Based on the incidents, you can determine the impact and oversights in design and operations that might go unnoticed in preproduction. Ultimately, you'll be able to drive improvements based on real-life incidents. |

---

## Keep It Simple

> **Goal**: Avoid overengineering the architecture design, application code, and operations.

It's often what you remove rather than what you add that leads to the most reliable solutions. *Simplicity reduces the surface area for control*, minimizing inefficiencies and potential misconfigurations or unexpected interactions.

| Approach | Benefit |
|---|---|
| Add components to your architecture only if they help you achieve target business values. **Keep the critical path lean**. | Designing for business requirements can lead to a straightforward solution that's easy to implement and manage. Avoid having too many critical components, because each one is a significant point of failure. |
| **Establish standards** in code implementation, deployment, and processes, and document them. Identify opportunities to enforce those standards by using automated validations. | Standards provide consistency and minimize human errors. |
| Evaluate whether theoretical approaches translate to **pragmatic design** that applies to your use cases. | Application code that's too granular can lead to unnecessary interdependence, extra operations, and difficult maintenance. |
| **Develop just enough code**. | You'll be able to prevent problems that are the result of inefficient implementations, like unexpected resource consumption, user or dataflow failures, and code bugs. |
| **Take advantage of platform-provided features** and prebuilt assets that can help you effectively meet business targets. | This approach minimizes development time. It also enables you to rely on tried and tested practices that have been used with similar workloads. |

---

## Design Review Checklist for Reliability

The 10 checklist items (RE:01–RE:10) span from foundational design principles through operational validation:

1. **RE:01 — Simplicity First**: Prioritize practical approaches that avoid unnecessary complexity
2. **RE:02 — Flow Assessment**: Rank user and system flows using business-driven criticality scales
3. **RE:03 — Failure Analysis**: Conduct failure mode analysis to identify vulnerabilities and dependencies
4. **RE:04 — Target Definition**: Establish reliability metrics that inform design and health monitoring
5. **RE:05 — Redundancy Strategy**: Incorporate redundant components and instances for critical flows
6. **RE:06 — Scaling Plans**: Design timely, predictable scaling with minimal manual oversight
7. **RE:07 — Self-Preservation**: Deploy self-healing mechanisms and established cloud patterns
8. **RE:08 — Resilience Testing**: Apply chaos engineering principles to validate failure handling
9. **RE:09 — Disaster Recovery**: Create structured, tested DR plans aligned with recovery targets
10. **RE:10 — Health Monitoring**: Track system indicators continuously with retained, accessible data

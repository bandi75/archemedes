<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/cost-optimization/principles -->
<!-- publication_date: 2025-05-27 -->
<!-- category: waf -->

# Cost Optimization Design Principles — Azure Well-Architected Framework

Architecture design is always driven by business goals and must **factor in return on investment (ROI) and financial constraints**. A cost-optimized workload isn't necessarily a low-cost workload. Tactical approaches are reactive and can reduce costs only in the short term. To achieve long-term financial responsibility, you need to **create a strategy with prioritization, continuous monitoring, and repeatable processes** that focuses on optimization.

---

## Develop Cost-Management Discipline

> **Goal**: Build a team culture that has awareness of budget, expenses, reporting, and cost tracking.

Cost optimization is conducted at various levels of the organization. It's important to understand how your workload cost is aligned with organizational FinOps practices.

| Approach | Benefit |
|---|---|
| Develop a cost model. This fundamental exercise is a prerequisite to setting up a financial tracking system. | A cost model helps segment expenses and estimate and forecast the total cost of ownership, including infrastructure, support, and implementation. It enables you to identify cost drivers early and predict how any change, growth, or shrinkage will affect overall spending. |
| Have an effective but flexible **accountability model** that's governed and implemented with properly assigned roles and responsibilities. | Clear accountability helps enforce the functional expectations of each role, drive clarity, and generate reports with transparency at desired levels. Proactive governance can help you avoid actions that might lead to unnecessary expenditure. |
| Estimate **realistic budgets** that cover all non-negotiable functional and nonfunctional requirements, personnel, and processes that provide for anticipated growth. | You'll be able to set financial boundaries and establish ways to check your spending against the allocated budget. You'll also get notifications when certain thresholds are exceeded, which prevents overspending. |
| For workloads governed by SLAs, evaluate whether to allocate budget toward **potential penalties or toward implementation efforts**. | A well-implemented solution can help you avoid penalties altogether, making proactive investment a pragmatic approach to reduce the risk of future liability. |
| Plan on **training costs, hiring expenses**, and the cost of infrastructure needed to augment skills as the workload matures. | Investing in staffing complements existing skills through full-time or vendor support. |
| **Communicate cost implications of design changes** that are driven by insights gained from production. | The organization is able to make practical budget adjustment based on production feedback. |

---

## Design with a Cost-Efficiency Mindset

> **Goal**: Spend only on what you need to achieve the highest return on your investments.

Every architectural decision has direct and indirect financial implications. Understand the costs associated with build versus buy options, technology choices, the billing model and licensing, training, operations, and so on.

| Approach | Benefit |
|---|---|
| Establish a **cost baseline, including the projected growth**. Ensure design choices work within the allocated budget to meet the functional and nonfunctional requirements. Factor in expenses related to technology choices, automation, acquisition, training, and change management. | Cost estimates enable you to forecast expenses against the budget and pinpoint key cost drivers. They also help reveal hidden costs that might otherwise go unnoticed, supporting a balanced approach that avoids overengineering. |
| **Design and enforce cost guardrails** in your architecture that keep the resources within the upper and lower limits. | Enforcement can prevent incidental or unapproved charges and ensure that only budgeted quantity of resources are provisioned. |
| Treat different **SDLC environments differently**, and deploy the right number of environments. | You can save money by understanding that not all environments need to simulate production. Nonproduction environments can have different features, SKUs, instance counts, and even logging. You can also save costs by creating preproduction environments on-demand and removing them when you no longer need them. |

---

## Design for Usage Optimization

> **Goal**: Maximize the use of resources and operations. Apply them to the negotiated functional and nonfunctional requirements of the solution.

Services and offerings provide various capabilities and pricing tiers. After you purchase a set of features, avoid underutilizing them.

| Approach | Benefit |
|---|---|
| Take advantage of the **full capabilities of your selected resource SKUs** to meet performance, security, reliability, and operational goals. | You can maximize the use of what you paid for. Avoid selecting SKUs with features you don't need, as they can lead to unnecessary costs without added benefit. |
| Evaluate opportunities to **dynamically adjust capacity**, scaling up when demand increases and scaling down when it's no longer needed. | Without this approach, you may need to pre-provision more capacity than necessary. Dynamic scaling enables you to maintain a minimum baseline and expand only when required, aligning resource consumption with actual usage patterns. |
| Prioritize deployment of **active-active models over active-passive models**, as part of your recovery plan, if you already paid for the resources. | If your design defaults to active-passive models, you might have idle resources that could otherwise be used. Converting to active-active might enable you to meet load leveling and scale bursting requirements without overspending. |
| Prioritize the use of **commitment-based discounted resources** when developing new features, setting up additional environments, or optimizing for nonfunctional requirements. | Finding opportunities to use committed plans can significantly reduce the cost of implementing new functionality. |

---

## Design for Rate Optimization

> **Goal**: Increase efficiency without redesigning, renegotiating, or sacrificing functional or nonfunctional requirements.

| Approach | Benefit |
|---|---|
| Identify resources that have **stable or predictable usage patterns** over time. Optimize costs by prepurchasing these resources to take advantage of available discounts. Collaborate with your licensing team to influence future purchasing agreements and renewal strategies. | Microsoft offers discounted rates for predictable, long-term commitments to specific resources or resource categories. These resources incur lower costs during the usage period and can be amortized over time. |
| Explore alternatives that don't require additional licensing. Consider options like **hybrid use and preproduction subscription pricing**. | You'll be able to reduce licensing costs by taking advantage of options that give you usage rights to the same or comparable technologies at a lower cost. |
| Use **consumption-based pricing** when it's more cost effective. | You'll pay for what you use. This option might be more expensive than a fully utilized prepaid option. However, if you don't expect to fully utilize pre-purchased compute, pay-as-you-go might be a better choice. |
| Use **fixed-price billing** instead of consumption-based billing for a resource when its utilization is high and predictable and a comparable SKU or billing option is available. | When utilization is high and predictable, the fixed-price model usually costs less and often supports more features. |
| Where possible, **co-locate usage with other workloads**, resources, and teams to reduce financial and operational costs. | Shared resources are managed centrally and provisioned with higher capacity to support multiple workloads, allowing costs to be distributed across teams. |
| Deploy to **lower-cost regions**, provided there are no compromises to functional or nonfunctional requirements. Evaluate regional options for each environment individually. | Using premium regions only where necessary can lead to significant savings. Savings from non-production environments can be reallocated to other priorities. |
| Prefer services that make it easier to **achieve higher density**. Consider the potential tradeoffs, especially on security boundaries. | As density increases, the amount of resources that you need to run a workload decreases. This decreases cost per unit and the cost of management. |

---

## Monitor and Optimize Over Time

> **Goal**: Continuously right-size investment as your workload evolves with the ecosystem.

What was important yesterday might not be important today. As you learn through evaluation of production workloads, expect changes in architecture, business requirements, processes, and even team structure.

| Approach | Benefit |
|---|---|
| Build capabilities in the system that **capture and classify expense**. | You'll be able to calculate the costs that reveal technical and business perspectives at different billing boundaries. You'll also be able to conduct regular reviews and drive showback and chargeback processes. |
| Implement **cost alerts** when spending approaches predefined budget thresholds. Regularly review and adjust these alerts to ensure they remain aligned with evolving usage patterns. | Proactive notifications help prevent budget overruns and support timely decision-making. |
| Continuously **evaluate and adjust architecture design decisions** around cost of resources, operations, and paid support. | Regular reviews of metrics, performance data, billing reports, and feature usage might lead to fine-tuning that can reduce costs. |
| **Decommission resources** that are underutilized, unused, obsolete, or can be replaced with more efficient alternatives. Regularly delete unnecessary data. | By resizing or removing underutilized resources, or even changing SKUs, you can reduce costs. Shutting down unused resources and deleting data when you no longer need it reduces waste and frees up funds. |

---

## Design Review Checklist for Cost Optimization (CO:01–CO:14)

1. **CO:01 — Financial Culture**: Build organizational accountability for spending decisions
2. **CO:02 — Cost Modeling**: Establish budgets with contingency buffers
3. **CO:03 — Cost Monitoring**: Track daily expenses with automated alerts
4. **CO:04 — Spending Controls**: Implement governance policies and resource limits
5. **CO:05 — Rate Optimization**: Negotiate favorable pricing agreements
6. **CO:06 — Billing Alignment**: Match resource usage to billing structures
7. **CO:07 — Component Optimization**: Remove underutilized features and resources
8. **CO:08 — Environment Costs**: Strategically configure nonproduction systems
9. **CO:09 — Flow Prioritization**: Align spending with business priorities
10. **CO:10 — Data Management**: Optimize storage, tiering, and retention strategies
11. **CO:11 — Code Efficiency**: Reduce resource consumption through optimization
12. **CO:12 — Scaling Strategy**: Evaluate cost-effective scaling approaches
13. **CO:13 — Personnel Efficiency**: Reduce task duration without sacrificing quality
14. **CO:14 — Consolidation**: Centralize resources to increase density

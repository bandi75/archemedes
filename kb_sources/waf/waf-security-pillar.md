<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/security/security-principles -->
<!-- publication_date: 2023-11-15 -->
<!-- category: waf -->

# Security Design Principles — Azure Well-Architected Framework

A Well-Architected workload must be built with a **zero-trust approach**. A secure workload is resilient to attacks and incorporates the interrelated security **principles of confidentiality, integrity, and availability** (the *CIA triad*) in addition to meeting business goals.

As you design your system, use the Microsoft Zero Trust model as the compass to mitigate security risks:

- **Verify explicitly** so that only trusted identities perform intended and allowed actions that originate from expected locations.
- **Use least-privilege access** for the right identities, with the right set of permissions, for the right duration, and to the right assets.
- **Assume breach** of security controls and design compensating controls that limit risk and damage if a primary layer of defense fails.

---

## Plan Your Security Readiness

> **Goal**: Strive to adopt and implement security practices in architectural design decisions and operations with minimal friction.

As a workload owner, you have a shared responsibility with the organization to protect assets. Create a **security readiness plan** that's aligned with business priorities. It will lead to well-defined processes, adequate investments, and appropriate accountabilities.

| Approach | Benefit |
|---|---|
| **Use segmentation as a strategy to plan security boundaries** in the workload environment, processes, and team structure to isolate access and function. Your segmentation strategy should be driven by business requirements. | You'll be able to minimize operational friction by defining roles and establishing clear lines of responsibility. Isolation enables you to limit exposure of sensitive flows to only roles and assets that need access. |
| Continuously **build skills** through **role-based security training** that meets the requirements of the organization and the use cases of the workload. | A highly skilled team can design, implement, and monitor security controls that remain effective against attackers. |
| **Make sure there's an incident response plan** for your workload. Use industry frameworks that define the standard operating procedure for preparedness, detection, containment, mitigation, and post-incident activity. | If you have a well-documented plan, responsible roles can focus on execution without wasting time on uncertain actions. |
| **Strengthen your security posture by understanding the security compliance requirements** imposed by influences outside the workload team, like organizational policies, regulatory compliance, and industry standards. | Clarity about compliance requirements will help you design for the right security assurances and prevent non-compliance issues, which could lead to penalties. |
| **Define and enforce team-level security standards** across the lifecycle and operations of the workload. Strive for consistent practices in coding, gated approvals, release management, and data protection and retention. | Defining good security practices can minimize negligence and the surface area for potential errors. |

---

## Design to Protect Confidentiality

> **Goal**: Prevent exposure to privacy, regulatory, application, and proprietary information through access restrictions and obfuscation techniques.

| Approach | Benefit |
|---|---|
| Implement **strong access controls** that grant access only on a need-to-know basis. | *Least privilege.* The workload will be protected from unauthorized access and prohibited activities. Even when access is from trusted identities, the access permissions and exposure time will be minimized. |
| **Classify data based on its type, sensitivity, and potential risk**. Assign a confidentiality level for each. Include system components that are in scope for the identified level. | *Verify explicitly.* This evaluation helps you right-size security measures. You'll also be able to identify data and components that have a high potential impact and/or exposure to risk. |
| Safeguard your data at rest, in transit, and during processing by using **encryption**. Base your strategy on the assigned confidentiality level. | *Assume breach.* Even if an attacker gets access, they won't be able to read properly encrypted sensitive data. |
| **Guard against exploits** that might cause unwarranted exposure of information. | *Verify explicitly.* It's crucial to minimize vulnerabilities in authentication and authorization implementations, code, configurations, and operations. |
| **Guard against data exfiltration** that results from malicious or inadvertent access to data. | *Assume breach.* You'll be able to contain blast radius by blocking unauthorized data transfer. |
| Maintain an **audit trail** of all types of access activities. | *Assume breach.* Audit logs support faster detection and recovery in case of incidents and help with ongoing security monitoring. |

---

## Design to Protect Integrity

> **Goal**: Prevent corruption of design, implementation, operations, and data to avoid disruptions that can stop the system from delivering its intended utility.

| Approach | Benefit |
|---|---|
| **Implement strong access controls that authenticate and authorize access to the system. Minimize access based on privilege, scope, and time.** | *Least privilege.* Depending on the strength of the controls, you'll be able to prevent or reduce risks from unapproved modifications. |
| **Continuously protect against vulnerabilities and detect them in your supply chain** to block attackers from injecting software faults into your infrastructure, build system, tools, libraries, and other dependencies. | *Assume breach.* Knowing the origin of software and verifying its authenticity throughout the lifecycle will provide predictability. You'll know about vulnerabilities well in advance. |
| **Establish trust and verify by using cryptography techniques** like attestation, code signing, certificates, and encryption. | *Verify explicitly, least privilege.* You'll know that changes to data or access to the system is verified by a trusted source. |
| **Ensure backup data is immutable and encrypted** when data is replicated or transferred. | *Verify explicitly.* You'll be able to recover data with confidence that backup data wasn't changed at rest. |

---

## Design to Protect Availability

> **Goal**: Prevent or minimize system and workload downtime and degradation in the event of a security incident.

| Approach | Benefit |
|---|---|
| **Prevent compromised identities from misusing access** to gain control of the system. Check for overly pervasive scope and time limits to minimize risk exposure. | *Least privilege.* This strategy mitigates the risks of excessive, unnecessary, or misused access permissions on crucial resources. Take advantage of JIT, JEA, and time-based security modes to replace standing permissions wherever possible. |
| Use security controls and design patterns to **prevent attacks and code flaws from causing resource exhaustion** and blocking access. | *Verify explicitly.* The system won't experience downtime caused by malicious actions, like distributed denial of service (DDoS) attacks. |
| Implement **preventative measures for attack vectors that exploit vulnerabilities** in application code, networking protocols, identity systems, malware protection, and other areas. | *Assume breach.* You'll be able to reduce the attack surface to ensure business continuity. |
| **Prioritize** security controls on the **critical components and flows** in the system that are susceptible to risk. | *Assume breach, verify explicitly.* Regular detection and prioritization exercises can help you apply security expertise to the critical aspects of the system. |
| Apply at least the same level of **security rigor in your recovery resources and processes** as you do in the primary environment, including security controls and frequency of backup. | *Assume breach.* A well-designed process can prevent a security incident from hindering the recovery process. |

---

## Sustain and Evolve Your Security Posture

> **Goal**: Incorporate continuous improvement and apply vigilance to stay ahead of attackers who are continuously evolving their attack strategies.

Your security posture must not degrade over time. You must continually improve security operations so that new disruptions are handled more efficiently.

| Approach | Benefit |
|---|---|
| **Create and maintain a comprehensive asset inventory** that includes classified information about resources, locations, dependencies, owners, and other metadata. Automate inventory to derive data from the system. | A well-organized inventory provides a holistic view of the environment, which puts you in an advantageous position against attackers, especially during post-incident activities. |
| **Perform threat modeling** to identify and mitigate potential threats. | You'll have a report of attack vectors prioritized by their severity level. |
| Regularly **capture data to quantify your current state** against your established security baseline and **set priorities for remediations**. Take advantage of platform-provided features for **security posture management** and **the enforcement of compliance**. | You need accurate reports that bring clarity and consensus to focus areas. You'll be able to immediately execute technical remediations, starting with the highest priority items. |
| **Run periodic security tests** conducted by experts external to the workload team who attempt to ethically hack the system. Perform routine and integrated **vulnerability scanning** to detect exploits in infrastructure, dependencies, and application code. | These tests enable you to validate security defenses by simulating real-world attacks using techniques like penetration testing. |
| **Detect, respond, and recover** with swift and effective security operations. | The primary benefit is that it enables you to preserve or restore the security assurances of the CIA triad during and after an attack. |
| **Conduct post-incident activities** like root-cause analyses, postmortems, and incident reports. | These activities provide insight into the impact of the breach and into resolution measures, which drives improvements in defenses and operations. |
| **Get current, and stay current.** Stay current on updates, patching, and security fixes. Use threat intelligence powered by security analytics for dynamic detection of threats. At regular intervals, review the workload's conformance to Security Development Lifecycle (SDL) best practices. | You'll be able to ensure that your security posture doesn't degrade over time. By integrating findings from real-world attacks and testing activities, you'll be able to combat attackers who continuously improve. |

---

## Design Review Checklist for Security (SE:01–SE:12)

1. **SE:01 — Security Baseline**: Establish baseline aligned to compliance and industry standards
2. **SE:02 — Secure Development Lifecycle**: Integrate security throughout the software development lifecycle
3. **SE:03 — Data Classification**: Classify information and apply consistent labeling practices
4. **SE:04 — Segmentation**: Create intentional segmentation across networks, roles, and identities
5. **SE:05 — Identity and Access**: Implement conditional identity management with minimal privilege
6. **SE:06 — Network Security**: Control traffic flow across all network boundaries
7. **SE:07 — Encryption**: Apply modern cryptographic methods based on data classification
8. **SE:08 — Hardening**: Reduce attack surface across all components
9. **SE:09 — Application Secrets**: Secure application credentials with rotation procedures
10. **SE:10 — Threat Monitoring**: Deploy threat detection integrated with security operations
11. **SE:11 — Security Testing**: Validate both prevention and detection mechanisms
12. **SE:12 — Incident Response**: Define procedures for incident management and recovery

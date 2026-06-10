<!-- source_url: https://learn.microsoft.com/en-us/azure/well-architected/security/overview -->
<!-- publication_date: 2025-11-01 -->
<!-- category: waf -->

# Azure Well-Architected Framework — Security Pillar

The Security pillar of the Azure Well-Architected Framework ensures your workload is protected against threats while maintaining **confidentiality, integrity, and availability** of data and systems. Security is not a single control — it is a set of layered controls (defense in depth) applied across identity, network, data, application, and operations.

## Design Principles

### 1. Plan Your Security Readiness
- Define a security baseline before building
- Identify compliance requirements early (PCI-DSS, HIPAA, ISO 27001, SOC 2)
- Classify data by sensitivity; apply controls proportionate to risk

### 2. Design to Protect Confidentiality
- Encrypt data at rest and in transit
- Minimize data exposure: collect only what is needed, mask sensitive fields in logs
- Implement secrets management (Azure Key Vault) — no secrets in code or config files

### 3. Design to Protect Integrity
- Use checksums and digital signatures for data validation
- Implement immutable audit logs
- Use managed identities instead of service principals with secrets

### 4. Design to Protect Availability
- Protect against DDoS attacks (Azure DDoS Protection)
- Implement rate limiting at API gateways
- Use Azure Front Door or Application Gateway with WAF for internet-facing services

### 5. Sustain and Evolve Your Security Posture
- Treat security as continuous process, not one-time setup
- Regularly review access permissions (access reviews via Entra ID)
- Monitor for threats using Microsoft Defender for Cloud and Sentinel

## Zero Trust Principles

The Azure Security pillar is built on Zero Trust:

| Principle | Implementation |
|---|---|
| **Verify explicitly** | Authenticate and authorize every request; don't trust network location |
| **Use least privilege** | Grant minimum permissions; use just-in-time access for elevated roles |
| **Assume breach** | Design assuming attackers are already inside; detect and respond quickly |

## Identity and Access Management

### Managed Identity (Preferred)
Assign system-assigned or user-assigned managed identities to Azure services. Eliminates the need to manage service principal credentials or connection strings.

```
Azure Stream Analytics (managed identity)
    → Event Hubs (Entra RBAC: Azure Event Hubs Data Receiver)
    → Cosmos DB (Entra RBAC: Cosmos DB Built-in Data Contributor)
```

### RBAC Roles for Fraud Detection Stack

| Service | Role | Notes |
|---|---|---|
| Event Hubs | `Azure Event Hubs Data Sender` | For producers |
| Event Hubs | `Azure Event Hubs Data Receiver` | For consumers (ASA, Functions) |
| Cosmos DB | `Cosmos DB Built-in Data Contributor` | For write access |
| Cosmos DB | `Cosmos DB Built-in Data Reader` | For read-only access |
| Azure AI Search | `Search Index Data Contributor` | For indexing |
| Key Vault | `Key Vault Secrets User` | For reading secrets |

### Principle of Least Privilege
- Assign roles at the **resource scope** (not subscription scope)
- Use Entra ID Privileged Identity Management (PIM) for elevated roles with time-bound access
- Review and remove unused role assignments quarterly

## Network Security

### Private Endpoints
- Connect Azure services (Event Hubs, Cosmos DB, Key Vault, AI Search) to your VNet via private endpoints
- All traffic stays on the Azure backbone; no public internet exposure
- Disable public network access on services after private endpoints are configured

### Network Segmentation
- Use Azure Virtual Network with subnets per tier: compute, data, management
- Apply Network Security Groups (NSGs) with explicit deny-all defaults
- Use Azure Firewall or NVA for north-south egress control

### DDoS Protection
- Enable Azure DDoS Network Protection for internet-facing public IPs
- Use Azure Application Gateway with WAF for HTTP/HTTPS endpoints
- Rate-limit API endpoints at the API Management layer

## Data Security

### Encryption at Rest
All Azure services encrypt data at rest by default using service-managed keys:
- Event Hubs: AES-256
- Cosmos DB: AES-256
- Azure Storage (Blob, ADLS): AES-256
- Azure AI Search: AES-256

For PCI-DSS compliance: consider **customer-managed keys (CMK)** via Azure Key Vault for Cosmos DB and Storage to maintain full key control.

### Encryption in Transit
- All Azure services use TLS 1.2+ by default for data in transit
- Disable TLS 1.0 and 1.1 explicitly on all endpoints
- Use service endpoints or private endpoints to avoid internet transit entirely

### Secrets Management
- Store all secrets, connection strings, and API keys in **Azure Key Vault**
- Applications access Key Vault using managed identity (no secret needed to access secrets)
- Enable Key Vault soft-delete and purge protection to prevent accidental or malicious deletion
- Rotate keys and secrets regularly; set Key Vault expiry notifications

## PCI-DSS Considerations for Fraud Detection

PCI-DSS (Payment Card Industry Data Security Standard) applies to systems that store, process, or transmit cardholder data.

Key controls relevant to Azure fraud detection architecture:

| PCI-DSS Requirement | Azure Implementation |
|---|---|
| Req 1: Firewall controls | NSGs, Azure Firewall, private endpoints |
| Req 2: No default passwords | Managed identity (no passwords); Key Vault for secrets |
| Req 3: Protect stored cardholder data | CMK encryption for Cosmos DB and Storage; data masking |
| Req 4: Encrypt in transit | TLS 1.2+ enforced on all services |
| Req 7: Restrict access to need-to-know | RBAC with least privilege; Entra ID |
| Req 8: Unique IDs for access | Entra ID managed identity; no shared accounts |
| Req 10: Track and monitor access | Azure Monitor, Diagnostic Logs, Microsoft Sentinel |
| Req 11: Test security systems | Penetration testing, Defender for Cloud assessments |
| Req 12: Information security policy | Azure Policy, Microsoft Defender for Cloud baseline |

## STRIDE Threat Model for Fraud Detection

| Threat | Relevant Components | Mitigation |
|---|---|---|
| **Spoofing** | API endpoints, Event Hubs producers | Entra ID authentication, SAS with short expiry |
| **Tampering** | Cosmos DB writes, event payloads | TLS in transit, CMK at rest, integrity checks |
| **Repudiation** | Transaction processing, alert generation | Immutable audit logs in Azure Monitor / Storage |
| **Information Disclosure** | Cosmos DB, Log Analytics | Private endpoints, RBAC, log data masking |
| **Denial of Service** | Event Hubs, API Gateway | Auto-inflate, DDoS Protection, rate limiting |
| **Elevation of Privilege** | AKS workload identity, admin access | PIM, least privilege RBAC, pod security standards |

## Security Checklist for Fraud Detection Architectures

- [ ] All services use managed identity (no connection strings in code)
- [ ] All Azure services have public network access disabled; private endpoints configured
- [ ] Key Vault soft-delete and purge protection enabled
- [ ] CMK configured for Cosmos DB (PCI-DSS scope)
- [ ] TLS 1.0/1.1 disabled on all endpoints
- [ ] NSG deny-all default with explicit allow rules per subnet
- [ ] Azure DDoS Network Protection enabled on VNet
- [ ] Microsoft Defender for Cloud enabled; all security recommendations reviewed
- [ ] RBAC reviewed: no wildcard assignments, all roles at resource scope
- [ ] PCI-DSS scoping documented: which resources are in-scope and why

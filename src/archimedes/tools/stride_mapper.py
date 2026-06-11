from __future__ import annotations

from dataclasses import dataclass


STRIDE_CATALOG: dict[str, dict[str, list[str] | str]] = {
    "Spoofing": {
        "keywords": ["identity", "token", "auth", "credential", "impersonation"],
        "description": "Impersonating users, services, or trusted systems.",
        "controls": ["Managed Identity", "Entra ID", "mTLS", "token validation"],
    },
    "Tampering": {
        "keywords": ["integrity", "modify", "payload", "message", "hash"],
        "description": "Unauthorized data or message alteration.",
        "controls": ["TLS", "message signing", "immutable logs", "checksums"],
    },
    "Repudiation": {
        "keywords": ["audit", "trace", "log", "non-repudiation", "forensic"],
        "description": "Actions cannot be reliably traced to actors.",
        "controls": ["centralized logging", "signed audit trails", "correlation ids"],
    },
    "Information Disclosure": {
        "keywords": ["secret", "pii", "leak", "exposure", "encryption"],
        "description": "Unauthorized access to sensitive data.",
        "controls": ["encryption at rest", "private endpoints", "key vault", "rbac"],
    },
    "Denial of Service": {
        "keywords": ["availability", "throttle", "rate", "flood", "traffic spike"],
        "description": "Service degradation or outage due to resource exhaustion.",
        "controls": ["autoscale", "rate limiting", "circuit breakers", "queue buffering"],
    },
    "Elevation of Privilege": {
        "keywords": ["privilege", "role", "rbac", "permission", "admin"],
        "description": "Actor gains higher access than intended.",
        "controls": ["least privilege", "segregation of duties", "pim", "policy checks"],
    },
}


@dataclass(slots=True)
class StrideThreat:
    category: str
    description: str
    threat_statement: str
    suggested_controls: list[str]
    confidence: float


def map_stride_threats(text: str) -> list[StrideThreat]:
    lowered = text.lower()
    threats: list[StrideThreat] = []

    for category, meta in STRIDE_CATALOG.items():
        keywords = meta["keywords"]
        assert isinstance(keywords, list)
        matches = [kw for kw in keywords if kw in lowered]
        if not matches:
            continue

        confidence = min(0.98, 0.45 + (0.1 * len(matches)))
        controls = meta["controls"]
        assert isinstance(controls, list)
        threats.append(
            StrideThreat(
                category=category,
                description=str(meta["description"]),
                threat_statement=f"Potential {category.lower()} risk due to signals: {', '.join(matches)}.",
                suggested_controls=controls,
                confidence=round(confidence, 2),
            )
        )

    return sorted(threats, key=lambda item: item.confidence, reverse=True)

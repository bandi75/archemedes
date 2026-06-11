from __future__ import annotations

from enum import Enum


class StageName(str, Enum):
    INTAKE = "intake"
    REQUIREMENTS_EXTRACTION = "requirements_extraction"
    PATTERN_DETECTION = "pattern_detection"
    OPTIONS_GENERATION = "options_generation"
    SOCRATIC_REVIEW = "socratic_review"
    EVIDENCE_AUDIT_CHECKPOINT = "evidence_audit_checkpoint"
    ADR_GENERATION = "adr_generation"
    HLD_GENERATION = "hld_generation"
    MINI_WAF_REVIEW = "mini_waf_review"
    FINAL_EVIDENCE_AUDIT = "final_evidence_audit"
    REREASONING = "rereasoning"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class QualityGateStatus(str, Enum):
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


class QualityGateOutcome(str, Enum):
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"


class ClaimType(str, Enum):
    FACT = "fact"
    ASSUMPTION = "assumption"
    RECOMMENDATION = "recommendation"
    JUDGMENT = "judgment"
    CONSTRAINT = "constraint"


class EvidenceRetrievalMethod(str, Enum):
    FOUNDRY_IQ = "foundry_iq"
    WEB_SEARCH = "web_search"
    FUNCTION_TOOL = "function_tool"
    USER_INPUT = "user_input"
    MOCK = "mock"


class SourceFreshness(str, Enum):
    CURRENT = "current"
    RECENT = "recent"
    STALE = "stale"
    UNKNOWN = "unknown"


class TrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ChangeType(str, Enum):
    REQUIREMENT_ADDED = "requirement_added"
    REQUIREMENT_MODIFIED = "requirement_modified"
    REQUIREMENT_UPDATED = "requirement_updated"
    REQUIREMENT_REMOVED = "requirement_removed"
    CONSTRAINT_MODIFIED = "constraint_modified"
    SCOPE_CHANGE = "scope_change"
    ASSUMPTION_VALIDATED = "assumption_validated"
    OPTION_OVERRIDDEN = "option_overridden"
    USER_OVERRIDE = "user_override"
    SYSTEM_RETRY = "system_retry"


class DiffType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class SocratesDepth(str, Enum):
    LIGHT = "light"
    STANDARD = "standard"
    DEEP = "deep"


class PersonaName(str, Enum):
    DEVILS_ADVOCATE = "devils_advocate"
    SRE_OPS_LEAD = "sre_ops_lead"
    SECURITY_ARCHITECT = "security_architect"
    FINOPS_LEAD = "finops_lead"
    DELIVERY_LEAD = "delivery_lead"
    CUSTOMER_BIZ_SPONSOR = "customer_biz_sponsor"
    DATA_ARCHITECT = "data_architect"
    SYNTHESIZER = "synthesizer"

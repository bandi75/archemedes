# Archimedes Pydantic Schemas

**Document ID:** `03-pydantic-schemas.md`  
**Solution:** Archimedes — AI Architecture Workbench  
**Version:** v2.2  
**Status:** Implementation-ready baseline  
**Last updated:** 2026-06-09  
**Related documents:** `01-archimedes-hld.md`, `02-domain-models.md`

---

## 1. Purpose

This document defines the concrete Pydantic schema layer for Archimedes.

It translates the domain model from `02-domain-models.md` into implementation-ready Pydantic v2 models, including enums, base classes, lifecycle models, stage patches, artifacts, claims, evidence, Socrates outputs, quality gates, cost estimates, change events, and API-oriented request/response DTOs.

The schemas in this document should be implemented under:

```text
src/archimedes/models/
├── __init__.py
├── base.py
├── enums.py
├── session.py
├── requirements.py
├── patterns.py
├── options.py
├── artifacts.py
├── claims.py
├── evidence.py
├── quality_gates.py
├── socrates.py
├── cost.py
├── change.py
├── patches.py
├── diffs.py
└── api.py
```

This document does not cover:

- Cosmos DB physical container definitions. See `04-database-design.md`.
- FastAPI route contracts in detail. See `05-api-contracts.md`.
- Stage transition logic. See `06-stage-pipeline.md`.
- Full agent prompts. See `07-agent-specifications.md`.
- Socrates workflow implementation. See `08-socrates-engine.md`.
- Tool implementations. See `09-tool-specifications.md`.

---

## 2. Schema Design Principles

The schema layer follows these principles:

1. **Pydantic v2 style only**: use `BaseModel`, `ConfigDict`, `Field`, `field_validator`, and `model_validator`.
2. **Agents return structured patches, never raw database writes**.
3. **Claims are separate from evidence**.
4. **Every stage output is versioned**.
5. **Every stage execution is recoverable** using `stage_run_id`, status, retry count, and failure metadata.
6. **Idempotency and optimistic concurrency are first-class fields** on stage patches.
7. **Stage output schemas should be strict where possible**, but artifact content may allow flexible dictionaries for MVP speed.
8. **Enums are preferred over free-form strings** for persisted state values.
9. **Datetime fields use timezone-aware `datetime` objects**, serialized as ISO 8601 strings.
10. **Large artifacts are referenced by URI**, not embedded directly into every document.

---

## 3. Common Imports

```python
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)
```

---

## 4. Base Model Utilities

File: `src/archimedes/models/base.py`

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


class ArchimedesModel(BaseModel):
    """Base class for all Archimedes schemas."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class FlexibleContentModel(BaseModel):
    """Base class for flexible generated content blocks.

    Use this only where LLM-generated stage content needs controlled flexibility.
    Persisted top-level entities should generally extend ArchimedesModel.
    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class AuditFields(BaseModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: str | None = None
    updated_by: str | None = None
```

### Notes

- `ArchimedesModel` forbids unknown fields. This protects persisted entities from malformed agent output.
- `FlexibleContentModel` allows extra fields and should be used sparingly for generated artifact content where the shape may evolve.
- `use_enum_values=True` keeps persisted JSON clean.

---

## 5. Enums

File: `src/archimedes/models/enums.py`

```python
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


class ClaimType(str, Enum):
    FACT = "fact"
    ASSUMPTION = "assumption"
    RECOMMENDATION = "recommendation"


class EvidenceRetrievalMethod(str, Enum):
    FOUNDRY_IQ = "foundry_iq"
    WEB_SEARCH = "web_search"
    FUNCTION_TOOL = "function_tool"
    USER_INPUT = "user_input"


class SourceFreshness(str, Enum):
    CURRENT = "current"
    RECENT = "recent"
    STALE = "stale"
    UNKNOWN = "unknown"


class TrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequirementPriority(str, Enum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"
    WONT = "wont"


class RequirementSource(str, Enum):
    USER = "user"
    INFERRED = "inferred"
    FOUNDRY_IQ = "foundry_iq"
    WEB_SEARCH = "web_search"
    SYSTEM_DEFAULT = "system_default"


class RequirementCategory(str, Enum):
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    DATA_RESIDENCY = "data_residency"
    INTEGRATION = "integration"
    OBSERVABILITY = "observability"
    COST = "cost"
    DELIVERY = "delivery"
    OPERABILITY = "operability"
    SCALABILITY = "scalability"


class ArchitecturePatternType(str, Enum):
    REAL_TIME_STREAMING = "real_time_streaming"
    RAG_APPLICATION = "rag_application"
    EVENT_DRIVEN_INTEGRATION = "event_driven_integration"
    BATCH_ANALYTICS = "batch_analytics"
    MULTI_AGENT_WORKFLOW = "multi_agent_workflow"
    TRANSACTIONAL_SYSTEM = "transactional_system"
    MIGRATION_MODERNIZATION = "migration_modernization"
    IOT_INGESTION = "iot_ingestion"
    UNKNOWN = "unknown"


class OptionStatus(str, Enum):
    RECOMMENDED = "recommended"
    VIABLE = "viable"
    REJECTED = "rejected"
    NEEDS_VALIDATION = "needs_validation"


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


class WafPillar(str, Enum):
    RELIABILITY = "reliability"
    SECURITY = "security"
    COST_OPTIMIZATION = "cost_optimization"
    OPERATIONAL_EXCELLENCE = "operational_excellence"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ChangeType(str, Enum):
    REQUIREMENT_ADDED = "requirement_added"
    REQUIREMENT_UPDATED = "requirement_updated"
    REQUIREMENT_REMOVED = "requirement_removed"
    ASSUMPTION_VALIDATED = "assumption_validated"
    OPTION_OVERRIDDEN = "option_overridden"
    USER_OVERRIDE = "user_override"
    SYSTEM_RETRY = "system_retry"


class DiffType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class EvidenceAuditRecommendation(str, Enum):
    PROCEED = "proceed"
    REVIEW_FLAGGED_ITEMS = "review_flagged_items"
    PAUSE_AND_VALIDATE = "pause_and_validate"


class EvidenceQuality(str, Enum):
    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
```

---

## 6. Quality Gate Models

File: `src/archimedes/models/quality_gates.py`

```python
from __future__ import annotations

from pydantic import Field, model_validator

from .base import ArchimedesModel
from .enums import QualityGateStatus


class QualityGateCheck(ArchimedesModel):
    check_id: str
    description: str
    passed: bool = False
    severity: str = "warning"  # blocking | warning
    message: str | None = None


class QualityGateResult(ArchimedesModel):
    status: QualityGateStatus
    blocking_failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: list[QualityGateCheck] = Field(default_factory=list)
    user_override_allowed: bool = True

    @model_validator(mode="after")
    def validate_status_consistency(self):
        if self.blocking_failures and self.status != QualityGateStatus.FAILED:
            raise ValueError("Quality gate with blocking failures must have status='failed'.")
        if self.status == QualityGateStatus.FAILED and self.user_override_allowed:
            raise ValueError("Failed quality gate cannot allow user override.")
        return self
```

### Usage

```python
result = QualityGateResult(
    status="passed_with_warnings",
    warnings=["Data residency not specified; using default regional assumption."],
    user_override_allowed=True,
)
```

---

## 7. Session and Stage Execution Models

File: `src/archimedes/models/session.py`

```python
from __future__ import annotations

from datetime import datetime
from pydantic import Field, model_validator

from .base import ArchimedesModel, utc_now, new_id
from .enums import StageName, StageStatus
from .quality_gates import QualityGateResult


class StageExecution(ArchimedesModel):
    stage: StageName
    stage_run_id: str = Field(default_factory=lambda: new_id("stage_run"))
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = Field(default=0, ge=0)
    failure_reason: str | None = None
    base_version: int | None = Field(default=None, ge=0)
    target_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_timestamps(self):
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValueError("completed_at cannot be earlier than started_at.")
        if self.status == StageStatus.FAILED and not self.failure_reason:
            raise ValueError("failure_reason is required when status='failed'.")
        return self


class ArchitectureSession(ArchimedesModel):
    session_id: str = Field(default_factory=lambda: new_id("session"))
    title: str | None = None
    business_need: str
    current_stage: StageName = StageName.INTAKE
    last_successful_stage: StageName | None = None
    active_version: int = Field(default=0, ge=0)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user_id: str | None = None
    project_id: str | None = None

    stage_executions: dict[StageName, StageExecution] = Field(default_factory=dict)
    dependency_map: dict[str, list[StageName]] = Field(default_factory=dict)
    quality_gates: dict[StageName, QualityGateResult] = Field(default_factory=dict)
    detected_patterns: list[str] = Field(default_factory=list)

    latest_artifact_versions: dict[StageName, int] = Field(default_factory=dict)
    is_archived: bool = False

    @model_validator(mode="after")
    def ensure_current_stage_execution_exists(self):
        if self.current_stage not in self.stage_executions:
            self.stage_executions[self.current_stage] = StageExecution(stage=self.current_stage)
        return self
```

### Persistence Notes

- Stored in Cosmos DB container: `sessions`.
- Partition key: `/session_id`.
- This object should remain small and should reference artifacts by version, not embed full outputs.

---

## 8. Requirement Models

File: `src/archimedes/models/requirements.py`

```python
from __future__ import annotations

from pydantic import Field

from .base import ArchimedesModel, new_id
from .enums import RequirementCategory, RequirementPriority, RequirementSource


class RequirementItem(ArchimedesModel):
    requirement_id: str = Field(default_factory=lambda: new_id("req"))
    category: RequirementCategory
    description: str
    measurable_target: str | None = None
    priority: RequirementPriority = RequirementPriority.SHOULD
    source: RequirementSource = RequirementSource.USER
    rationale: str | None = None
    requires_validation: bool = False
    validated: bool = False
    related_claim_ids: list[str] = Field(default_factory=list)


class FunctionalRequirement(RequirementItem):
    category: RequirementCategory = RequirementCategory.FUNCTIONAL


class NonFunctionalRequirement(RequirementItem):
    pass


class ConstraintItem(ArchimedesModel):
    constraint_id: str = Field(default_factory=lambda: new_id("constraint"))
    description: str
    constraint_type: str  # platform | compliance | budget | timeline | organization | integration
    source: RequirementSource = RequirementSource.USER
    requires_validation: bool = False


class AssumptionItem(ArchimedesModel):
    assumption_id: str = Field(default_factory=lambda: new_id("assumption"))
    description: str
    source: RequirementSource = RequirementSource.INFERRED
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    requires_validation: bool = True
    validated: bool = False
    impact_if_wrong: list[str] = Field(default_factory=list)


class OpenQuestion(ArchimedesModel):
    question_id: str = Field(default_factory=lambda: new_id("question"))
    question: str
    reason: str | None = None
    impact_if_unanswered: list[str] = Field(default_factory=list)
    status: str = "open"  # open | answered | deferred


class RequirementSet(ArchimedesModel):
    functional: list[FunctionalRequirement] = Field(default_factory=list)
    non_functional: list[NonFunctionalRequirement] = Field(default_factory=list)
    constraints: list[ConstraintItem] = Field(default_factory=list)
    assumptions: list[AssumptionItem] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
```

### Validation Strategy

Do not enforce all requirement quality rules inside the models. Use the Quality Gate Service for stage-level checks such as:

- Scale defined.
- Security requirements identified.
- Compliance requirements checked.
- Data residency handled or warned.

---

## 9. Pattern Detection Models

File: `src/archimedes/models/patterns.py`

```python
from __future__ import annotations

from pydantic import Field

from .base import ArchimedesModel
from .enums import ArchitecturePatternType


class ArchitecturePatternCandidate(ArchimedesModel):
    pattern: ArchitecturePatternType
    confidence: float = Field(ge=0.0, le=1.0)
    detected_signals: list[str] = Field(default_factory=list)
    rationale: str | None = None


class ArchitecturePatternResult(ArchimedesModel):
    primary_pattern: ArchitecturePatternType
    secondary_patterns: list[ArchitecturePatternCandidate] = Field(default_factory=list)
    typical_pipeline: str | None = None
    azure_services_to_explore: list[str] = Field(default_factory=list)
    reference_architectures: list[str] = Field(default_factory=list)
    pattern_specific_nfrs: list[str] = Field(default_factory=list)
    detection_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
```

---

## 10. Architecture Options and Decision Models

File: `src/archimedes/models/options.py`

```python
from __future__ import annotations

from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id
from .enums import OptionStatus, Severity


class AzureServiceMapping(ArchimedesModel):
    component_name: str
    azure_service: str
    sku_hint: str | None = None
    region_assumption: str | None = None
    rationale: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class TradeoffScores(ArchimedesModel):
    cost: int = Field(ge=1, le=10)
    complexity: int = Field(ge=1, le=10)
    scalability: int = Field(ge=1, le=10)
    time_to_market: int = Field(ge=1, le=10)
    operational_burden: int = Field(ge=1, le=10)
    security: int | None = Field(default=None, ge=1, le=10)
    reliability: int | None = Field(default=None, ge=1, le=10)


class RiskItem(ArchimedesModel):
    risk_id: str = Field(default_factory=lambda: new_id("risk"))
    description: str
    severity: Severity = Severity.MEDIUM
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    impact: float | None = Field(default=None, ge=0.0, le=1.0)
    mitigation: str | None = None
    related_claim_ids: list[str] = Field(default_factory=list)


class ArchitectureOption(ArchimedesModel):
    option_id: str = Field(default_factory=lambda: new_id("option"))
    name: str
    summary: str
    status: OptionStatus = OptionStatus.VIABLE
    components: list[AzureServiceMapping] = Field(default_factory=list)
    tradeoff_scores: TradeoffScores
    risks: list[RiskItem] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    rejection_reason: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def rejected_requires_reason(self):
        if self.status == OptionStatus.REJECTED and not self.rejection_reason:
            raise ValueError("Rejected option must include rejection_reason.")
        return self


class ArchitectureOptionsResult(ArchimedesModel):
    options: list[ArchitectureOption]
    recommended_option_id: str | None = None
    evaluation_criteria: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_options(self):
        viable_count = sum(1 for o in self.options if o.status in {OptionStatus.VIABLE, OptionStatus.RECOMMENDED})
        rejected_count = sum(1 for o in self.options if o.status == OptionStatus.REJECTED)
        if viable_count < 2:
            raise ValueError("At least two viable/recommended options are required.")
        if rejected_count < 1:
            raise ValueError("At least one rejected option is required.")
        if self.recommended_option_id:
            ids = {o.option_id for o in self.options}
            if self.recommended_option_id not in ids:
                raise ValueError("recommended_option_id must match one of the options.")
        return self


class ArchitectureDecision(ArchimedesModel):
    decision_id: str = Field(default_factory=lambda: new_id("decision"))
    recommended_option_id: str
    rationale: str
    tradeoffs: list[str] = Field(default_factory=list)
    rejected_option_ids: list[str] = Field(default_factory=list)
    assumptions_to_validate: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    claim_ids: list[str] = Field(default_factory=list)
```

---

## 11. Claim and Evidence Models

File: `src/archimedes/models/claims.py`

```python
from __future__ import annotations

from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id
from .enums import ClaimType, StageName


class ClaimRecord(ArchimedesModel):
    claim_id: str = Field(default_factory=lambda: new_id("claim"))
    session_id: str
    claim: str
    type: ClaimType
    confidence: float = Field(ge=0.0, le=1.0)
    stage: StageName
    evidence_ids: list[str] = Field(default_factory=list)
    artifact_id: str | None = None
    requires_user_validation: bool = False
    validation_question: str | None = None

    @model_validator(mode="after")
    def fact_should_have_evidence(self):
        if self.type == ClaimType.FACT and not self.evidence_ids:
            raise ValueError("Fact claims must reference at least one evidence source.")
        if self.requires_user_validation and not self.validation_question:
            raise ValueError("validation_question is required when requires_user_validation=True.")
        return self
```

File: `src/archimedes/models/evidence.py`

```python
from __future__ import annotations

from datetime import datetime
from pydantic import Field, HttpUrl

from .base import ArchimedesModel, new_id, utc_now
from .enums import EvidenceRetrievalMethod, SourceFreshness, TrustLevel


class EvidenceSource(ArchimedesModel):
    evidence_id: str = Field(default_factory=lambda: new_id("evidence"))
    session_id: str
    source: str
    source_url: HttpUrl | None = None
    retrieved_via: EvidenceRetrievalMethod
    retrieved_at: datetime = Field(default_factory=utc_now)
    excerpt: str | None = None
    chunk_id: str | None = None

    kb_name: str | None = None
    kb_version: str | None = None
    source_document_version: str | None = None

    source_freshness: SourceFreshness = SourceFreshness.UNKNOWN
    trust_level: TrustLevel = TrustLevel.MEDIUM
    used_in_stages: list[str] = Field(default_factory=list)
```

### Claim/Evidence Rule

- A `ClaimRecord` says what Archimedes asserts.
- An `EvidenceSource` says where support came from.
- A `fact` claim must have at least one evidence source.
- `assumption` and `recommendation` claims may be evidence-informed, but they do not have to be directly cited the same way a factual claim does.

---

## 12. Artifact Models

File: `src/archimedes/models/artifacts.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import Field, model_validator

from .base import ArchimedesModel, FlexibleContentModel, new_id, utc_now
from .enums import StageName
from .quality_gates import QualityGateResult


class MermaidDiagram(FlexibleContentModel):
    diagram_id: str = Field(default_factory=lambda: new_id("diagram"))
    diagram_type: str  # system_context | container | data_flow | network | sequence
    title: str
    mermaid_source: str
    render_checked: bool = False
    render_errors: list[str] = Field(default_factory=list)


class AdrContent(FlexibleContentModel):
    title: str
    status: str = "proposed"
    context: str
    decision: str
    alternatives: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)


class HldContent(FlexibleContentModel):
    title: str
    summary: str
    diagrams: list[MermaidDiagram] = Field(default_factory=list)
    components: list[dict[str, Any]] = Field(default_factory=list)
    data_flows: list[dict[str, Any]] = Field(default_factory=list)
    security_zones: list[dict[str, Any]] = Field(default_factory=list)


class WafFinding(FlexibleContentModel):
    finding_id: str = Field(default_factory=lambda: new_id("waf_finding"))
    pillar: str
    severity: str
    finding: str
    recommendation: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class WafReviewContent(FlexibleContentModel):
    findings: list[WafFinding] = Field(default_factory=list)
    summary_by_pillar: dict[str, str] = Field(default_factory=dict)


class VersionedArtifact(ArchimedesModel):
    artifact_id: str = Field(default_factory=lambda: new_id("artifact"))
    session_id: str
    stage: StageName
    version: int = Field(ge=1)
    stage_run_id: str
    content: dict[str, Any]
    content_type: str = "json"  # json | markdown | mermaid | mixed
    full_content_uri: str | None = None
    quality_gate: QualityGateResult
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    created_by: str | None = "archimedes"
    change_trigger: str | None = None

    @model_validator(mode="after")
    def content_or_uri_required(self):
        if not self.content and not self.full_content_uri:
            raise ValueError("Either content or full_content_uri must be provided.")
        return self
```

---

## 13. Socrates Models

File: `src/archimedes/models/socrates.py`

```python
from __future__ import annotations

from datetime import datetime
from pydantic import Field

from .base import ArchimedesModel, new_id, utc_now
from .enums import PersonaName, SocratesDepth
from .quality_gates import QualityGateResult


class PersonaFinding(ArchimedesModel):
    finding_id: str = Field(default_factory=lambda: new_id("persona_finding"))
    persona: PersonaName
    target_option_id: str | None = None
    finding: str
    severity: str = "medium"
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class PersonaAnalysis(ArchimedesModel):
    persona: PersonaName
    summary: str
    findings: list[PersonaFinding] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SocraticSynthesis(ArchimedesModel):
    recommended_option_id: str | None = None
    ranked_option_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    blind_spots: list[str] = Field(default_factory=list)
    assumptions_to_validate: list[str] = Field(default_factory=list)
    premortem_scenarios: list[str] = Field(default_factory=list)
    hybrid_option_summary: str | None = None
    rationale: str


class SocraticReview(ArchimedesModel):
    review_id: str = Field(default_factory=lambda: new_id("socratic_review"))
    session_id: str
    stage_run_id: str
    depth: SocratesDepth = SocratesDepth.STANDARD
    persona_analyses: list[PersonaAnalysis] = Field(default_factory=list)
    cross_examination: str | None = None
    synthesis: SocraticSynthesis
    quality_gate: QualityGateResult
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
```

---

## 14. Evidence Audit Models

File: `src/archimedes/models/evidence_audit.py`

```python
from __future__ import annotations

from pydantic import Field

from .base import ArchimedesModel, new_id, utc_now
from .enums import EvidenceAuditRecommendation, EvidenceQuality, Severity, StageName


class EvidenceAuditFinding(ArchimedesModel):
    finding_id: str = Field(default_factory=lambda: new_id("audit_finding"))
    severity: Severity
    category: str  # unsupported_claim | irrelevant_citation | stale_source | contradiction | low_trust
    description: str
    claim_id: str | None = None
    evidence_id: str | None = None
    recommendation: str | None = None


class EvidenceAuditReport(ArchimedesModel):
    audit_id: str = Field(default_factory=lambda: new_id("evidence_audit"))
    session_id: str
    stage: StageName
    total_claims: int = Field(ge=0)
    facts_cited: int = Field(ge=0)
    recommendations_with_evidence: int = Field(ge=0)
    assumptions_unvalidated: int = Field(ge=0)
    findings: list[EvidenceAuditFinding] = Field(default_factory=list)
    overall_evidence_quality: EvidenceQuality
    recommendation: EvidenceAuditRecommendation
    created_at: datetime = Field(default_factory=utc_now)
```

---

## 15. Cost Models

File: `src/archimedes/models/cost.py`

```python
from __future__ import annotations

from pydantic import Field, model_validator

from .base import ArchimedesModel


class CostRange(ArchimedesModel):
    low: float = Field(ge=0)
    expected: float = Field(ge=0)
    high: float = Field(ge=0)
    currency: str = "USD"

    @model_validator(mode="after")
    def validate_order(self):
        if not (self.low <= self.expected <= self.high):
            raise ValueError("CostRange must satisfy low <= expected <= high.")
        return self


class ResourceSizing(ArchimedesModel):
    service: str
    sku: str | None = None
    quantity: int = Field(default=1, ge=0)
    region: str | None = None
    assumption: str
    monthly_cost: CostRange | None = None


class CostDriver(ArchimedesModel):
    service: str
    percentage_of_total: float = Field(ge=0.0, le=100.0)
    sensitivity: str


class CostEstimate(ArchimedesModel):
    assumptions: list[str] = Field(default_factory=list)
    resource_sizing: list[ResourceSizing] = Field(default_factory=list)
    pricing_source: str
    pricing_version: str
    monthly_estimate: CostRange
    annual_estimate: CostRange
    major_cost_drivers: list[CostDriver] = Field(default_factory=list)
    cost_sensitivity: str = "medium"  # low | medium | high
    scale_projections: dict[str, CostRange] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
```

---

## 16. Change, Dependency, and Diff Models

File: `src/archimedes/models/change.py`

```python
from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import Field

from .base import ArchimedesModel, new_id, utc_now
from .enums import ChangeType, StageName


class ChangeEvent(ArchimedesModel):
    change_event_id: str = Field(default_factory=lambda: new_id("change"))
    session_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    change_type: ChangeType
    changed_field: str
    old_value_summary: str | None = None
    new_value_summary: str | None = None
    impacted_stages: list[StageName] = Field(default_factory=list)
    stable_stages: list[StageName] = Field(default_factory=list)
    user_message: str | None = None


class DependencyImpactResult(ArchimedesModel):
    impact_id: str = Field(default_factory=lambda: new_id("impact"))
    session_id: str
    change_event_id: str
    impacted_stages: list[StageName] = Field(default_factory=list)
    stable_stages: list[StageName] = Field(default_factory=list)
    reason_by_stage: dict[StageName, str] = Field(default_factory=dict)
    rerun_required: bool = True
```

File: `src/archimedes/models/diffs.py`

```python
from __future__ import annotations

from typing import Any
from pydantic import Field

from .base import ArchimedesModel, new_id, utc_now
from .enums import DiffType, StageName


class FieldDiff(ArchimedesModel):
    field_path: str
    diff_type: DiffType
    before: Any | None = None
    after: Any | None = None
    summary: str | None = None


class ArtifactDiff(ArchimedesModel):
    diff_id: str = Field(default_factory=lambda: new_id("diff"))
    session_id: str
    stage: StageName
    before_version: int = Field(ge=1)
    after_version: int = Field(ge=1)
    change_event_id: str | None = None
    field_diffs: list[FieldDiff] = Field(default_factory=list)
    summary: str
    created_at: str | None = None
```

---

## 17. Stage Patch Models

File: `src/archimedes/models/patches.py`

```python
from __future__ import annotations

from typing import Any
from pydantic import Field, model_validator

from .base import ArchimedesModel, new_id
from .claims import ClaimRecord
from .evidence import EvidenceSource
from .enums import StageName
from .quality_gates import QualityGateResult, QualityGateStatus


class StagePatch(ArchimedesModel):
    patch_id: str = Field(default_factory=lambda: new_id("patch"))
    session_id: str
    stage: StageName
    stage_run_id: str
    base_version: int = Field(ge=0)
    target_version: int = Field(ge=1)
    idempotency_key: str
    patch_hash: str

    patch: dict[str, Any]
    claims: list[ClaimRecord] = Field(default_factory=list)
    evidence_sources: list[EvidenceSource] = Field(default_factory=list)
    quality_gate_result: QualityGateResult
    requires_user_input: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_versions_and_gate(self):
        if self.target_version <= self.base_version:
            raise ValueError("target_version must be greater than base_version.")
        if self.quality_gate_result.status == QualityGateStatus.FAILED:
            if not self.quality_gate_result.blocking_failures:
                raise ValueError("failed quality gate must include blocking_failures.")
        return self


class ApplyPatchResult(ArchimedesModel):
    applied: bool
    session_id: str
    stage: StageName
    version: int | None = None
    reason: str | None = None
    current_version: int | None = None
    patch_base_version: int | None = None
    action: str | None = None
```

### Idempotency Rule

The `idempotency_key` should be deterministic for one execution attempt:

```text
{session_id}:{stage}:{stage_run_id}:{patch_hash}
```

The `patch_hash` should be computed from canonical JSON serialization of the patch content.

---

## 18. API DTO Models

File: `src/archimedes/models/api.py`

These DTOs are intentionally lightweight. The complete endpoint list belongs in `05-api-contracts.md`.

```python
from __future__ import annotations

from pydantic import Field

from .base import ArchimedesModel
from .enums import SocratesDepth, StageName
from .session import ArchitectureSession
from .artifacts import VersionedArtifact
from .change import DependencyImpactResult
from .diffs import ArtifactDiff


class CreateSessionRequest(ArchimedesModel):
    business_need: str
    title: str | None = None
    user_id: str | None = None
    project_id: str | None = None


class CreateSessionResponse(ArchimedesModel):
    session: ArchitectureSession


class RunStageRequest(ArchimedesModel):
    stage: StageName
    socrates_depth: SocratesDepth = SocratesDepth.STANDARD
    force: bool = False


class RunStageResponse(ArchimedesModel):
    session_id: str
    stage: StageName
    stage_run_id: str
    status: str
    artifact: VersionedArtifact | None = None
    requires_user_input: list[str] = Field(default_factory=list)


class ChangeRequirementRequest(ArchimedesModel):
    changed_field: str
    new_value: str
    old_value: str | None = None
    user_message: str | None = None


class ChangeRequirementResponse(ArchimedesModel):
    session_id: str
    impact: DependencyImpactResult
    diffs: list[ArtifactDiff] = Field(default_factory=list)


class SessionStatusResponse(ArchimedesModel):
    session: ArchitectureSession
    latest_artifacts: list[VersionedArtifact] = Field(default_factory=list)
```

---

## 19. Validation Helpers

File: `src/archimedes/models/validators.py`

```python
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_patch_hash(patch: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(patch).encode("utf-8")).hexdigest()


def compute_idempotency_key(
    session_id: str,
    stage: str,
    stage_run_id: str,
    patch_hash: str,
) -> str:
    raw = f"{session_id}:{stage}:{stage_run_id}:{patch_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

---

## 20. Example: Requirements StagePatch

```python
from archimedes.models.enums import StageName, ClaimType, EvidenceRetrievalMethod
from archimedes.models.quality_gates import QualityGateResult
from archimedes.models.patches import StagePatch
from archimedes.models.requirements import RequirementSet, FunctionalRequirement, NonFunctionalRequirement
from archimedes.models.claims import ClaimRecord
from archimedes.models.evidence import EvidenceSource
from archimedes.models.validators import compute_patch_hash, compute_idempotency_key

session_id = "session_demo_001"
stage_run_id = "stage_run_requirements_001"

requirement_set = RequirementSet(
    functional=[
        FunctionalRequirement(
            description="Detect potentially fraudulent transactions in real time.",
            priority="must",
        )
    ],
    non_functional=[
        NonFunctionalRequirement(
            category="performance",
            description="Process 10K transactions per second.",
            measurable_target="10000 TPS",
            priority="must",
        )
    ],
)

patch_content = requirement_set.model_dump(mode="json")
patch_hash = compute_patch_hash(patch_content)

patch = StagePatch(
    session_id=session_id,
    stage=StageName.REQUIREMENTS_EXTRACTION,
    stage_run_id=stage_run_id,
    base_version=0,
    target_version=1,
    idempotency_key=compute_idempotency_key(session_id, "requirements_extraction", stage_run_id, patch_hash),
    patch_hash=patch_hash,
    patch=patch_content,
    claims=[],
    evidence_sources=[],
    quality_gate_result=QualityGateResult(
        status="passed_with_warnings",
        warnings=["Data residency requirement not provided."],
        user_override_allowed=True,
    ),
)
```

---

## 21. Model-to-Storage Mapping

| Model | Cosmos Container | Partition Key | Notes |
|---|---|---|---|
| `ArchitectureSession` | `sessions` | `/session_id` | Small active session summary. |
| `VersionedArtifact` | `artifacts` | `/session_id` | One document per stage per version. |
| `ClaimRecord` | `claims` | `/session_id` | Append-only logical claim ledger. |
| `EvidenceSource` | `evidence` | `/session_id` | Append-only evidence source ledger. |
| `ChangeEvent` | `changelog` | `/session_id` | Append-only change trail. |
| `DependencyImpactResult` | `changelog` or `impacts` | `/session_id` | Can be embedded in change event or stored separately. |
| `ArtifactDiff` | `artifacts` or `diffs` | `/session_id` | Store separately if diff history becomes important. |

The final Cosmos DB physical design is covered in `04-database-design.md`.

---

## 22. Implementation Notes

### 22.1 Strict vs Flexible Models

Use strict `ArchimedesModel` for:

- Session state.
- Stage execution state.
- Stage patches.
- Claims.
- Evidence.
- Quality gates.
- Change events.

Use `FlexibleContentModel` for:

- HLD generated content.
- WAF narrative content.
- Mermaid diagram metadata.
- Artifact-specific generated sections that may evolve.

### 22.2 Agent Output Handling

Agents should not return arbitrary prose to the State Manager. They should return either:

1. A typed `StagePatch`, or
2. Raw JSON that is immediately parsed into a `StagePatch`.

Invalid patches should fail fast before database writes.

### 22.3 Versioning

Rules:

- `base_version` is the latest version the agent used as input.
- `target_version` is the version the patch will create.
- `target_version` must be greater than `base_version`.
- The State Manager must reject stale patches when the latest artifact version is different from `base_version`.

### 22.4 Evidence and KB Versioning

Every `EvidenceSource` retrieved via Foundry IQ should include:

- `kb_name`
- `kb_version`
- `source_document_version`, where available
- `retrieved_at`
- `chunk_id`, where available

This allows future ADR/HLD outputs to be traced back to the knowledge snapshot used at the time.

### 22.5 Pydantic JSON Serialization

Use:

```python
model.model_dump(mode="json")
```

for Cosmos DB documents and API responses.

Use:

```python
ModelClass.model_validate(payload)
```

for parsing agent/tool/API payloads back into typed models.

---

## 23. Open Items for Later Documents

The following items are intentionally deferred:

| Topic | Document |
|---|---|
| Cosmos DB indexing, TTL, throughput, and optimistic concurrency implementation | `04-database-design.md` |
| Exact API endpoint list and request/response mapping | `05-api-contracts.md` |
| Stage transition engine and quality gate execution rules | `06-stage-pipeline.md` |
| Full system prompts for all routines | `07-agent-specifications.md` |
| Socrates WorkflowBuilder code and executor definitions | `08-socrates-engine.md` |
| Function tool implementation details | `09-tool-specifications.md` |
| Evidence Auditor prompt and audit algorithm | `11-evidence-and-claims.md` |

---

## 24. References

- Latest Archimedes v2.2 architecture spec supplied in conversation.
- `01-archimedes-hld.md`
- `02-domain-models.md`
- Pydantic v2 documentation for models, fields, validators, and configuration.

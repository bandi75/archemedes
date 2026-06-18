import type { QualityGateStatus } from "@/components/shared/quality-gate-badge";
import type { StatusBadgeVariant } from "@/components/shared/status-badge";
import type {
  ArtifactPackageView,
  ChangeImpactView,
  EvidenceView,
  OptionsView,
  PatternsView,
  PipelineView,
  RequirementsView,
  SocratesView,
} from "@/lib/view-models";

export const mockSessions: Array<{
  id: string;
  name: string;
  stage: string;
  qualityGate: QualityGateStatus;
  updatedAt: string;
}> = [
  {
    id: "session-fraud-100k",
    name: "Fintech fraud platform",
    stage: "Change Impact",
    qualityGate: "passed_with_warnings",
    updatedAt: "10 min ago",
  },
  {
    id: "session-claims-modernization",
    name: "Claims modernization",
    stage: "Socrates",
    qualityGate: "passed",
    updatedAt: "42 min ago",
  },
  {
    id: "session-iot-edge",
    name: "Factory telemetry edge",
    stage: "Evidence",
    qualityGate: "passed",
    updatedAt: "Yesterday",
  },
];

export const mockPipelineStages: Array<{
  id: string;
  name: string;
  summary: string;
  status: string;
  statusVariant: StatusBadgeVariant;
}> = [
  {
    id: "requirements",
    name: "Requirements Review",
    summary: "NFRs, assumptions, and compliance constraints",
    status: "Ready",
    statusVariant: "success",
  },
  {
    id: "socrates",
    name: "Socrates Reasoning",
    summary: "Five personas and synthesizer output",
    status: "Mocked",
    statusVariant: "purple",
  },
  {
    id: "evidence",
    name: "Evidence Explorer",
    summary: "Claims, citations, freshness, and trust",
    status: "Mocked",
    statusVariant: "teal",
  },
  {
    id: "impact",
    name: "Change Impact",
    summary: "Impacted stages, rerun plan, and diffs",
    status: "Skeleton",
    statusVariant: "info",
  },
];

export const mockPipelineView: PipelineView = {
  session_id: "session-demo",
  session: {
    session_id: "session-demo",
    title: "Fintech fraud platform",
    business_need: "Modernize real-time fraud detection for card transactions at 100K TPS.",
    mode: "mock",
  },
  current_stage: "socratic_review",
  stages: [
    { stage: "requirements_extraction", label: "Requirements", status: "completed", summary: "NFRs, PCI-DSS constraints, and throughput assumptions captured.", artifact_version: 1, last_updated_at: "2026-06-18T08:58:00Z", quality_gate: { status: "passed" } },
    { stage: "pattern_detection", label: "Pattern Detection", status: "completed", summary: "Real-time streaming and event-driven architecture detected.", artifact_version: 1, last_updated_at: "2026-06-18T09:00:00Z", quality_gate: { status: "passed" } },
    { stage: "options_generation", label: "Options", status: "completed", summary: "Three Azure architecture options generated and scored.", artifact_version: 1, last_updated_at: "2026-06-18T09:01:00Z", quality_gate: { status: "passed_with_warnings" } },
    { stage: "socratic_review", label: "Socratic Review", status: "running", summary: "Five personas are reviewing operability, cost, security, delivery, and failure modes.", artifact_version: 1, last_updated_at: "2026-06-18T09:03:00Z", quality_gate: { status: "passed_with_warnings" } },
    { stage: "evidence_audit_checkpoint", label: "Evidence Checkpoint", status: "pending", summary: "Evidence coverage will be audited after Socrates synthesis.", artifact_version: null, last_updated_at: "2026-06-18T09:03:00Z", quality_gate: null },
  ],
  selected_stage: { stage: "socratic_review", label: "Socratic Review", status: "running", summary: "Five personas are reviewing the architecture options.", artifact_version: 1, last_updated_at: "2026-06-18T09:03:00Z", quality_gate: { status: "passed_with_warnings" } },
  recent_events: [
    { event_id: "evt-1", event_type: "stage_completed", stage: "options_generation", message: "Options generated with 3 candidates.", timestamp: "2026-06-18T09:00:00Z", percent: 50 },
    { event_id: "evt-2", event_type: "socrates_persona_completed", stage: "socratic_review", message: "Security Architect completed PCI-DSS scope review.", timestamp: "2026-06-18T09:02:00Z", percent: 70 },
    { event_id: "evt-3", event_type: "stage_progress", stage: "socratic_review", message: "FinOps Lead reviewing cost growth at 100K TPS.", timestamp: "2026-06-18T09:03:00Z", percent: 80 },
  ],
};

export const mockSocratesView: SocratesView = {
  session_id: "session-demo",
  decision_under_review: {
    title: "Managed Azure streaming architecture",
    summary: "Event Hubs, Stream Analytics, Azure Functions, Cosmos DB, and Azure Monitor for real-time fraud scoring.",
  },
  synthesis: {
    recommended_decision: "Proceed with the managed streaming option, with explicit PCI scope controls and load-test gates.",
    confidence: 0.86,
    blind_spots: ["Cardholder data boundary needs validation.", "Cross-region failover runbook is not yet tested."],
    premortem: ["Partition hot spots create latency spikes during fraud campaigns.", "Cost grows sharply if retention and replay windows are oversized."],
  },
  personas: [
    { persona: "Security Architect", summary: "Tokenization boundary and private networking need to be explicit before ADR approval." },
    { persona: "SRE/Ops Lead", summary: "Observability and partition-pressure alerts are mandatory for launch readiness." },
    { persona: "FinOps Lead", summary: "Throughput and retention assumptions dominate monthly cost variance." },
    { persona: "Delivery Lead", summary: "Managed services keep the first release achievable within the hackathon/demo timeline." },
    { persona: "Devil's Advocate", summary: "Replay, poison events, and model rollback paths are still under-specified." },
  ],
};

export const mockRequirementsView: RequirementsView = {
  session_id: "session-demo",
  summary: "Real-time fraud platform for fintech transaction scoring with PCI-DSS constraints and 99.95% availability.",
  functional_requirements: [
    { id: "fr-1", description: "Ingest transaction events in real time.", priority: "must" },
    { id: "fr-2", description: "Score transactions and publish fraud decisions.", priority: "must" },
    { id: "fr-3", description: "Expose investigation events for downstream review.", priority: "should" },
  ],
  non_functional_requirements: [
    { id: "nfr-1", metric: "Throughput", target: "10K TPS initial, 100K TPS change scenario" },
    { id: "nfr-2", metric: "Availability", target: "99.95%" },
    { id: "nfr-3", metric: "Compliance", target: "PCI-DSS scoped controls" },
  ],
  constraints: [
    { id: "c-1", description: "Azure-first managed services preferred." },
    { id: "c-2", description: "No raw cardholder data in analytics stores." },
  ],
  assumptions: [
    { claim_id: "claim-2", claim: "PCI scope is limited to tokenized transaction events.", validation_question: "Confirm tokenization boundary.", requires_user_validation: true },
  ],
  open_questions: ["What is the required decision latency?", "How long must raw events be retained?"],
  quality_gate: { status: "passed_with_warnings" },
};

export const mockPatternsView: PatternsView = {
  session_id: "session-demo",
  primary_patterns: ["real_time_streaming", "event_driven_architecture"],
  signals: ["10K TPS", "fraud scoring", "low-latency decisions", "PCI-DSS"],
  recommended_services: ["Azure Event Hubs", "Azure Stream Analytics", "Azure Functions", "Azure Cosmos DB", "Azure Monitor"],
  pattern_specific_nfrs: ["Partition strategy", "Replay window", "Backpressure handling", "Poison event isolation"],
  quality_gate: { status: "passed" },
};

export const mockOptionsView: OptionsView = {
  session_id: "session-demo",
  selected_option_id: "option-managed-streaming",
  options: [
    {
      option_id: "option-managed-streaming",
      name: "Managed Azure Streaming",
      summary: "Event Hubs, Stream Analytics, Functions, Cosmos DB, and Monitor.",
      scores: { cost: 7, complexity: 8, scalability: 8, delivery: 9 },
      risks: ["Partition hot spots", "PCI boundary ambiguity"],
    },
    {
      option_id: "option-aks-streaming",
      name: "AKS Stream Processors",
      summary: "Custom scoring workers on AKS with Event Hubs and Cosmos DB.",
      scores: { cost: 5, complexity: 5, scalability: 9, delivery: 5 },
      risks: ["Higher operational burden", "Longer delivery path"],
    },
  ],
  rejected_options: [{ name: "Single VM queue processor", reason: "Weak availability and scale posture." }],
  tradeoff_matrix: [
    { criterion: "Time to market", best: "Managed Azure Streaming" },
    { criterion: "Operational control", best: "AKS Stream Processors" },
  ],
  cost_estimate: { expected_monthly_usd: 8400, sensitivity: "high" },
  quality_gate: { status: "passed_with_warnings" },
};

export const mockEvidenceView: EvidenceView = {
  session_id: "session-demo",
  coverage: {
    total_claims: 12,
    claims_with_evidence: 10,
    evidence_sources: 7,
    trust_breakdown: { high: 5, medium: 2 },
    open_assumptions: 2,
  },
  claims: [
    { claim_id: "claim-1", claim: "Event Hubs is viable for high-throughput event ingestion.", type: "fact", confidence: 0.9, requires_user_validation: false },
    { claim_id: "claim-2", claim: "PCI scope is limited to tokenized transaction events.", type: "assumption", confidence: 0.7, requires_user_validation: true },
    { claim_id: "claim-3", claim: "Cosmos DB can serve low-latency fraud decisions with proper partitioning.", type: "recommendation", confidence: 0.82, requires_user_validation: false },
  ],
  evidence: [
    { evidence_id: "ev-1", source: "Azure Event Hubs documentation", trust_level: "high", source_freshness: "current", excerpt: "Event Hubs supports large-scale event ingestion patterns." },
    { evidence_id: "ev-2", source: "Azure Cosmos DB partitioning overview", trust_level: "high", source_freshness: "current", excerpt: "Partition key design determines scale and workload distribution." },
  ],
};

export const mockArtifactPackageView: ArtifactPackageView = {
  session_id: "session-demo",
  package_status: "ready",
  render_status: { status: "passed", warnings: [] },
  artifacts: [
    { stage: "requirements_extraction", title: "Requirements", summary: "10K TPS, PCI-DSS, 99.95% availability, low-latency scoring.", version: 1, quality_gate: { status: "passed" } },
    { stage: "socratic_review", title: "Socrates Brief", summary: "Persona review recommends managed streaming with guardrails.", version: 1, quality_gate: { status: "passed_with_warnings" } },
    { stage: "adr_generation", title: "ADR-001", summary: "Use managed Azure streaming architecture.", version: 1, quality_gate: { status: "passed" } },
    { stage: "hld_generation", title: "HLD", summary: "Mermaid system context and data-flow diagrams are render-ready.", version: 1, quality_gate: { status: "passed" } },
    { stage: "mini_waf_review", title: "Mini WAF Review", summary: "Reliability and security findings require owner follow-up.", version: 1, quality_gate: { status: "passed_with_warnings" } },
  ],
};

export const mockChangeImpactView: ChangeImpactView = {
  session_id: "session-demo",
  change_event: { change_event_id: "change-demo", changed_field: "scale", new_value_summary: "Increase to 100K TPS and active-active regions" },
  impact: {
    impacted_stages: ["options_generation", "socratic_review", "adr_generation", "hld_generation", "mini_waf_review", "final_evidence_audit"],
    stable_stages: ["intake", "requirements_extraction", "pattern_detection"],
    ordered_stages: ["options_generation", "socratic_review", "adr_generation", "hld_generation", "mini_waf_review", "final_evidence_audit"],
  },
  rerun_plan: [
    { stage: "options_generation", label: "Options", status: "ready_to_rerun" },
    { stage: "socratic_review", label: "Socratic Review", status: "ready_to_rerun" },
    { stage: "hld_generation", label: "HLD", status: "ready_to_rerun" },
  ],
  diffs: [],
};

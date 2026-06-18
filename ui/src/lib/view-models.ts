import type { QualityGateStatus } from "@/components/shared/quality-gate-badge";
import type { StatusBadgeVariant } from "@/components/shared/status-badge";

export type StageRow = {
  stage: string;
  label: string;
  status: string;
  summary: string;
  artifact_version?: number | null;
  quality_gate?: { status: QualityGateStatus } | null;
};

export type SessionEvent = {
  event_id: string;
  event_type: string;
  stage?: string | null;
  message: string;
  timestamp: string;
  percent?: number | null;
};

export type PipelineView = {
  session_id: string;
  current_stage: string;
  stages: StageRow[];
  selected_stage: StageRow;
  recent_events: SessionEvent[];
};

export type SocratesView = {
  session_id: string;
  decision_under_review: { title: string; summary: string };
  synthesis: {
    recommended_decision: string;
    confidence: number;
    blind_spots: string[];
    premortem: string[] | string;
  };
  personas: Array<{ persona?: string; persona_name?: string; summary?: string; findings?: unknown[] }>;
};

export type EvidenceView = {
  session_id: string;
  coverage: {
    total_claims: number;
    claims_with_evidence: number;
    evidence_sources: number;
    trust_breakdown: Record<string, number>;
    open_assumptions: number;
  };
  claims: Array<{ claim_id: string; claim: string; type: string; confidence: number; requires_user_validation: boolean }>;
  evidence: Array<{ evidence_id: string; source: string; trust_level: string; source_freshness: string; excerpt?: string | null }>;
};

export type ArtifactPackageView = {
  session_id: string;
  package_status: string;
  render_status: { status: string; warnings: string[] };
  artifacts: Array<{
    stage: string;
    label?: string;
    title?: string;
    summary: string;
    version?: number | null;
    quality_gate?: { status: QualityGateStatus } | null;
  }>;
};

export type ChangeImpactView = {
  session_id: string;
  change_event: { change_event_id: string; changed_field: string; new_value_summary?: string | null };
  impact: { impacted_stages: string[]; stable_stages: string[]; ordered_stages: string[] };
  rerun_plan: Array<{ stage: string; label: string; status: string }>;
  diffs: unknown[];
};

export type RequirementsView = {
  session_id: string;
  summary: string;
  functional_requirements: Array<Record<string, unknown>>;
  non_functional_requirements: Array<Record<string, unknown>>;
  constraints: Array<Record<string, unknown>>;
  assumptions: Array<{ claim_id: string; claim: string; validation_question?: string | null; requires_user_validation?: boolean }>;
  open_questions: string[];
  quality_gate?: { status: QualityGateStatus } | null;
};

export type PatternsView = {
  session_id: string;
  primary_patterns: Array<string | Record<string, unknown>>;
  signals: Array<string | Record<string, unknown>>;
  recommended_services: string[];
  pattern_specific_nfrs: string[];
  quality_gate?: { status: QualityGateStatus } | null;
};

export type OptionsView = {
  session_id: string;
  options: Array<Record<string, unknown>>;
  rejected_options: Array<Record<string, unknown>>;
  tradeoff_matrix: Array<Record<string, unknown>>;
  cost_estimate?: Record<string, unknown> | null;
  selected_option_id?: string | null;
  quality_gate?: { status: QualityGateStatus } | null;
};

export type ArtifactListView = {
  items: Array<{
    artifact_id: string;
    stage: string;
    version: number;
    content: Record<string, unknown>;
    quality_gate: { status: QualityGateStatus };
    created_at: string;
  }>;
};

export type PipelineStageMock = {
  id: string;
  name: string;
  summary: string;
  status: string;
  statusVariant: StatusBadgeVariant;
};

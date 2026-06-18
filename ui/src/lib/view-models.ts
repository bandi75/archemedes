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

export type PipelineStageMock = {
  id: string;
  name: string;
  summary: string;
  status: string;
  statusVariant: StatusBadgeVariant;
};

import type {
  ArtifactListView,
  ArtifactPackageView,
  ChangeImpactView,
  EvidenceView,
  OptionsView,
  PatternsView,
  PipelineView,
  RequirementsView,
  SocratesView,
} from "@/lib/view-models";

const API_URL = process.env.NEXT_PUBLIC_ARCHIMEDES_API_URL ?? "http://localhost:8000/api/v1";

type SessionListResponse = {
  items: Array<{
    session_id: string;
    title?: string | null;
    current_stage?: string | null;
    created_at?: string;
  }>;
  total: number;
};

async function getJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export function getPipelineView(sessionId = "default"): Promise<PipelineView> {
  return getJson(`/sessions/${sessionId}/pipeline/view`, {
    session_id: sessionId,
    title: "",
    current_stage: "",
    pipeline: [],
    stages: [],
    selected_stage: { stage: "", status: "", label: "", order: 0 },
    recent_events: [],
  } as unknown as PipelineView);
}

export async function getActivePipelineView(sessionId?: string): Promise<PipelineView> {
  const resolvedSessionId = sessionId ?? await getLatestSessionId();
  if (!resolvedSessionId) {
    return {
      session_id: "",
      title: "",
      current_stage: "",
      pipeline: [],
      stages: [],
      selected_stage: { stage: "", status: "", label: "", order: 0 },
      recent_events: [],
    } as unknown as PipelineView;
  }
  return getPipelineView(resolvedSessionId);
}

async function getLatestSessionId(): Promise<string | null> {
  try {
    const response = await fetch(`${API_URL}/sessions`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    const payload = (await response.json()) as SessionListResponse;
    return payload.items[0]?.session_id ?? null;
  } catch {
    return null;
  }
}

export function getSocratesView(sessionId = "default"): Promise<SocratesView> {
  return getJson(`/sessions/${sessionId}/socrates/view`, {
    session_id: sessionId,
    decision_under_review: { title: "", summary: "" },
    synthesis: {
      recommended_decision: "",
      confidence: 0,
      blind_spots: [],
      premortem: [],
    },
    personas: [],
  } as SocratesView);
}

export function getRequirementsView(sessionId = "default"): Promise<RequirementsView> {
  return getJson(`/sessions/${sessionId}/requirements/view`, {
    session_id: sessionId,
    summary: "",
    functional_requirements: [],
    non_functional_requirements: [],
    constraints: [],
    assumptions: [],
    open_questions: [],
  } as RequirementsView);
}

export function getPatternsView(sessionId = "default"): Promise<PatternsView> {
  return getJson(`/sessions/${sessionId}/patterns/view`, {
    session_id: sessionId,
    primary_patterns: [],
    signals: [],
    recommended_services: [],
    pattern_specific_nfrs: [],
  } as PatternsView);
}

export function getOptionsView(sessionId = "default"): Promise<OptionsView> {
  return getJson(`/sessions/${sessionId}/options/view`, {
    session_id: sessionId,
    options: [],
    rejected_options: [],
    tradeoff_matrix: [],
  } as OptionsView);
}

export function getEvidenceView(sessionId = "default"): Promise<EvidenceView> {
  return getJson(`/sessions/${sessionId}/evidence/view`, {
    session_id: sessionId,
    coverage: {
      total_claims: 0,
      claims_with_evidence: 0,
      evidence_sources: 0,
      trust_breakdown: {},
      open_assumptions: 0,
    },
    claims: [],
    evidence: [],
  } as EvidenceView);
}

export function getArtifactPackageView(sessionId = "default"): Promise<ArtifactPackageView> {
  return getJson(`/sessions/${sessionId}/artifacts/package-view`, {
    session_id: sessionId,
    package_status: "unknown",
    render_status: { status: "unknown", warnings: [] },
    artifacts: [],
  } as ArtifactPackageView);
}

export function getChangeImpactView(
  sessionId = "default",
  changeEventId = "default",
): Promise<ChangeImpactView> {
  return getJson(`/sessions/${sessionId}/changes/${changeEventId}/impact-view`, {
    session_id: sessionId,
    change_event: { change_event_id: changeEventId, changed_field: "" },
    impact: { impacted_stages: [], stable_stages: [], ordered_stages: [] },
    rerun_plan: [],
    diffs: [],
  } as ChangeImpactView);
}

export function getArtifactHistory(sessionId = "default"): Promise<ArtifactListView> {
  return getJson(`/sessions/${sessionId}/artifacts`, { items: [], total: 0 } as unknown as ArtifactListView);
}
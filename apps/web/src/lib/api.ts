import {
  mockArtifactPackageView,
  mockChangeImpactView,
  mockEvidenceView,
  mockOptionsView,
  mockPatternsView,
  mockPipelineView,
  mockRequirementsView,
  mockSocratesView,
} from "@/lib/mock-data";
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
const MOCK_DATA = process.env.NEXT_PUBLIC_ARCHIMEDES_MOCK_DATA === "true";
export const DEFAULT_SESSION_ID = "session-demo";
export const DEFAULT_CHANGE_EVENT_ID = "change-demo";

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
  if (MOCK_DATA) {
    return fallback;
  }
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

export function getPipelineView(sessionId = DEFAULT_SESSION_ID): Promise<PipelineView> {
  return getJson(`/sessions/${sessionId}/pipeline/view`, mockPipelineView);
}

export async function getActivePipelineView(sessionId?: string): Promise<PipelineView> {
  if (MOCK_DATA) {
    return mockPipelineView;
  }
  const resolvedSessionId = sessionId ?? await getLatestSessionId();
  if (!resolvedSessionId) {
    return mockPipelineView;
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

export function getSocratesView(sessionId = DEFAULT_SESSION_ID): Promise<SocratesView> {
  return getJson(`/sessions/${sessionId}/socrates/view`, mockSocratesView);
}

export function getRequirementsView(sessionId = DEFAULT_SESSION_ID): Promise<RequirementsView> {
  return getJson(`/sessions/${sessionId}/requirements/view`, mockRequirementsView);
}

export function getPatternsView(sessionId = DEFAULT_SESSION_ID): Promise<PatternsView> {
  return getJson(`/sessions/${sessionId}/patterns/view`, mockPatternsView);
}

export function getOptionsView(sessionId = DEFAULT_SESSION_ID): Promise<OptionsView> {
  return getJson(`/sessions/${sessionId}/options/view`, mockOptionsView);
}

export function getEvidenceView(sessionId = DEFAULT_SESSION_ID): Promise<EvidenceView> {
  return getJson(`/sessions/${sessionId}/evidence/view`, mockEvidenceView);
}

export function getArtifactPackageView(sessionId = DEFAULT_SESSION_ID): Promise<ArtifactPackageView> {
  return getJson(`/sessions/${sessionId}/artifacts/package-view`, mockArtifactPackageView);
}

export function getChangeImpactView(
  sessionId = DEFAULT_SESSION_ID,
  changeEventId = DEFAULT_CHANGE_EVENT_ID,
): Promise<ChangeImpactView> {
  return getJson(`/sessions/${sessionId}/changes/${changeEventId}/impact-view`, mockChangeImpactView);
}

export function getArtifactHistory(sessionId = DEFAULT_SESSION_ID): Promise<ArtifactListView> {
  return getJson(`/sessions/${sessionId}/artifacts`, { items: [] });
}

import type { QualityGateStatus } from "@/components/shared/quality-gate-badge";
import type { StatusBadgeVariant } from "@/components/shared/status-badge";

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

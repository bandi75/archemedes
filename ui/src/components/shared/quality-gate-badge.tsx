import { StatusBadge } from "@/components/shared/status-badge";

export type QualityGateStatus = "passed" | "passed_with_warnings" | "failed";

type QualityGateBadgeProps = {
  status: QualityGateStatus;
};

const labels: Record<QualityGateStatus, string> = {
  passed: "Gate passed",
  passed_with_warnings: "Gate warnings",
  failed: "Gate failed",
};

const variants: Record<QualityGateStatus, "success" | "warning" | "danger"> = {
  passed: "success",
  passed_with_warnings: "warning",
  failed: "danger",
};

export function QualityGateBadge({ status }: QualityGateBadgeProps) {
  return <StatusBadge variant={variants[status]}>{labels[status]}</StatusBadge>;
}

import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { StatusBadge } from "@/components/shared/status-badge";
import type { StageRow } from "@/lib/view-models";

export function StageList({ stages }: { stages: StageRow[] }) {
  return (
    <div className="rounded-lg border border-border bg-panel shadow-panel">
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-base font-semibold text-ink">Pipeline stages</h2>
        <p className="mt-1 text-sm text-ink-muted">Screen-ready stage status and gate state.</p>
      </div>
      <div className="divide-y divide-border">
        {stages.map((stage) => (
          <article key={stage.stage} className="grid gap-3 px-5 py-4 md:grid-cols-[180px_minmax(0,1fr)_auto] md:items-center">
            <div>
              <p className="text-sm font-semibold text-ink">{stage.label}</p>
              <p className="text-xs text-ink-subtle">v{stage.artifact_version ?? "-"}</p>
            </div>
            <p className="text-sm text-ink-muted">{stage.summary}</p>
            <div className="flex flex-wrap gap-2">
              <StatusBadge variant={stage.status === "completed" ? "success" : stage.status === "running" ? "info" : "neutral"}>
                {stage.status}
              </StatusBadge>
              {stage.quality_gate ? <QualityGateBadge status={stage.quality_gate.status} /> : null}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

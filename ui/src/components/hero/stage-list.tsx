import Link from "next/link";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { StatusBadge } from "@/components/shared/status-badge";
import type { StageRow } from "@/lib/view-models";

const stageActions: Record<string, { href: string; label: string }> = {
  intake: { href: "/intake", label: "Refine" },
  requirements_extraction: { href: "/requirements", label: "Review" },
  pattern_detection: { href: "/patterns", label: "Explore" },
  options_generation: { href: "/options", label: "Compare" },
  socratic_review: { href: "/socrates", label: "Watch" },
  evidence_audit_checkpoint: { href: "/evidence", label: "Inspect" },
  adr_generation: { href: "/artifacts", label: "View" },
  hld_generation: { href: "/diagrams", label: "View diagram" },
  mini_waf_review: { href: "/artifacts", label: "Review" },
  final_evidence_audit: { href: "/evidence", label: "Audit" },
  rereasoning: { href: "/changes", label: "Impact" },
};

function formatUpdatedAt(value?: string | null) {
  if (!value) {
    return "Not started";
  }
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function StageList({ stages }: { stages: StageRow[] }) {
  return (
    <div className="rounded-lg border border-border bg-panel shadow-panel">
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-base font-semibold text-ink">Pipeline stages</h2>
        <p className="mt-1 text-sm text-ink-muted">Session lifecycle control with direct links into each stage workspace.</p>
      </div>
      <div className="divide-y divide-border">
        {stages.map((stage) => {
          const action = stageActions[stage.stage] ?? { href: "/artifacts", label: "Open" };
          const isUnavailable = stage.status === "pending" && !stage.artifact_version;
          return (
            <article key={stage.stage} className="grid gap-3 px-5 py-4 md:grid-cols-[190px_minmax(0,1fr)_auto] md:items-center">
              <div>
                <p className="text-sm font-semibold text-ink">{stage.label}</p>
                <p className="text-xs text-ink-subtle">v{stage.artifact_version ?? "-"} | {formatUpdatedAt(stage.last_updated_at)}</p>
              </div>
              <p className="text-sm text-ink-muted">{stage.summary}</p>
              <div className="flex flex-wrap items-center justify-start gap-2 md:justify-end">
                <StatusBadge variant={stage.status === "completed" ? "success" : stage.status === "running" ? "info" : "neutral"}>
                  {stage.status}
                </StatusBadge>
                {stage.quality_gate ? <QualityGateBadge status={stage.quality_gate.status} /> : null}
                {isUnavailable ? (
                  <span className="rounded-md border border-border px-3 py-1.5 text-xs font-semibold text-ink-subtle">Unavailable</span>
                ) : (
                  <Link className="rounded-md bg-ink px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-accent" href={action.href}>
                    {action.label}
                  </Link>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

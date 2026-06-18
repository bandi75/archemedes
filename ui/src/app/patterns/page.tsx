import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { StatusBadge } from "@/components/shared/status-badge";
import { getPatternsView } from "@/lib/api";

export default async function PatternsPage() {
  const view = await getPatternsView();

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Patterns"]}
          title="Pattern Explorer"
          description="Detected architecture patterns, signals, and service directions for downstream optioning."
          badges={[{ label: "Pattern map", variant: "info" }]}
        />
        {view.quality_gate ? <QualityGateBadge status={view.quality_gate.status} /> : null}
        <section className="grid gap-5 lg:grid-cols-2">
          <TokenPanel title="Primary patterns" items={view.primary_patterns.map(String)} variant="purple" />
          <TokenPanel title="Detected signals" items={view.signals.map(String)} variant="teal" />
          <TokenPanel title="Azure services to explore" items={view.recommended_services} variant="info" />
          <TokenPanel title="Pattern-specific NFRs" items={view.pattern_specific_nfrs} variant="warning" />
        </section>
      </div>
    </AppShell>
  );
}

function TokenPanel({ title, items, variant }: { title: string; items: string[]; variant: "purple" | "teal" | "info" | "warning" }) {
  return (
    <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <div className="mt-4 flex flex-wrap gap-2">
        {items.map((item) => (
          <StatusBadge key={item} variant={variant}>{item}</StatusBadge>
        ))}
      </div>
    </div>
  );
}

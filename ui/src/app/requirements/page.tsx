import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { StatusBadge } from "@/components/shared/status-badge";
import { getRequirementsView } from "@/lib/api";

export default async function RequirementsPage() {
  const view = await getRequirementsView();

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Requirements"]}
          title="Requirements Review"
          description={view.summary}
          badges={[{ label: "Review ready", variant: "teal" }]}
        />
        {view.quality_gate ? <QualityGateBadge status={view.quality_gate.status} /> : null}
        <section className="grid gap-5 lg:grid-cols-2">
          <RequirementPanel title="Functional requirements" items={view.functional_requirements} />
          <RequirementPanel title="Non-functional requirements" items={view.non_functional_requirements} />
          <RequirementPanel title="Constraints" items={view.constraints} />
          <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
            <h2 className="text-base font-semibold text-ink">Assumptions</h2>
            <div className="mt-4 space-y-3">
              {view.assumptions.map((assumption) => (
                <div key={assumption.claim_id} className="rounded-md border border-border bg-surface p-3">
                  <p className="text-sm font-medium text-ink">{assumption.claim}</p>
                  <p className="mt-1 text-xs text-ink-muted">{assumption.validation_question ?? "Awaiting validation."}</p>
                  <div className="mt-2"><StatusBadge variant="warning">Needs validation</StatusBadge></div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function RequirementPanel({ title, items }: { title: string; items: Array<Record<string, unknown>> }) {
  return (
    <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <div className="mt-4 space-y-3">
        {items.map((item, index) => (
          <div key={String(item.id ?? index)} className="rounded-md border border-border bg-surface p-3 text-sm text-ink-muted">
            {String(item.description ?? item.metric ?? item.target ?? JSON.stringify(item))}
          </div>
        ))}
      </div>
    </div>
  );
}

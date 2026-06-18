import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { StatusBadge } from "@/components/shared/status-badge";
import { getOptionsView } from "@/lib/api";

export default async function OptionsPage() {
  const view = await getOptionsView();

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Options"]}
          title="Architecture Options Board"
          description="Option cards, tradeoff signals, and selected recommendation context."
          badges={[{ label: view.selected_option_id ?? "No selection", variant: "info" }]}
        />
        {view.quality_gate ? <QualityGateBadge status={view.quality_gate.status} /> : null}
        <section className="grid gap-5 lg:grid-cols-2">
          {view.options.map((option, index) => (
            <article key={String(option.option_id ?? index)} className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-lg font-semibold text-ink">{String(option.name ?? `Option ${index + 1}`)}</h2>
                {option.option_id === view.selected_option_id ? <StatusBadge variant="success">Selected</StatusBadge> : null}
              </div>
              <p className="mt-3 text-sm leading-6 text-ink-muted">{String(option.summary ?? "Architecture option summary.")}</p>
              <pre className="mt-4 overflow-auto rounded-md border border-border bg-surface p-3 text-xs text-ink-muted">{JSON.stringify(option.scores ?? option, null, 2)}</pre>
            </article>
          ))}
        </section>
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Rejected options</h2>
          <div className="mt-4 space-y-3">
            {view.rejected_options.map((option, index) => (
              <p key={index} className="rounded-md border border-border bg-surface p-3 text-sm text-ink-muted">{String(option.reason ?? option.name ?? JSON.stringify(option))}</p>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

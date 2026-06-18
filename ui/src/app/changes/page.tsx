import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { getChangeImpactView } from "@/lib/api";

export default async function ChangesPage() {
  const view = await getChangeImpactView();

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Change Impact"]}
          title="Change Impact Studio"
          description={view.change_event.new_value_summary ?? "Requirement change impact is ready for review."}
          badges={[{ label: view.change_event.changed_field, variant: "info" }]}
        />
        <section className="grid gap-5 lg:grid-cols-2">
          <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
            <h2 className="text-base font-semibold text-ink">Impacted stages</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {view.impact.impacted_stages.map((stage) => (
                <StatusBadge key={stage} variant="warning">{stage}</StatusBadge>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
            <h2 className="text-base font-semibold text-ink">Stable stages</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {view.impact.stable_stages.map((stage) => (
                <StatusBadge key={stage} variant="success">{stage}</StatusBadge>
              ))}
            </div>
          </div>
        </section>
        <section className="rounded-lg border border-border bg-panel shadow-panel">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold text-ink">Rerun plan</h2>
          </div>
          <div className="divide-y divide-border">
            {view.rerun_plan.map((item, index) => (
              <div key={item.stage} className="flex items-center justify-between gap-3 px-5 py-4">
                <div>
                  <p className="text-sm font-semibold text-ink">{index + 1}. {item.label}</p>
                  <p className="text-xs text-ink-muted">{item.stage}</p>
                </div>
                <StatusBadge variant="info">{item.status}</StatusBadge>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

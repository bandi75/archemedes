import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
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
        <SessionContextBanner stage="Change Impact" />
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-ink-subtle">Before</p>
              <p className="mt-2 text-sm text-ink-muted">10K TPS, single-region deployment assumptions</p>
            </div>
            <div className="text-sm font-semibold text-accent">changes to</div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-ink-subtle">After</p>
              <p className="mt-2 text-sm text-ink-muted">{view.change_event.new_value_summary ?? "100K TPS, active-active multi-region deployment"}</p>
            </div>
          </div>
        </section>
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
                  <p className="text-xs text-ink-muted">{impactReason(item.stage)}</p>
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

function impactReason(stage: string) {
  const reasons: Record<string, string> = {
    options_generation: "Scale and topology affect service selection and trade-offs.",
    socratic_review: "Personas must re-check security, cost, reliability, and delivery assumptions.",
    adr_generation: "Decision record must reflect the updated scale and deployment choice.",
    hld_generation: "Architecture diagrams and deployment topology need regeneration.",
    mini_waf_review: "Reliability, security, and cost risks change with active-active deployment.",
    final_evidence_audit: "Evidence coverage must be re-audited after changed artifacts.",
  };
  return reasons[stage] ?? "Stage depends on changed requirement context.";
}

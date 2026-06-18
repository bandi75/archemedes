import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
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
        <SessionContextBanner stage="Options Generation" />
        {view.quality_gate ? <QualityGateBadge status={view.quality_gate.status} /> : null}
        <section className="grid gap-5 lg:grid-cols-2">
          {view.options.map((option, index) => (
            <article key={String(option.option_id ?? index)} className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-lg font-semibold text-ink">{String(option.name ?? `Option ${index + 1}`)}</h2>
                {option.option_id === view.selected_option_id ? <StatusBadge variant="success">Selected</StatusBadge> : null}
              </div>
              <p className="mt-3 text-sm leading-6 text-ink-muted">{String(option.summary ?? "Architecture option summary.")}</p>
              <TradeoffScores scores={option.scores} />
              <div className="mt-4 rounded-md border border-border bg-surface p-3 text-sm text-ink-muted">
                <p className="font-medium text-ink">Selection rationale</p>
                <p className="mt-1">{String(option.rationale ?? option.reason ?? "Balances delivery speed, managed operations, scalability, and evidence-backed Azure service fit.")}</p>
              </div>
            </article>
          ))}
        </section>
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Assumptions affecting options</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {["Tokenized card data boundary", "100K TPS burst target", "Active-active region requirement", "Team can operate streaming services"].map((item) => (
              <StatusBadge key={item} variant="warning">{item}</StatusBadge>
            ))}
          </div>
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

function TradeoffScores({ scores }: { scores: unknown }) {
  const entries = Object.entries((scores && typeof scores === "object" ? scores : {
    cost: 7,
    complexity: 6,
    scalability: 8,
    delivery: 9,
  }) as Record<string, unknown>);

  return (
    <div className="mt-4 space-y-3">
      {entries.map(([dimension, rawScore]) => {
        const score = Number(rawScore) || 0;
        return (
          <div key={dimension}>
            <div className="flex items-center justify-between text-xs font-medium text-ink-muted">
              <span className="capitalize">{dimension.replaceAll("_", " ")}</span>
              <span>{score}/10</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface">
              <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(score * 10, 100)}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

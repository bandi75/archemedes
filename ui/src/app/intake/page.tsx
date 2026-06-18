import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";

export default function IntakePage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Session Workspace", "Intake"]}
          title="Intake Stage Detail"
          description="Review the original business need, clarifications, session setup metadata, and readiness for requirements extraction."
          badges={[{ label: "Stage 1", variant: "info" }]}
        />
        <SessionContextCard />
        <section className="rounded-lg border border-border bg-panel p-4 shadow-panel">
          <div className="flex flex-wrap gap-2">
            {["Answer clarification", "Update business need", "Mark intake ready", "Return to pipeline"].map((action, index) => (
              <button
                key={action}
                className={index === 2
                  ? "inline-flex h-9 items-center rounded-md bg-accent px-3 text-sm font-medium text-white"
                  : "inline-flex h-9 items-center rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink"}
                type="button"
              >
                {action}
              </button>
            ))}
          </div>
          <p className="mt-3 text-sm text-ink-muted">Pipeline run controls stay on Pipeline. This page explains and edits Intake outputs.</p>
        </section>
        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)]">
          <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
            <h2 className="text-base font-semibold text-ink">Guided intake conversation</h2>
            <div className="mt-4 space-y-3">
              <div className="rounded-md border border-border bg-surface p-4 text-sm leading-6 text-ink-muted">
                Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.
              </div>
              <div className="rounded-md border border-accent/20 bg-accent/5 p-4 text-sm leading-6 text-ink-muted">
                Archimedes: I will clarify throughput, data sensitivity, regional availability, latency target, and approved service constraints before generating requirements.
              </div>
            </div>
            <div className="mt-5 rounded-md border border-border bg-surface p-3 text-sm text-ink-subtle">
              Ask for missing constraints, paste an existing brief, or select a template below to seed the session.
            </div>
          </div>

          <aside className="space-y-5">
            <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Session setup</h2>
              <div className="mt-4 space-y-3 text-sm text-ink-muted">
                <p><span className="font-medium text-ink">Domain:</span> Financial services</p>
                <p><span className="font-medium text-ink">Preferred cloud:</span> Azure</p>
                <p><span className="font-medium text-ink">Library context:</span> Org approved services v2.1</p>
                <p><span className="font-medium text-ink">Evidence sources:</span> Azure Architecture Center, WAF, internal standards</p>
              </div>
            </div>
            <div className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <h2 className="text-base font-semibold text-ink">Completeness checklist</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                {["Business goal", "Scale", "Compliance", "Availability", "Latency"].map((item) => (
                  <StatusBadge key={item} variant="success">{item}</StatusBadge>
                ))}
                <StatusBadge variant="warning">Data boundary</StatusBadge>
              </div>
            </div>
          </aside>
        </section>
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Demo scenario templates</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {["Real-time fraud detection", "Claims modernization", "Factory telemetry edge"].map((template) => (
              <button key={template} className="rounded-md border border-border bg-surface p-4 text-left text-sm font-medium text-ink transition hover:border-accent hover:text-accent">
                {template}
              </button>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function SessionContextCard() {
  return (
    <section className="rounded-lg border border-border bg-panel px-5 py-4 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-subtle">Current session</p>
      <h2 className="mt-1 text-base font-semibold text-ink">Fintech fraud platform</h2>
      <p className="mt-1 text-sm text-ink-muted">Current stage: Intake | Active version: v0 | Owner: current user | Mode: mock</p>
    </section>
  );
}

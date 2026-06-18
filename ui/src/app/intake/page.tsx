import { AppShell } from "@/components/layout/app-shell";
import { SessionActions } from "@/components/hero/session-actions";
import { PageHeader } from "@/components/shared/page-header";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
import { StatusBadge } from "@/components/shared/status-badge";

export default function IntakePage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Intake"]}
          title="Intake Workspace"
          description="Dedicated entry point for creating an architecture session and starting the guided pipeline."
          badges={[{ label: "Session entry", variant: "info" }]}
        />
        <SessionContextBanner stage="Intake" />
        <SessionActions />
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

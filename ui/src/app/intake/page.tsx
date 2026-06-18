import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";

export default function IntakePage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Command Center", "New Session"]}
          title="New architecture session"
          description="Capture the business need, choose organization/library context, clarify missing details, then create the session."
          badges={[
            { label: "No session created yet", variant: "neutral" },
            { label: "Creation mode", variant: "info" },
          ]}
        />
        <section className="rounded-lg border border-border bg-panel p-4 shadow-panel">
          <div className="flex flex-wrap gap-2">
            {["Save draft", "Ask clarifying questions", "Create session", "Create and start pipeline", "Cancel"].map((action, index) => (
              <button
                key={action}
                className={index === 3
                  ? "inline-flex h-9 items-center rounded-md bg-accent px-3 text-sm font-medium text-white"
                  : "inline-flex h-9 items-center rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink"}
                type="button"
              >
                {action}
              </button>
            ))}
          </div>
          <p className="mt-3 text-sm text-ink-muted">Pipeline controls appear after a session exists and the user lands on Pipeline.</p>
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

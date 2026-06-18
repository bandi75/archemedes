import { AppShell } from "@/components/layout/app-shell";
import { SessionActions } from "@/components/hero/session-actions";
import { PageHeader } from "@/components/shared/page-header";

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
        <SessionActions />
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Business need draft</h2>
          <div className="mt-4 rounded-md border border-border bg-surface p-4 text-sm leading-6 text-ink-muted">
            Design a real-time fraud detection platform on Azure for a fintech processing 10K TPS with PCI-DSS constraints and 99.95% availability.
          </div>
        </section>
      </div>
    </AppShell>
  );
}

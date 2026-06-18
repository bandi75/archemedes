import { Activity, CheckCircle2, Clock3, FileText, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { DataTable } from "@/components/shared/data-table";
import { RightDrawer } from "@/components/shared/right-drawer";
import { mockPipelineStages, mockSessions } from "@/lib/mock-data";

export default function Home() {
  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Command Center"]}
          title="Architecture Command Center"
          description="Session triage, pipeline readiness, and demo-safe mock state for the React workbench."
          badges={[
            { label: "Demo mode", variant: "info" },
            { label: "Mock data", variant: "teal" },
          ]}
        />

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Active sessions" value="3" trend="2 ready for review" icon={FileText} />
          <MetricCard label="Pipeline health" value="92%" trend="All gates inspectable" icon={Activity} tone="success" />
          <MetricCard label="Open assumptions" value="5" trend="Validation flow ready" icon={Clock3} tone="warning" />
          <MetricCard label="Evidence trust" value="High" trend="17 cited sources" icon={ShieldCheck} tone="teal" />
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(340px,0.75fr)]">
          <div className="rounded-lg border border-border bg-panel shadow-panel">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div>
                <h2 className="text-base font-semibold text-ink">Recent sessions</h2>
                <p className="mt-1 text-sm text-ink-muted">Newest-first mock sessions for Phase 1 shell validation.</p>
              </div>
              <StatusBadge variant="neutral">Read only</StatusBadge>
            </div>
            <DataTable
              columns={[
                { key: "name", label: "Session" },
                { key: "stage", label: "Current stage" },
                { key: "quality", label: "Gate" },
                { key: "updated", label: "Updated" },
              ]}
              rows={mockSessions.map((session) => ({
                id: session.id,
                name: <span className="font-medium text-ink">{session.name}</span>,
                stage: session.stage,
                quality: <QualityGateBadge status={session.qualityGate} />,
                updated: session.updatedAt,
              }))}
            />
          </div>

          <div className="rounded-lg border border-border bg-panel shadow-panel">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-base font-semibold text-ink">Pipeline skeleton</h2>
              <p className="mt-1 text-sm text-ink-muted">The shell reserves stable space for Phase 2 live orchestration state.</p>
            </div>
            <ol className="space-y-3 p-5">
              {mockPipelineStages.map((stage) => (
                <li key={stage.id} className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-3">
                  <CheckCircle2 className="h-4 w-4 text-success" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{stage.name}</p>
                    <p className="text-xs text-ink-muted">{stage.summary}</p>
                  </div>
                  <StatusBadge variant={stage.statusVariant}>{stage.status}</StatusBadge>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <RightDrawer title="Foundation Drawer" description="Shared drawer component wired for later detail views.">
          <div className="space-y-3 text-sm text-ink-muted">
            <p>Selected session details, quality gate evidence, and trace events will dock here in later phases.</p>
            <QualityGateBadge status="passed_with_warnings" />
          </div>
        </RightDrawer>
      </div>
    </AppShell>
  );
}

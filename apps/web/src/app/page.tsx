import Link from "next/link";
import { Activity, BookOpen, CheckCircle2, Clock3, FileText, Plus, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { DataTable } from "@/components/shared/data-table";

export default function Home() {
  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Command Center"]}
          title="Architecture Command Center"
          description="My architecture sessions, work needing review, and reusable organization knowledge."
        />


        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Active sessions" value="3" trend="2 ready for review" icon={FileText} />
          <MetricCard label="Pipeline health" value="92%" trend="All gates inspectable" icon={Activity} tone="success" />
          <MetricCard label="Open assumptions" value="5" trend="Validation flow ready" icon={Clock3} tone="warning" />
          <MetricCard label="Evidence trust" value="High" trend="17 cited sources" icon={ShieldCheck} tone="teal" />
        </section>

        <section className="flex flex-col gap-3 rounded-lg border border-border bg-panel p-5 shadow-panel md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink">Create a new architecture session</h2>
            <p className="mt-1 text-sm text-ink-muted">Start with a business need, choose library context, and launch the guided pipeline.</p>
          </div>
          <Link className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white transition hover:bg-accent" href="/sessions/new">
            <Plus className="h-4 w-4" aria-hidden="true" />
            New session
          </Link>
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(340px,0.75fr)]">
          <div className="rounded-lg border border-border bg-panel shadow-panel">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div>
                <h2 className="text-base font-semibold text-ink">My active sessions</h2>
                <p className="mt-1 text-sm text-ink-muted">Recently updated sessions owned by or assigned to the current user.</p>
              </div>
            </div>
            <DataTable
              columns={[
                { key: "name", label: "Session" },
                { key: "stage", label: "Current stage" },
                { key: "owner", label: "Owner" },
                { key: "quality", label: "Gate" },
                { key: "updated", label: "Updated" },
              ]}
              rows={[]}
            />
          </div>

          <div className="rounded-lg border border-border bg-panel shadow-panel">
            <div className="border-b border-border px-5 py-4">
              <h2 className="text-base font-semibold text-ink">Workbench readiness</h2>
              <p className="mt-1 text-sm text-ink-muted">Core session workflow areas available for the current product path.</p>
            </div>
            <ol className="space-y-3 p-5">
            </ol>
          </div>
        </section>

        <section className="grid gap-5 md:grid-cols-3">
          {[
            ["Needs my review", "3 assumptions need validation before the next run.", "/evidence"],
            ["Failed / waiting stages", "No failed stages. Socrates is currently running.", "/pipeline"],
            ["Architecture libraries", "Org standards, approved services, patterns, and review checklists.", "/library"],
          ].map(([title, body, href], index) => (
            <Link key={title} className="rounded-lg border border-border bg-panel p-5 shadow-panel transition hover:border-accent hover:shadow-elevated" href={href}>
              <BookOpen className="h-5 w-5 text-accent" aria-hidden={index !== 2} />
              <h2 className="mt-3 text-base font-semibold text-ink">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-ink-muted">{body}</p>
            </Link>
          ))}
        </section>
      </div>
    </AppShell>
  );
}

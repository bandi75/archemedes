import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
import { StatusBadge } from "@/components/shared/status-badge";
import { getArtifactPackageView } from "@/lib/api";

export default async function ArtifactsPage() {
  const view = await getArtifactPackageView();

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Artifacts"]}
          title="Artifact Studio"
          description="Architecture package status with render status separated from quality gates."
          badges={[{ label: view.package_status, variant: "info" }]}
        />
        <SessionContextBanner stage="Artifact Studio" />
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Studio mode</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {["Package overview", "Document viewer", "Requirements", "Options", "Socrates Brief", "ADR", "HLD", "WAF Review", "Evidence Report", "Export"].map((tab, index) => (
              <StatusBadge key={tab} variant={index === 0 ? "info" : "neutral"}>{tab}</StatusBadge>
            ))}
          </div>
        </section>
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge variant={view.render_status.status === "passed" ? "success" : "warning"}>Render {view.render_status.status}</StatusBadge>
            <p className="text-sm text-ink-muted">Browser-side render state is tracked separately from stage quality gates.</p>
          </div>
        </section>
        <section className="grid gap-4 lg:grid-cols-2">
          {view.artifacts.map((artifact) => (
            <article key={artifact.stage} className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-normal text-ink-subtle">{artifact.stage}</p>
                  <h2 className="mt-1 text-lg font-semibold text-ink">{artifact.title ?? artifact.label ?? artifact.stage}</h2>
                </div>
                {artifact.quality_gate ? <QualityGateBadge status={artifact.quality_gate.status} /> : <StatusBadge variant="neutral">Pending</StatusBadge>}
              </div>
              <p className="mt-3 text-sm leading-6 text-ink-muted">{artifact.summary}</p>
              <p className="mt-4 text-xs text-ink-subtle">Version {artifact.version ?? "-"}</p>
            </article>
          ))}
        </section>
      </div>
    </AppShell>
  );
}

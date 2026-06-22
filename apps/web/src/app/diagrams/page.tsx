import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
import { StatusBadge } from "@/components/shared/status-badge";
import { getArtifactPackageView } from "@/lib/api";

export default async function DiagramsPage() {
  const view = await getArtifactPackageView("default");
  const hld = view.artifacts?.find((artifact) => artifact.stage === "hld_generation");

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Diagrams"]}
          title="Mermaid Diagram Viewer"
          description={hld?.summary ?? "HLD diagram preview and source view."}
          badges={[{ label: "Render separate from gate", variant: "teal" }]}
        />
        <SessionContextBanner stage="HLD Diagram" />
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge variant="info">Rendered Diagram</StatusBadge>
            <StatusBadge variant="neutral">Mermaid Source</StatusBadge>
            <StatusBadge variant="neutral">Render Diagnostics</StatusBadge>
          </div>
          <div className="mt-5 rounded-xl border border-border bg-surface p-6">
            <p className="text-sm font-semibold text-ink-muted">No diagram to render.</p>
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <StatusBadge variant={view.render_status?.status === "passed" ? "success" : "warning"}>Render {view.render_status?.status ?? "unknown"}</StatusBadge>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

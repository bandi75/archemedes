import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
import { StatusBadge } from "@/components/shared/status-badge";
import { getArtifactPackageView } from "@/lib/api";

const demoMermaid = `flowchart LR
  Client[Transaction Systems] --> EventHubs[Azure Event Hubs]
  EventHubs --> StreamAnalytics[Stream Analytics]
  StreamAnalytics --> Functions[Azure Functions]
  Functions --> Cosmos[Cosmos DB]
  Cosmos --> Monitor[Azure Monitor]`;

export default async function DiagramsPage() {
  const view = await getArtifactPackageView();
  const hld = view.artifacts.find((artifact) => artifact.stage === "hld_generation");

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
            <div className="grid gap-4 md:grid-cols-5 md:items-center">
              {["Transaction Systems", "Event Hubs", "Stream Analytics", "Azure Functions", "Cosmos DB"].map((node, index) => (
                <div key={node} className="relative rounded-lg border border-accent/20 bg-panel p-4 text-center shadow-panel">
                  <p className="text-sm font-semibold text-ink">{node}</p>
                  {index < 4 ? <span className="absolute -right-3 top-1/2 hidden h-px w-6 bg-accent md:block" /> : null}
                </div>
              ))}
            </div>
            <div className="mx-auto mt-4 max-w-xs rounded-lg border border-evidence/20 bg-evidence/10 p-4 text-center text-sm font-semibold text-evidence">
              Azure Monitor
            </div>
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <StatusBadge variant="success">Render source available</StatusBadge>
            <StatusBadge variant={view.render_status.status === "passed" ? "success" : "warning"}>Render {view.render_status.status}</StatusBadge>
          </div>
          <pre className="mt-5 overflow-auto rounded-md border border-border bg-surface p-4 text-sm leading-6 text-ink-muted">{demoMermaid}</pre>
        </section>
      </div>
    </AppShell>
  );
}

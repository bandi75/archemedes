import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
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
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge variant="success">Render source available</StatusBadge>
            <StatusBadge variant={view.render_status.status === "passed" ? "success" : "warning"}>Render {view.render_status.status}</StatusBadge>
          </div>
          <pre className="mt-5 overflow-auto rounded-md border border-border bg-surface p-4 text-sm leading-6 text-ink-muted">{demoMermaid}</pre>
        </section>
      </div>
    </AppShell>
  );
}

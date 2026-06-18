import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { getArtifactHistory, getArtifactPackageView } from "@/lib/api";

export default async function HistoryPage() {
  const history = await getArtifactHistory();
  const packageView = await getArtifactPackageView();
  const rows = history.items.length > 0 ? history.items : packageView.artifacts.map((artifact, index) => ({
    artifact_id: `${artifact.stage}-${index}`,
    stage: artifact.stage,
    version: artifact.version ?? 0,
    content: { summary: artifact.summary },
    quality_gate: artifact.quality_gate ?? { status: "passed" as const },
    created_at: "mock",
  }));

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "History"]}
          title="Version History"
          description="Artifact versions and quality state across the architecture package."
          badges={[{ label: `${rows.length} artifacts`, variant: "info" }]}
        />
        <section className="rounded-lg border border-border bg-panel shadow-panel">
          <DataTable
            columns={[
              { key: "stage", label: "Stage" },
              { key: "version", label: "Version" },
              { key: "summary", label: "Summary" },
              { key: "gate", label: "Gate" },
            ]}
            rows={rows.map((artifact) => ({
              id: artifact.artifact_id,
              stage: artifact.stage,
              version: `v${artifact.version}`,
              summary: String(artifact.content.summary ?? "Artifact version"),
              gate: <QualityGateBadge status={artifact.quality_gate.status} />,
            }))}
          />
        </section>
      </div>
    </AppShell>
  );
}

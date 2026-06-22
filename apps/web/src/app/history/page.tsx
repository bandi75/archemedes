import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { QualityGateBadge } from "@/components/shared/quality-gate-badge";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
import { StatusBadge } from "@/components/shared/status-badge";
import { getArtifactHistory, getArtifactPackageView } from "@/lib/api";

const stageNames: Record<string, string> = {
  intake: "Intake",
  requirements_extraction: "Requirements",
  pattern_detection: "Pattern Detection",
  options_generation: "Options",
  socratic_review: "Socrates Review",
  adr_generation: "ADR",
  hld_generation: "HLD",
  mini_waf_review: "Mini WAF Review",
  final_evidence_audit: "Final Evidence Audit",
};

export default async function HistoryPage() {
  const history = await getArtifactHistory();
  const packageView = await getArtifactPackageView();
  const rows = history.items.length > 0 ? history.items : packageView.artifacts.map((artifact, index) => ({
    artifact_id: `${artifact.stage}-${index}`,
    stage: artifact.stage,
    version: artifact.version ?? 0,
    content: { summary: artifact.summary },
    quality_gate: artifact.quality_gate ?? { status: "passed" as const },
    created_at: new Date().toISOString(),
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
        <SessionContextBanner stage="Version History" />
        <section className="rounded-lg border border-border bg-panel shadow-panel">
          <DataTable
            columns={[
              { key: "stage", label: "Stage" },
              { key: "version", label: "Version" },
              { key: "summary", label: "Summary" },
              { key: "created", label: "Created" },
              { key: "change", label: "Change" },
              { key: "diff", label: "Diff" },
              { key: "gate", label: "Gate" },
            ]}
            rows={rows.map((artifact) => ({
              id: artifact.artifact_id,
              stage: stageNames[artifact.stage] ?? artifact.stage,
              version: `v${artifact.version}`,
              summary: String(artifact.content.summary ?? "Artifact version"),
              created: new Date(artifact.created_at).toLocaleString(),
              change: artifact.version > 1 ? "Requirement change" : "Initial run",
              diff: <StatusBadge variant={artifact.version > 1 ? "info" : "neutral"}>{artifact.version > 1 ? "View diff" : "Baseline"}</StatusBadge>,
              gate: <QualityGateBadge status={artifact.quality_gate.status} />,
            }))}
          />
        </section>
      </div>
    </AppShell>
  );
}

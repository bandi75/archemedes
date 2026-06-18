import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { DataTable } from "@/components/shared/data-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { getEvidenceView } from "@/lib/api";
import { Database, FileCheck2, ShieldCheck } from "lucide-react";

export default async function EvidencePage() {
  const view = await getEvidenceView();

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Evidence"]}
          title="Evidence & Claims Explorer"
          description="Claims, citations, trust levels, freshness, and validation state from the evidence view model."
          badges={[{ label: "Claims linked", variant: "teal" }]}
        />
        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Claims" value={String(view.coverage.total_claims)} trend={`${view.coverage.claims_with_evidence} with evidence`} icon={FileCheck2} tone="teal" />
          <MetricCard label="Evidence sources" value={String(view.coverage.evidence_sources)} trend="Queryable source list" icon={Database} />
          <MetricCard label="Open assumptions" value={String(view.coverage.open_assumptions)} trend="Validation ready" icon={ShieldCheck} tone="warning" />
        </section>
        <section className="rounded-lg border border-border bg-panel shadow-panel">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold text-ink">Claims</h2>
          </div>
          <DataTable
            columns={[
              { key: "claim", label: "Claim" },
              { key: "type", label: "Type" },
              { key: "confidence", label: "Confidence" },
              { key: "validation", label: "Validation" },
            ]}
            rows={view.claims.map((claim) => ({
              id: claim.claim_id,
              claim: <span className="font-medium text-ink">{claim.claim}</span>,
              type: claim.type,
              confidence: `${Math.round(claim.confidence * 100)}%`,
              validation: <StatusBadge variant={claim.requires_user_validation ? "warning" : "success"}>{claim.requires_user_validation ? "Needs validation" : "Grounded"}</StatusBadge>,
            }))}
          />
        </section>
      </div>
    </AppShell>
  );
}

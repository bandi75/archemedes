import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { DataTable } from "@/components/shared/data-table";
import { SessionContextBanner } from "@/components/shared/session-context-banner";
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
        <SessionContextBanner stage="Evidence & Claims" />
        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Claims" value={String(view.coverage.total_claims)} trend={`${view.coverage.claims_with_evidence} with evidence`} icon={FileCheck2} tone="teal" />
          <MetricCard label="Evidence sources" value={String(view.coverage.evidence_sources)} trend="Queryable source list" icon={Database} />
          <MetricCard label="Open assumptions" value={String(view.coverage.open_assumptions)} trend="Validation ready" icon={ShieldCheck} tone="warning" />
        </section>
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Explorer filters</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {["All stages", "Assumptions", "Needs validation", "High trust", "Current sources", "Unsupported only"].map((filter, index) => (
              <StatusBadge key={filter} variant={index === 0 ? "info" : "neutral"}>{filter}</StatusBadge>
            ))}
          </div>
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
        {view.claims[0] ? (
          <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-ink">Claim detail</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-muted">{view.claims[0].claim}</p>
              </div>
              <StatusBadge variant={view.claims[0].requires_user_validation ? "warning" : "success"}>
                {view.claims[0].requires_user_validation ? "Validation needed" : "Grounded"}
              </StatusBadge>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <DetailTile label="Used by stage" value={view.claims[0].type} />
              <DetailTile label="Trust / freshness" value={view.evidence[0] ? `${view.evidence[0].trust_level} / ${view.evidence[0].source_freshness}` : "No evidence"} />
              <DetailTile label="Audit notes" value="No contradictions detected in current evidence set." />
            </div>
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}

function DetailTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-subtle">{label}</p>
      <p className="mt-2 text-sm leading-6 text-ink-muted">{value}</p>
    </div>
  );
}

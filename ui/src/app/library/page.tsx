import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";

const libraryItems = [
  ["Approved services", "Event Hubs, Cosmos DB, Azure Monitor, Functions"],
  ["Architecture patterns", "Event-driven streaming, CQRS, resilient ingestion"],
  ["Organization standards", "PCI-DSS data boundaries, landing-zone rules, observability baseline"],
  ["Review checklists", "WAF, cost, reliability, security, operational readiness"],
];

export default function LibraryPage() {
  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Command Center", "Library"]}
          title="Architecture Libraries"
          description="Reusable organization knowledge outside any single architecture session."
          badges={[{ label: "Global catalog", variant: "info" }]}
        />
        <section className="grid gap-5 md:grid-cols-2">
          {libraryItems.map(([title, body]) => (
            <article key={title} className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <StatusBadge variant="neutral">Catalog item</StatusBadge>
              <h2 className="mt-3 text-base font-semibold text-ink">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-ink-muted">{body}</p>
            </article>
          ))}
        </section>
      </div>
    </AppShell>
  );
}

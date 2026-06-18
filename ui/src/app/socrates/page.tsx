import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { getSocratesView } from "@/lib/api";
import { Landmark, Sparkles, Target } from "lucide-react";

export default async function SocratesPage() {
  const view = await getSocratesView();
  const confidence = Math.round((view.synthesis.confidence || 0) * 100);

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Workbench", "Socrates"]}
          title="Socrates Reasoning Lab"
          description={view.decision_under_review.summary}
          badges={[{ label: "Standard mode", variant: "purple" }]}
        />
        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Personas" value={String(view.personas.length)} trend="Concurrent review" icon={Landmark} tone="teal" />
          <MetricCard label="Confidence" value={`${confidence}%`} trend="Synthesizer decision" icon={Target} tone="success" />
          <MetricCard label="Blind spots" value={String(view.synthesis.blind_spots.length)} trend="Requires review" icon={Sparkles} tone="warning" />
        </section>
        <section className="rounded-lg border border-border bg-panel p-5 shadow-panel">
          <StatusBadge variant="purple">Recommended decision</StatusBadge>
          <h2 className="mt-3 text-xl font-semibold text-ink">{view.synthesis.recommended_decision}</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {view.synthesis.blind_spots.map((item) => (
              <p key={item} className="rounded-md border border-border bg-surface p-3 text-sm text-ink-muted">{item}</p>
            ))}
          </div>
        </section>
        <section className="grid gap-4 lg:grid-cols-2">
          {view.personas.map((persona, index) => (
            <article key={`${persona.persona ?? persona.persona_name ?? index}`} className="rounded-lg border border-border bg-panel p-5 shadow-panel">
              <StatusBadge variant="purple">{persona.persona ?? persona.persona_name ?? `Persona ${index + 1}`}</StatusBadge>
              <p className="mt-3 text-sm leading-6 text-ink-muted">{persona.summary ?? "Persona findings are ready for review."}</p>
            </article>
          ))}
        </section>
      </div>
    </AppShell>
  );
}

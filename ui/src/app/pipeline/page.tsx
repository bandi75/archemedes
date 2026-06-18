import { AppShell } from "@/components/layout/app-shell";
import { LiveEventsPanel } from "@/components/hero/live-events-panel";
import { SessionActions } from "@/components/hero/session-actions";
import { StageList } from "@/components/hero/stage-list";
import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { getPipelineView } from "@/lib/api";
import { Activity, CheckCircle2, Clock3 } from "lucide-react";

export default async function PipelinePage() {
  const view = await getPipelineView();
  const completed = view.stages.filter((stage) => stage.status === "completed").length;
  const sessionTitle = view.session?.title ?? "Active architecture session";

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          breadcrumb={["Session Workspace", "Pipeline"]}
          title={sessionTitle}
          description={view.session?.business_need ?? "Pipeline controls the architecture journey; stage pages explain the details."}
          badges={[
            { label: `Current: ${view.selected_stage.label}`, variant: "info" },
            { label: `Mode: ${view.session?.mode ?? "live"}`, variant: "neutral" },
          ]}
        />
        <SessionActions />
        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Completed stages" value={`${completed}/${view.stages.length}`} trend="Screen-ready timeline" icon={CheckCircle2} tone="success" />
          <MetricCard label="Current stage" value={view.selected_stage.label} trend={view.selected_stage.status} icon={Activity} />
          <MetricCard label="Recent events" value={String(view.recent_events.length)} trend="Snapshot then stream" icon={Clock3} tone="teal" />
        </section>
        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
          <StageList stages={view.stages} />
          <LiveEventsPanel sessionId={view.session_id} initialEvents={view.recent_events} />
        </section>
      </div>
    </AppShell>
  );
}

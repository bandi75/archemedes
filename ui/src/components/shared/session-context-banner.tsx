import { StatusBadge } from "@/components/shared/status-badge";

type SessionContextBannerProps = {
  stage: string;
  version?: string;
  mode?: string;
  owner?: string;
};

export function SessionContextBanner({
  stage,
  version = "v1",
  mode = "Mock",
  owner = "current user",
}: SessionContextBannerProps) {
  return (
    <section className="rounded-lg border border-border bg-panel px-5 py-4 shadow-panel">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-subtle">Current session</p>
          <h2 className="mt-1 text-base font-semibold text-ink">Fintech fraud platform</h2>
          <p className="mt-1 text-sm text-ink-muted">Owner: {owner} | Active version: {version}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge variant="info">Stage: {stage}</StatusBadge>
          <StatusBadge variant="neutral">Mode: {mode}</StatusBadge>
        </div>
      </div>
    </section>
  );
}

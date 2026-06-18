import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/cn";

type MetricCardProps = {
  label: string;
  value: string;
  trend: string;
  icon: LucideIcon;
  tone?: "neutral" | "success" | "warning" | "teal";
};

const toneClasses = {
  neutral: "text-accent",
  success: "text-success",
  warning: "text-warning",
  teal: "text-evidence",
};

export function MetricCard({ label, value, trend, icon: Icon, tone = "neutral" }: MetricCardProps) {
  return (
    <article className="rounded-lg border border-border bg-panel p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-ink-muted">{label}</p>
        <Icon className={cn("h-4 w-4", toneClasses[tone])} aria-hidden="true" />
      </div>
      <p className="mt-3 text-2xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-sm text-ink-muted">{trend}</p>
    </article>
  );
}

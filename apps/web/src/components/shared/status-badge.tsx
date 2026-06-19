import { AlertTriangle, CheckCircle2, Circle, Info, Sparkles } from "lucide-react";
import { cn } from "@/lib/cn";

export type StatusBadgeVariant = "success" | "warning" | "danger" | "info" | "neutral" | "purple" | "teal";

type StatusBadgeProps = {
  variant: StatusBadgeVariant;
  children: React.ReactNode;
};

const variantStyles: Record<StatusBadgeVariant, string> = {
  success: "border-success/20 bg-success/10 text-success",
  warning: "border-warning/25 bg-warning/10 text-warning",
  danger: "border-danger/20 bg-danger/10 text-danger",
  info: "border-accent/20 bg-accent/10 text-accent",
  neutral: "border-border bg-surface text-ink-muted",
  purple: "border-socrates/20 bg-socrates/10 text-socrates",
  teal: "border-evidence/20 bg-evidence/10 text-evidence",
};

const icons = {
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: AlertTriangle,
  info: Info,
  neutral: Circle,
  purple: Sparkles,
  teal: CheckCircle2,
};

export function StatusBadge({ variant, children }: StatusBadgeProps) {
  const Icon = icons[variant];

  return (
    <span
      className={cn(
        "inline-flex h-6 max-w-full items-center gap-1.5 rounded-md border px-2 text-xs font-medium",
        variantStyles[variant],
      )}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      <span className="truncate">{children}</span>
    </span>
  );
}

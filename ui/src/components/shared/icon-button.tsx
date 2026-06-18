import type { LucideIcon } from "lucide-react";

type IconButtonProps = {
  label: string;
  icon: LucideIcon;
};

export function IconButton({ label, icon: Icon }: IconButtonProps) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      className="grid h-10 w-10 shrink-0 place-items-center rounded-md border border-border bg-panel text-ink-muted transition hover:bg-surface hover:text-ink"
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
    </button>
  );
}

import { StatusBadge, type StatusBadgeVariant } from "@/components/shared/status-badge";

type PageHeaderProps = {
  breadcrumb: string[];
  title: string;
  description?: string;
  badges?: Array<{ label: string; variant: StatusBadgeVariant }>;
};

export function PageHeader({ breadcrumb, title, description, badges = [] }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-normal text-ink-subtle">{breadcrumb.join(" / ")}</p>
        <h1 className="mt-2 text-2xl font-semibold text-ink sm:text-3xl">{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-muted">{description}</p> : null}
      </div>
      {badges.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {badges.map((badge) => (
            <StatusBadge key={badge.label} variant={badge.variant}>
              {badge.label}
            </StatusBadge>
          ))}
        </div>
      ) : null}
    </header>
  );
}

type RightDrawerProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
};

export function RightDrawer({ title, description, children }: RightDrawerProps) {
  return (
    <aside className="rounded-lg border border-border bg-panel p-5 shadow-panel">
      <div className="border-b border-border pb-4">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
        {description ? <p className="mt-1 text-sm text-ink-muted">{description}</p> : null}
      </div>
      <div className="pt-4">{children}</div>
    </aside>
  );
}

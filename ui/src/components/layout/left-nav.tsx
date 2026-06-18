import { Activity, Boxes, FileText, GitCompareArrows, Home, Landmark, Search, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/cn";

const navItems = [
  { label: "Home", icon: Home, active: true },
  { label: "Pipeline", icon: Activity, active: false },
  { label: "Requirements", icon: FileText, active: false },
  { label: "Options", icon: Boxes, active: false },
  { label: "Socrates", icon: Landmark, active: false },
  { label: "Evidence", icon: ShieldCheck, active: false },
  { label: "Change Impact", icon: GitCompareArrows, active: false },
];

export function LeftNav() {
  return (
    <aside className="hidden border-r border-border bg-panel/95 px-4 py-5 lg:block">
      <div className="flex items-center gap-3 px-2">
        <div className="grid h-9 w-9 place-items-center rounded-md bg-ink text-sm font-bold text-white">A</div>
        <div>
          <p className="text-sm font-semibold text-ink">Archimedes</p>
          <p className="text-xs text-ink-muted">Architecture Workbench</p>
        </div>
      </div>

      <div className="mt-6 flex h-10 items-center gap-2 rounded-md border border-border bg-surface px-3 text-sm text-ink-muted">
        <Search className="h-4 w-4" aria-hidden="true" />
        <span>Search sessions</span>
      </div>

      <nav className="mt-6 space-y-1">
        {navItems.map((item) => (
          <a
            key={item.label}
            href="#"
            className={cn(
              "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition",
              item.active ? "bg-accent text-white" : "text-ink-muted hover:bg-surface hover:text-ink",
            )}
          >
            <item.icon className="h-4 w-4" aria-hidden="true" />
            {item.label}
          </a>
        ))}
      </nav>
    </aside>
  );
}

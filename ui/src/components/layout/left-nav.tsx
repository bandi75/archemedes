"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BookOpen, Boxes, FileText, GitCompareArrows, Home, Landmark, Search, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/cn";

const commandItems = [
  { label: "Command Center", href: "/", icon: Home },
  { label: "Architecture Libraries", href: "/library", icon: BookOpen },
];

const sessionItems = [
  { label: "Pipeline", href: "/pipeline", icon: Activity },
  { label: "Intake", href: "/intake", icon: FileText },
  { label: "Requirements", href: "/requirements", icon: FileText },
  { label: "Patterns", href: "/patterns", icon: Boxes },
  { label: "Options", href: "/options", icon: Boxes },
  { label: "Socrates", href: "/socrates", icon: Landmark },
  { label: "Evidence", href: "/evidence", icon: ShieldCheck },
  { label: "Artifacts", href: "/artifacts", icon: FileText },
  { label: "Diagrams", href: "/diagrams", icon: Boxes },
  { label: "History", href: "/history", icon: Activity },
  { label: "Change Impact", href: "/changes", icon: GitCompareArrows },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function LeftNav() {
  const pathname = usePathname();

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

      <nav className="mt-6 space-y-6">
        <div className="space-y-1">
          {commandItems.map((item) => (
            <NavLink key={item.label} item={item} active={isActive(pathname, item.href)} />
          ))}
        </div>

        <div>
          <p className="px-3 text-xs font-semibold uppercase tracking-wide text-ink-subtle">Session Workspace</p>
          <div className="mt-2 space-y-1">
            {sessionItems.map((item) => (
              <NavLink key={item.label} item={item} active={isActive(pathname, item.href)} />
            ))}
          </div>
        </div>
      </nav>
    </aside>
  );
}

function NavLink({
  item,
  active,
}: {
  item: { label: string; href: string; icon: LucideIcon };
  active: boolean;
}) {
  return (
    <Link
      href={item.href}
      className={cn(
        "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition",
        active ? "bg-accent text-white" : "text-ink-muted hover:bg-surface hover:text-ink",
      )}
    >
      <item.icon className="h-4 w-4" aria-hidden="true" />
      {item.label}
    </Link>
  );
}

import { Bell, CircleHelp, Command, Search, UserRound } from "lucide-react";
import { IconButton } from "@/components/shared/icon-button";

export function TopBar() {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-panel/90 px-4 py-3 backdrop-blur sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        <div className="flex min-w-0 flex-1 items-center gap-2 rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink-muted">
          <Search className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span className="truncate">Search architectures, evidence, decisions</span>
          <span className="ml-auto hidden items-center gap-1 rounded border border-border bg-panel px-1.5 py-0.5 text-xs text-ink-subtle sm:flex">
            <Command className="h-3 w-3" aria-hidden="true" /> K
          </span>
        </div>
        <IconButton label="Notifications" icon={Bell} />
        <IconButton label="Help" icon={CircleHelp} />
        <IconButton label="Profile" icon={UserRound} />
      </div>
    </header>
  );
}

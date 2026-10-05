import { Search, Bell, Command } from "lucide-react";

export function TopBar() {
  return (
    <header className="fixed top-0 left-64 right-0 h-16 border-b border-border bg-background/70 backdrop-blur-xl z-30 flex items-center px-8 gap-6">
      <div className="flex items-center gap-2 text-xs font-mono-code text-muted-foreground">
        <span>workspace</span>
        <span>/</span>
        <span className="text-foreground">acme-platform</span>
        <span>/</span>
        <span className="text-primary">overview</span>
      </div>
      <div className="ml-auto flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-white/5 text-xs text-muted-foreground w-72">
          <Search className="w-4 h-4" />
          <span>Search graph, files, ontologies…</span>
          <span className="ml-auto flex items-center gap-1 font-mono-code">
            <Command className="w-3 h-3" /> K
          </span>
        </div>
        <button className="w-9 h-9 rounded-lg border border-border hover:bg-white/5 flex items-center justify-center text-muted-foreground">
          <Bell className="w-4 h-4" />
        </button>
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-secondary" />
      </div>
    </header>
  );
}

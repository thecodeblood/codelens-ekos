import { Link } from "@tanstack/react-router";
import { LayoutGrid, Network, DownloadCloud, Terminal, BookOpen, Settings, Box, Activity } from "lucide-react";

const items = [
  { icon: LayoutGrid, label: "Overview", to: "/" as const, exact: true },
  { icon: Network, label: "Graph", to: "/graph" as const },
  { icon: Activity, label: "Insights", to: "/insights" as const },
  { icon: DownloadCloud, label: "Ingest", to: "/ingest" as const },
  { icon: Terminal, label: "Query", to: "/query" as const },
  { icon: BookOpen, label: "Docs", to: null },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 w-64 border-r border-border bg-surface/60 backdrop-blur-xl z-40 flex flex-col">
      <div className="h-16 flex items-center gap-3 px-6 border-b border-border">
        <div className="w-9 h-9 rounded-lg bg-primary/15 border border-primary/30 flex items-center justify-center glow-primary">
          <Box className="w-5 h-5 text-primary" />
        </div>
        <div className="leading-tight">
          <div className="font-bold tracking-tight">CodeLens</div>
          <div className="font-mono-code text-[10px] text-muted-foreground uppercase">Knowledge OS</div>
        </div>
      </div>
      <nav className="flex-1 px-3 py-6 space-y-1">
        <div className="px-3 mb-2 font-mono-code text-[10px] uppercase tracking-widest text-muted-foreground/60">Workspace</div>
        {items.map((it) => {
          const base = "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors";
          const inactive = "text-muted-foreground hover:text-foreground hover:bg-white/5";
          const active = "bg-primary/10 text-primary border border-primary/20";
          if (!it.to) {
            return (
              <a key={it.label} href="#" className={`${base} ${inactive}`}>
                <it.icon className="w-4 h-4" />
                <span>{it.label}</span>
              </a>
            );
          }
          return (
            <Link
              key={it.label}
              to={it.to}
              activeOptions={{ exact: it.exact ?? false }}
              className={`${base} ${inactive}`}
              activeProps={{ className: `${base} ${active}` }}
            >
              <it.icon className="w-4 h-4" />
              <span>{it.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-3 py-4 border-t border-border">
        <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-white/5">
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </a>
        <div className="mt-3 px-3 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary" />
          <div className="text-xs leading-tight">
            <div className="font-semibold">Ada Lovelace</div>
            <div className="text-muted-foreground">ada@codelens.io</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

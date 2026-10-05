import { Network, GitBranch, Hand, RotateCw, Share2, Tag } from "lucide-react";
import type { LayoutKind } from "@/lib/graph-share";

export function LayoutControls({
  layout,
  onLayoutChange,
  onRerun,
  showLabels,
  onToggleLabels,
  onShare,
}: {
  layout: LayoutKind;
  onLayoutChange: (l: LayoutKind) => void;
  onRerun: () => void;
  showLabels: boolean;
  onToggleLabels: () => void;
  onShare: () => void;
}) {
  const items: { key: LayoutKind; icon: typeof Hand; label: string }[] = [
    { key: "manual", icon: Hand, label: "Manual" },
    { key: "force", icon: Network, label: "Force" },
    { key: "hierarchical", icon: GitBranch, label: "Hierarchy" },
  ];

  return (
    <div className="flex items-center gap-2">
      <div className="glass-card rounded-lg p-1 flex items-center">
        {items.map((it) => {
          const active = layout === it.key;
          return (
            <button
              key={it.key}
              onClick={() => onLayoutChange(it.key)}
              title={it.label}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                active ? "bg-primary/20 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              <it.icon className="w-3.5 h-3.5" />
              <span className="hidden md:inline">{it.label}</span>
            </button>
          );
        })}
      </div>
      <button
        onClick={onRerun}
        title="Re-run layout (R)"
        className="glass-card rounded-lg px-2.5 py-2 text-muted-foreground hover:text-foreground hover:bg-white/5"
      >
        <RotateCw className="w-4 h-4" />
      </button>
      <button
        onClick={onToggleLabels}
        title="Toggle edge labels (L)"
        className={`glass-card rounded-lg px-2.5 py-2 hover:bg-white/5 ${
          showLabels ? "text-primary" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Tag className="w-4 h-4" />
      </button>
      <button
        onClick={onShare}
        title="Copy share link (S)"
        className="glass-card rounded-lg px-2.5 py-2 text-muted-foreground hover:text-foreground hover:bg-white/5"
      >
        <Share2 className="w-4 h-4" />
      </button>
    </div>
  );
}

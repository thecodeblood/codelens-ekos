import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Keyboard } from "lucide-react";

const SHORTCUTS: { keys: string; desc: string }[] = [
  { keys: "Tab / Shift+Tab", desc: "Cycle node selection" },
  { keys: "Enter", desc: "Open inspector for selected node" },
  { keys: "Shift+Enter", desc: "Add focused node to path selection" },
  { keys: "+ / -", desc: "Zoom in / out" },
  { keys: "0", desc: "Reset zoom & clear selection" },
  { keys: "Esc", desc: "Clear selection" },
  { keys: "/", desc: "Focus search" },
  { keys: "L", desc: "Toggle edge labels" },
  { keys: "R", desc: "Re-run layout" },
  { keys: "S", desc: "Copy share link" },
  { keys: "?", desc: "Show this dialog" },
];

export function ShortcutsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <button
          title="Keyboard shortcuts (?)"
          className="glass-card rounded-lg px-2.5 py-2 text-muted-foreground hover:text-foreground hover:bg-white/5"
        >
          <Keyboard className="w-4 h-4" />
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
        </DialogHeader>
        <div className="divide-y divide-white/5 rounded-lg border border-outline-variant">
          {SHORTCUTS.map((s) => (
            <div key={s.keys} className="flex items-center justify-between px-4 py-2.5">
              <span className="text-sm text-muted-foreground">{s.desc}</span>
              <kbd className="font-mono-code text-[11px] uppercase px-2 py-0.5 rounded bg-surface-container-low border border-white/10">
                {s.keys}
              </kbd>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}

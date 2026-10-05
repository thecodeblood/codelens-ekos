import { Link } from "@tanstack/react-router";
import { Network, ArrowRight } from "lucide-react";
import type { Message } from "@/lib/query-store";

export function GraphTraversalPanel({ messages }: { messages: Message[] }) {
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant" && !m.pending);
  const services = lastAssistant?.relatedServices ?? [];

  return (
    <aside className="hidden xl:flex w-80 border-l border-border bg-surface/40 backdrop-blur-xl flex-col">
      <div className="px-5 h-14 flex items-center justify-between border-b border-border">
        <div className="text-xs uppercase tracking-widest text-muted-foreground font-mono-code">
          Graph Traversal
        </div>
        <Link
          to="/graph"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          Open <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
      <div className="p-5 space-y-5 overflow-y-auto">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono-code mb-2">
            Related Services
          </div>
          {services.length === 0 ? (
            <div className="text-sm text-muted-foreground italic">
              Ask a question to see the traversed services here.
            </div>
          ) : (
            <ul className="space-y-1.5">
              {services.map((s) => (
                <li
                  key={s}
                  className="flex items-center gap-2 rounded-md px-2.5 py-1.5 bg-surface-container-low border border-outline-variant"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                  <span className="text-sm font-mono-code text-foreground/90">{s}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono-code mb-2">
            Mini Topology
          </div>
          <div className="glass-card rounded-lg p-4 aspect-square flex items-center justify-center relative overflow-hidden">
            <Network className="w-10 h-10 text-primary/30 absolute" />
            <svg viewBox="0 0 200 200" className="w-full h-full">
              {services.slice(0, 5).map((_, i, arr) => {
                const angle = (i / arr.length) * Math.PI * 2 - Math.PI / 2;
                const x = 100 + Math.cos(angle) * 65;
                const y = 100 + Math.sin(angle) * 65;
                return <line key={i} x1={100} y1={100} x2={x} y2={y} stroke="oklch(0.66 0.21 275 / 0.4)" strokeWidth={1} />;
              })}
              {services.slice(0, 5).map((_, i, arr) => {
                const angle = (i / arr.length) * Math.PI * 2 - Math.PI / 2;
                const x = 100 + Math.cos(angle) * 65;
                const y = 100 + Math.sin(angle) * 65;
                return <circle key={i} cx={x} cy={y} r={6} fill="oklch(0.66 0.21 275)" opacity={0.7} />;
              })}
              {services.length > 0 && (
                <circle cx={100} cy={100} r={9} fill="oklch(0.82 0.16 200)" />
              )}
            </svg>
          </div>
          <p className="text-[11px] text-muted-foreground mt-2 leading-relaxed">
            Open the Graph Explorer to traverse these relationships interactively.
          </p>
        </div>
      </div>
    </aside>
  );
}

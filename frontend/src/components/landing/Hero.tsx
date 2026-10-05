import { ArrowRight, Play } from "lucide-react";

export function Hero() {
  return (
    <section className="relative py-24 flex flex-col items-center text-center">
      <div className="absolute inset-0 hero-gradient -z-10" />

      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-[11px] font-mono-code uppercase tracking-widest mb-8">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
        </span>
        V1.0.4 Stable — Now Live
      </div>

      <h1 className="font-sans text-5xl md:text-7xl font-bold leading-[1.05] max-w-4xl mb-6 bg-clip-text text-transparent bg-gradient-to-b from-foreground to-muted-foreground">
        The Engineering Knowledge Operating System.
      </h1>
      <p className="text-base md:text-lg text-muted-foreground max-w-2xl mb-10 leading-relaxed">
        Build the Software System Model by unifying codebases, documentation, and operational data into a deterministic, queryable knowledge graph.
      </p>

      <div className="flex flex-col sm:flex-row items-center gap-4">
        <button className="bg-primary text-primary-foreground px-8 py-3 rounded-lg font-semibold hover:opacity-90 transition-all glow-primary flex items-center gap-2">
          Start Ingesting Knowledge
          <ArrowRight className="w-4 h-4" />
        </button>
        <button className="bg-transparent border border-border text-foreground px-8 py-3 rounded-lg font-semibold hover:bg-white/5 transition-all flex items-center gap-2">
          <Play className="w-4 h-4" /> View Documentation
        </button>
      </div>

      {/* 3D Graph Visualization Placeholder */}
      <div className="mt-20 w-full max-w-5xl aspect-video glass-card rounded-2xl overflow-hidden relative group">
        <GraphPlaceholder />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/30 to-transparent" />
        <div className="absolute bottom-8 left-8 text-left">
          <div className="font-mono-code text-xs text-secondary mb-2 uppercase tracking-widest">
            SYSTEM_MODEL_VIEW_INIT
          </div>
          <div className="text-2xl md:text-3xl font-bold">Interactive Dependency Topology</div>
        </div>
        <div className="absolute top-6 right-6 flex items-center gap-2 px-3 py-1 rounded-md bg-background/50 border border-border font-mono-code text-[10px] text-muted-foreground uppercase">
          <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
          Live · 12,438 nodes
        </div>
      </div>
    </section>
  );
}

function GraphPlaceholder() {
  // Decorative SVG node/edge graph
  const nodes = [
    { x: 20, y: 30, r: 4, c: "var(--primary)" },
    { x: 35, y: 55, r: 6, c: "var(--secondary)" },
    { x: 50, y: 25, r: 5, c: "var(--primary)" },
    { x: 65, y: 60, r: 7, c: "var(--tertiary)" },
    { x: 80, y: 35, r: 4, c: "var(--primary)" },
    { x: 28, y: 75, r: 3, c: "var(--secondary)" },
    { x: 72, y: 80, r: 4, c: "var(--secondary)" },
    { x: 45, y: 78, r: 5, c: "var(--primary)" },
    { x: 88, y: 70, r: 3, c: "var(--tertiary)" },
    { x: 12, y: 55, r: 3, c: "var(--secondary)" },
  ];
  const edges = [
    [0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [3, 7], [5, 7], [7, 6], [6, 8], [0, 9], [9, 5], [2, 4],
  ];
  return (
    <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
      <defs>
        <radialGradient id="bg" cx="50%" cy="40%">
          <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.25" />
          <stop offset="100%" stopColor="var(--background)" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect width="100" height="100" fill="url(#bg)" />
      {edges.map(([a, b], i) => (
        <line
          key={i}
          x1={nodes[a].x} y1={nodes[a].y}
          x2={nodes[b].x} y2={nodes[b].y}
          stroke="var(--primary)" strokeOpacity="0.35" strokeWidth="0.15"
        />
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={n.r * 0.4} fill={n.c} opacity="0.9" />
          <circle cx={n.x} cy={n.y} r={n.r * 1.2} fill={n.c} opacity="0.15" />
        </g>
      ))}
    </svg>
  );
}

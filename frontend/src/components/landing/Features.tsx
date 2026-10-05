import { Workflow, GitBranch, Route } from "lucide-react";

const features = [
  {
    icon: Workflow,
    color: "primary",
    title: "Deterministic AST Extraction",
    body: "Deep analysis of source code to build a complete structural map, preserving logic and intent across 25+ languages.",
  },
  {
    icon: GitBranch,
    color: "secondary",
    title: "Hierarchical Ontology",
    body: "Map technical debt, service boundaries, and team ownership into a unified, version-controlled organizational schema.",
  },
  {
    icon: Route,
    color: "tertiary",
    title: "Intelligent Query Routing",
    body: "Natural language interface that traverses the knowledge graph to answer complex architectural questions instantly.",
  },
];

export function Features() {
  return (
    <section className="py-20 grid grid-cols-12 gap-6">
      <div className="col-span-12 mb-4">
        <h2 className="text-3xl md:text-4xl font-bold">Core Capabilities</h2>
        <div className="h-1 w-20 bg-primary mt-3 rounded-full" />
      </div>

      {features.map((f) => (
        <div key={f.title} className="col-span-12 md:col-span-4 glass-card p-8 rounded-xl flex flex-col gap-6">
          <div
            className={`w-12 h-12 rounded-lg flex items-center justify-center ${
              f.color === "primary" ? "bg-primary/10 text-primary"
              : f.color === "secondary" ? "bg-secondary/10 text-secondary"
              : "bg-tertiary/10 text-tertiary"
            }`}
          >
            <f.icon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold mb-3">{f.title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{f.body}</p>
          </div>
        </div>
      ))}

      {/* Large Image Card */}
      <div className="col-span-12 glass-card p-1 rounded-xl group relative overflow-hidden h-[420px]">
        <div className="absolute inset-0 z-0">
          <img
            className="w-full h-full object-cover opacity-50 group-hover:scale-105 transition-transform duration-700"
            alt="3D architectural node graph of microservices with glowing indigo and cyan data flow"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAA09iHVlYdrbF32IK4rRthexZed_dAFF9eg7275qBoOTrz1Kmu19hWbuQEABI_11xf0MkXHHYvsFGgoN1ifjOc_sCmDvTC6te4Q4oIruMtH-VE28P49JC0pmq8MQYyzuuH-iPxWFSwm4hr5v59yD_GmMHLXTFfVX9vzYhctx7yg-vXa6N3OBUYTbmD6maLt4Q2fYKHWvPRrmloG2OxXOi9zyseZiiPgzj3hAfAlxNnjmoNY3gaoxS0tchI31pT-PGKRd31yAa-_DMb"
          />
        </div>
        <div className="relative z-10 p-10 h-full flex flex-col justify-end bg-gradient-to-t from-surface-container-highest via-surface-container-highest/40 to-transparent">
          <div className="max-w-xl">
            <span className="font-mono-code text-xs text-primary mb-4 block uppercase tracking-widest">
              Global Graph Topology
            </span>
            <h3 className="text-3xl md:text-4xl font-bold mb-4">Eliminate Institutional Blindspots</h3>
            <p className="text-base text-muted-foreground leading-relaxed">
              Trace a single bug from a front-end component through the API gateway down to the specific database schema migration that caused it. Complete visibility is no longer a luxury.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

import { createFileRoute } from "@tanstack/react-router";
import { Sidebar } from "@/components/landing/Sidebar";
import { TopBar } from "@/components/landing/TopBar";
import { GitBranch, CheckCircle2, AlertTriangle, AlertCircle, ArrowRight, LayoutGrid } from "lucide-react";

export const Route = createFileRoute("/insights")({
  head: () => ({
    meta: [
      { title: "Architecture Insights — CodeLens" },
      { name: "description", content: "Track dependency drift, complexity hotspots, and architectural deviations across services." },
      { property: "og:title", content: "Architecture Insights — CodeLens" },
      { property: "og:description", content: "Dependency drift and complexity insights for your engineering org." },
    ],
  }),
  component: InsightsPage,
});

type Severity = "ok" | "warn" | "error";

const SEV = {
  ok: { bar: "bg-secondary", text: "text-secondary", Icon: CheckCircle2 },
  warn: { bar: "bg-tertiary", text: "text-tertiary", Icon: AlertTriangle },
  error: { bar: "bg-error", text: "text-error", Icon: AlertCircle },
} as const;

const drift: { name: string; pattern: string; expected: string; actual: string; sev: Severity }[] = [
  { name: "Auth-Service-v2", pattern: "Event-Driven / Kafka", expected: "v2.4.1", actual: "v2.3.8-beta", sev: "warn" },
  { name: "Payment-Gateway", pattern: "REST / PCI-Compliant", expected: "v1.1.0", actual: "v1.1.0", sev: "ok" },
  { name: "Inventory-Worker", pattern: "Serverless / AWS Lambda", expected: "Node 20.x", actual: "Node 16.x", sev: "error" },
];

const hotspots: { name: string; module: string; score: number; sev: Severity }[] = [
  { name: "Payment-Processor", module: "/core/transaction-engine.ts", score: 42, sev: "error" },
  { name: "User-Auth-Flow", module: "/services/auth-validator.js", score: 28, sev: "warn" },
];

function InsightsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="ml-64 min-h-screen">
        <TopBar />
        <div className="pt-16 pb-20 px-8 md:px-12 space-y-8">
          <section className="glass-card rounded-xl p-6 max-w-4xl mx-auto">
            <div className="flex items-start justify-between mb-6 gap-4">
              <div>
                <h2 className="text-2xl font-bold text-primary mb-1">Dependency Drift</h2>
                <p className="text-muted-foreground text-sm">Monitoring architectural deviations and version mismatches across the ecosystem.</p>
              </div>
              <GitBranch className="w-8 h-8 text-primary/70 shrink-0" />
            </div>
            <div className="space-y-4">
              {drift.map((d) => {
                const s = SEV[d.sev];
                return (
                  <div key={d.name} className="flex items-center justify-between p-4 rounded-lg bg-surface-container-low border border-outline-variant">
                    <div className="flex items-center gap-4">
                      <div className={`w-2 h-12 rounded-full ${s.bar}`} />
                      <div>
                        <h3 className="font-semibold">{d.name}</h3>
                        <p className="text-xs text-muted-foreground font-mono-code">Pattern: {d.pattern}</p>
                      </div>
                    </div>
                    <div className="flex gap-8 text-right items-center">
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Expected</p>
                        <p className="font-mono-code text-sm">{d.expected}</p>
                      </div>
                      <div>
                        <p className={`text-[10px] uppercase tracking-wider ${s.text}`}>Actual</p>
                        <p className={`font-mono-code text-sm ${s.text}`}>{d.actual}</p>
                      </div>
                      <s.Icon className={`w-5 h-5 ${s.text}`} />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-6 pt-6 border-t border-outline-variant flex justify-end">
              <button className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-2 transition-colors">
                View Full Topology Report <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </section>

          <section className="glass-card rounded-xl p-6 max-w-4xl mx-auto">
            <div className="flex items-start justify-between mb-6 gap-4">
              <div>
                <h2 className="text-2xl font-bold text-primary mb-1">Cyclomatic Complexity</h2>
                <p className="text-muted-foreground text-sm">Identifying maintainability risks and logic hotspots across the codebase.</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Average Complexity</p>
                <p className="text-2xl font-bold text-secondary">8.4 <span className="text-xs font-normal">— Low Risk</span></p>
              </div>
            </div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">High Complexity Hotspots</h4>
            <div className="space-y-4">
              {hotspots.map((h) => {
                const s = SEV[h.sev];
                return (
                  <div key={h.name} className="flex items-center justify-between p-4 rounded-lg bg-surface-container-low border border-outline-variant">
                    <div className="flex items-center gap-4">
                      <div className={`w-2 h-12 rounded-full ${s.bar}`} />
                      <div>
                        <h3 className="font-semibold">{h.name}</h3>
                        <p className="text-xs text-muted-foreground font-mono-code">Module: {h.module}</p>
                      </div>
                    </div>
                    <div className="flex gap-8 text-right items-center">
                      <div>
                        <p className={`text-[10px] uppercase tracking-wider ${s.text}`}>Score</p>
                        <p className={`font-mono-code text-sm ${s.text}`}>{h.score}</p>
                      </div>
                      <s.Icon className={`w-5 h-5 ${s.text}`} />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-6 pt-6 border-t border-outline-variant flex justify-end">
              <button className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-2 transition-colors">
                View Complexity Heatmap <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

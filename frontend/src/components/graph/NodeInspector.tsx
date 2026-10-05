import { X, ArrowRight, LucideIcon } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export type InspectorNode = {
  id: string;
  title: string;
  kind: string;
  description: string;
  owner: string;
  updated: string;
  connections: number;
};

export type InspectorRelationship = {
  id: string;
  title: string;
  edgeType: string;
};

export type InspectorMeta = {
  label: string;
  Icon: LucideIcon;
  ringClass: string;
};

export function NodeInspector({
  node,
  meta,
  relationships,
  metrics,
  onClose,
  onJumpTo,
}: {
  node: InspectorNode;
  meta: InspectorMeta;
  relationships: InspectorRelationship[];
  metrics: { label: string; value: string }[];
  onClose: () => void;
  onJumpTo: (id: string) => void;
}) {
  const grouped = relationships.reduce<Record<string, InspectorRelationship[]>>((acc, r) => {
    (acc[r.edgeType] ??= []).push(r);
    return acc;
  }, {});

  return (
    <aside className="w-[360px] border-l border-border bg-surface/70 backdrop-blur-xl flex flex-col">
      <div className="flex items-center justify-between px-5 h-14 border-b border-border">
        <div className="text-xs uppercase tracking-widest text-muted-foreground font-mono-code">
          Inspector
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded hover:bg-white/5 text-muted-foreground hover:text-foreground"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-5 pb-3">
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-mono-code border border-white/10 ${meta.ringClass}`}
          >
            <meta.Icon className="w-3 h-3" /> {meta.label}
          </span>
        </div>
        <h2 className="text-xl font-bold">{node.title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{node.description}</p>
      </div>

      <Tabs defaultValue="overview" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="mx-5 grid grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="relationships">Relations</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="px-5 pb-5 pt-3 space-y-4 overflow-y-auto">
          <div className="rounded-lg border border-outline-variant bg-surface-container-low divide-y divide-white/5">
            <Row label="Owner" value={node.owner} />
            <Row label="Updated" value={node.updated} />
            <Row label="Type" value={meta.label} />
            <Row label="Connections" value={String(node.connections)} />
          </div>
          <button className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-primary/15 border border-primary/30 text-primary text-sm font-medium py-2.5 hover:bg-primary/25 transition-colors">
            View details <ArrowRight className="w-4 h-4" />
          </button>
        </TabsContent>

        <TabsContent value="relationships" className="px-5 pb-5 pt-3 space-y-4 overflow-y-auto">
          {Object.keys(grouped).length === 0 && (
            <p className="text-sm text-muted-foreground">No relationships.</p>
          )}
          {Object.entries(grouped).map(([type, items]) => (
            <div key={type}>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono-code mb-2">
                {type}
              </div>
              <div className="rounded-lg border border-outline-variant bg-surface-container-low divide-y divide-white/5">
                {items.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => onJumpTo(r.id)}
                    className="w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-white/5"
                  >
                    <span className="text-sm">{r.title}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="metrics" className="px-5 pb-5 pt-3 overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            {metrics.map((m) => (
              <div
                key={m.label}
                className="rounded-lg border border-outline-variant bg-surface-container-low p-3"
              >
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono-code">
                  {m.label}
                </div>
                <div className="mt-1 text-xl font-semibold">{m.value}</div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </aside>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <span className="text-[11px] uppercase tracking-wider text-muted-foreground font-mono-code">
        {label}
      </span>
      <span className="text-sm">{value}</span>
    </div>
  );
}

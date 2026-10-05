import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Sidebar } from "@/components/landing/Sidebar";
import { TopBar } from "@/components/landing/TopBar";
import { Plus, Minus, Focus, Code, Database, FileText, User, X, LucideIcon } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { GraphSearch, GraphSearchHandle } from "@/components/graph/GraphSearch";
import { ImportExportMenu } from "@/components/graph/ImportExportMenu";
import { LayoutControls } from "@/components/graph/LayoutControls";
import { ShortcutsDialog } from "@/components/graph/ShortcutsDialog";
import { NodeInspector, InspectorMeta } from "@/components/graph/NodeInspector";
import { edgeKey, pathEdgeKeys, shortestPath } from "@/lib/graph-path";
import { forceLayout, hierarchicalLayout, Positions } from "@/lib/graph-layout";
import { copyToClipboard, decodeShareState, encodeShareState, LayoutKind } from "@/lib/graph-share";

export const Route = createFileRoute("/graph")({
  head: () => ({
    meta: [
      { title: "Graph Explorer — CodeLens" },
      { name: "description", content: "Interactively explore the engineering knowledge graph: code, docs, services, and people." },
      { property: "og:title", content: "Graph Explorer — CodeLens" },
      { property: "og:description", content: "Explore code, docs, and people as a living knowledge graph." },
    ],
  }),
  component: GraphPage,
});

type NodeKind = "code" | "service" | "doc" | "person";
type Shape = "circle" | "rect";

type NodeData = {
  id: string;
  title: string;
  kind: NodeKind;
  shape: Shape;
  x: number;
  y: number;
  small?: boolean;
  description: string;
  owner: string;
  updated: string;
};

type EdgeData = { source: string; target: string; type: string; color: string; weight?: number };


const KIND_META: Record<NodeKind, { color: string; ringClass: string; label: string; Icon: LucideIcon }> = {
  code: { color: "#c0c1ff", ringClass: "text-primary", label: "Code", Icon: Code },
  service: { color: "#c0c1ff", ringClass: "text-primary", label: "Service", Icon: Database },
  doc: { color: "#4edea3", ringClass: "text-secondary", label: "Documentation", Icon: FileText },
  person: { color: "#ffb95f", ringClass: "text-tertiary", label: "Person", Icon: User },
};

function GraphPage() {
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [positions, setPositions] = useState<Positions>({});
  const [layout, setLayout] = useState<LayoutKind>("force");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedPair, setSelectedPair] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [zoom, setZoom] = useState(1);
  const [showLabels, setShowLabels] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const hydratedRef = useRef(false);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const searchRef = useRef<GraphSearchHandle | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [nodesRes, edgesRes] = await Promise.all([
          fetch("http://127.0.0.1:8000/api/v1/model/nodes"),
          fetch("http://127.0.0.1:8000/api/v1/model/edges")
        ]);
        
        if (!nodesRes.ok || !edgesRes.ok) throw new Error("Failed to fetch graph data");
        
        const backendNodes = await nodesRes.json();
        const backendEdges = await edgesRes.json();
        
        const mappedNodes: NodeData[] = backendNodes.map((n: any) => {
          let kind: NodeKind = "code";
          let shape: Shape = "circle";
          const t = n.type.toLowerCase();
          if (t.includes("service") || t.includes("system")) {
             kind = "service";
             shape = "rect";
          } else if (t.includes("doc") || t.includes("rfc") || t.includes("page")) {
             kind = "doc";
          } else if (t.includes("person") || t.includes("user")) {
             kind = "person";
          }
          
          return {
            id: n.id,
            title: n.name || n.id,
            kind,
            shape,
            x: Math.random() * 800,
            y: Math.random() * 600,
            small: kind === "person" || kind === "doc",
            description: n.description || "No description provided.",
            owner: n.properties?.owner || "Unknown",
            updated: "Recently"
          };
        });
        
        const mappedEdges: EdgeData[] = backendEdges.map((e: any) => ({
          source: e.source_id,
          target: e.target_id,
          type: e.type,
          color: "#c0c1ff",
          weight: Math.ceil((e.confidence || 0.5) * 3)
        }));
        
        setNodes(mappedNodes);
        setEdges(mappedEdges);
        
        // Initial layout
        const lNodes = mappedNodes.map((n) => ({ id: n.id, x: n.x, y: n.y, small: n.small }));
        const lEdges = mappedEdges.map((e) => ({ source: e.source, target: e.target, weight: e.weight }));
        const pos = forceLayout(lNodes, lEdges, { seed: 1234 });
        setPositions(pos);
        setLayout("force");
        
      } catch (err) {
        console.error("Error loading graph:", err);
        toast.error("Failed to load graph data from backend.");
      }
    }
    
    fetchData();
  }, []);

  const nodesById = useMemo(() => Object.fromEntries(nodes.map((n) => [n.id, n])), [nodes]);

  const queryLower = query.trim().toLowerCase();
  const matchingIds = useMemo(() => {
    if (!queryLower) return null;
    return new Set(
      nodes.filter((n) => n.title.toLowerCase().includes(queryLower) || n.kind.includes(queryLower)).map((n) => n.id),
    );
  }, [queryLower, nodes]);

  const path = useMemo(() => {
    if (selectedPair.length === 2) return shortestPath(edges, selectedPair[0], selectedPair[1]);
    return null;
  }, [selectedPair, edges]);
  const pathKeys = useMemo(() => (path ? pathEdgeKeys(path) : new Set<string>()), [path]);
  const pathNodes = useMemo(() => new Set(path ?? []), [path]);

  const selected = selectedId ? nodesById[selectedId] : null;

  // ---------- Layout ----------
  const applyLayout = useCallback(
    (kind: LayoutKind) => {
      if (kind === "manual") {
        setPositions(Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }])));
        return;
      }
      const layoutNodes = nodes.map((n) => ({ id: n.id, x: n.x, y: n.y, small: n.small }));
      const layoutEdges = edges.map((e) => ({ source: e.source, target: e.target, weight: e.weight }));
      const next =
        kind === "force"
          ? forceLayout(layoutNodes, layoutEdges, { seed: Date.now() & 0xffff })
          : hierarchicalLayout(layoutNodes, layoutEdges);
      setPositions(next);
    },
    [nodes, edges],
  );

  function handleLayoutChange(kind: LayoutKind) {
    setLayout(kind);
    applyLayout(kind);
  }

  // ---------- Selection ----------
  function handleNodeClick(id: string, shift: boolean) {
    setSelectedId(id);
    if (shift) {
      setSelectedPair((prev) => {
        if (prev.includes(id)) return prev.filter((x) => x !== id);
        return [...prev, id].slice(-2);
      });
    } else {
      setSelectedPair([id]);
    }
  }

  function clearSelection() {
    setSelectedId(null);
    setSelectedPair([]);
  }

  const relationships = useMemo(() => {
    if (!selected) return [];
    return edges
      .filter((e) => e.source === selected.id || e.target === selected.id)
      .map((e) => {
        const otherId = e.source === selected.id ? e.target : e.source;
        return { id: otherId, title: nodesById[otherId]?.title ?? otherId, edgeType: e.type };
      });
  }, [selected, edges, nodesById]);

  const metrics = useMemo(() => {
    if (!selected) return [];
    const inDeg = edges.filter((e) => e.target === selected.id).length;
    const outDeg = edges.filter((e) => e.source === selected.id).length;
    const total = inDeg + outDeg;
    return [
      { label: "In-degree", value: String(inDeg) },
      { label: "Out-degree", value: String(outDeg) },
      { label: "Centrality", value: (total / Math.max(nodes.length - 1, 1)).toFixed(2) },
      { label: "Change freq.", value: selected.updated },
    ];
  }, [selected, edges, nodes.length]);

  // ---------- Share link ----------
  // Hydrate from hash on mount
  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    if (typeof window === "undefined") return;
    const state = decodeShareState(window.location.hash);
    if (!state) return;
    if (state.layout) setLayout(state.layout);
    if (typeof state.query === "string") setQuery(state.query);
    if (state.selectedId !== undefined) setSelectedId(state.selectedId);
    if (Array.isArray(state.selectedPair)) setSelectedPair(state.selectedPair);
    if (typeof state.showLabels === "boolean") setShowLabels(state.showLabels);
    if (typeof state.zoom === "number") setZoom(state.zoom);
    if (state.positions) {
      const pos: Positions = {};
      for (const [k, v] of Object.entries(state.positions)) pos[k] = { x: v[0], y: v[1] };
      setPositions(pos);
    } else if (state.layout && state.layout !== "manual") {
      // Recompute non-manual layouts so they match across viewers
      requestAnimationFrame(() => applyLayout(state.layout));
    }
  }, [applyLayout]);

  // Persist state to hash
  useEffect(() => {
    if (typeof window === "undefined") return;
    const compactPos: Record<string, [number, number]> | undefined =
      layout === "manual"
        ? Object.fromEntries(Object.entries(positions).map(([k, v]) => [k, [round(v.x), round(v.y)]]))
        : undefined;
    const hash = "#" + encodeShareState({
      layout, query, selectedId, selectedPair, showLabels, zoom: round(zoom, 2), positions: compactPos,
    });
    if (window.location.hash !== hash) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search + hash);
    }
  }, [layout, query, selectedId, selectedPair, showLabels, zoom, positions]);

  function handleShare() {
    copyToClipboard(window.location.href).then((ok) => {
      if (ok) toast.success("Share link copied to clipboard");
      else toast.error("Unable to copy link");
    });
  }

  // ---------- Export / Import ----------
  function exportJson() {
    const payload = {
      nodes: nodes.map((n) => ({ id: n.id, title: n.title, kind: n.kind, shape: n.shape, small: n.small,
        x: positions[n.id]?.x ?? n.x, y: positions[n.id]?.y ?? n.y,
        description: n.description, owner: n.owner, updated: n.updated })),
      edges: edges.map((e) => ({ source: e.source, target: e.target, type: e.type, weight: e.weight, color: e.color })),
      viewport: { zoom, layout, selected: selectedId, selectedPair, showLabels },
      exportedAt: new Date().toISOString(),
    };
    downloadBlob(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }), "graph.json");
  }

  function exportPng() {
    const svg = svgRef.current;
    if (!svg) return;
    const clone = svg.cloneNode(true) as SVGSVGElement;
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const width = 1000;
    const height = 800;
    clone.setAttribute("width", String(width));
    clone.setAttribute("height", String(height));
    const xml = new XMLSerializer().serializeToString(clone);
    const svgBlob = new Blob([xml], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    const img = new Image();
    img.onload = () => {
      const dpr = 2;
      const canvas = document.createElement("canvas");
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "#0b1020";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => { if (blob) downloadBlob(blob, "graph.png"); }, "image/png");
    };
    img.onerror = () => URL.revokeObjectURL(url);
    img.src = url;
  }

  function importJson(text: string) {
    try {
      const data = JSON.parse(text);
      if (!Array.isArray(data?.nodes) || !Array.isArray(data?.edges)) throw new Error("Missing nodes/edges arrays");
      const newNodes: NodeData[] = data.nodes.map((n: NodeData) => ({
        id: String(n.id),
        title: String(n.title ?? n.id),
        kind: (["code", "service", "doc", "person"].includes(n.kind) ? n.kind : "code") as NodeKind,
        shape: (n.shape === "rect" ? "rect" : "circle") as Shape,
        x: Number(n.x ?? 500), y: Number(n.y ?? 400),
        small: !!n.small,
        description: String(n.description ?? ""),
        owner: String(n.owner ?? "—"),
        updated: String(n.updated ?? "—"),
      }));
      const newEdges: EdgeData[] = data.edges.map((e: EdgeData) => ({
        source: String(e.source),
        target: String(e.target),
        type: String(e.type ?? "related"),
        color: String(e.color ?? "#c0c1ff"),
        weight: e.weight !== undefined ? Number(e.weight) : undefined,
      }));
      setNodes(newNodes);
      setEdges(newEdges);
      const pos: Positions = Object.fromEntries(newNodes.map((n) => [n.id, { x: n.x, y: n.y }]));
      setPositions(pos);
      setLayout("manual");
      // Clear stale selections
      const ids = new Set(newNodes.map((n) => n.id));
      if (selectedId && !ids.has(selectedId)) setSelectedId(null);
      setSelectedPair((prev) => prev.filter((id) => ids.has(id)));
      toast.success(`Imported ${newNodes.length} nodes, ${newEdges.length} edges`);
    } catch (err) {
      toast.error(`Import failed: ${(err as Error).message}`);
    }
  }

  // ---------- Keyboard shortcuts ----------
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement | null)?.tagName;
      const isTyping = tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement | null)?.isContentEditable;
      if (e.key === "Escape") {
        clearSelection();
        return;
      }
      if (isTyping) return;
      if (e.key === "/") { e.preventDefault(); searchRef.current?.focus(); return; }
      if (e.key === "?") { e.preventDefault(); setShortcutsOpen(true); return; }
      if (e.key === "+" || e.key === "=") { e.preventDefault(); setZoom((z) => Math.min(2, +(z + 0.1).toFixed(2))); return; }
      if (e.key === "-" || e.key === "_") { e.preventDefault(); setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2))); return; }
      if (e.key === "0") { e.preventDefault(); setZoom(1); clearSelection(); return; }
      if (e.key.toLowerCase() === "l") { setShowLabels((v) => !v); return; }
      if (e.key.toLowerCase() === "r") { applyLayout(layout); return; }
      if (e.key.toLowerCase() === "s") { handleShare(); return; }
      if (e.key === "Tab") {
        e.preventDefault();
        const order = [...nodes].sort((a, b) => {
          const pa = positions[a.id] ?? { x: a.x, y: a.y };
          const pb = positions[b.id] ?? { x: b.x, y: b.y };
          return pa.y - pb.y || pa.x - pb.x;
        });
        if (order.length === 0) return;
        const idx = selectedId ? order.findIndex((n) => n.id === selectedId) : -1;
        const dir = e.shiftKey ? -1 : 1;
        const next = order[(idx + dir + order.length) % order.length];
        setSelectedId(next.id);
        setSelectedPair([next.id]);
        return;
      }
      if (e.key === "Enter" && selectedId) {
        if (e.shiftKey) {
          setSelectedPair((prev) => {
            if (prev.includes(selectedId)) return prev;
            return [...prev, selectedId].slice(-2);
          });
        }
        return;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, positions, selectedId, layout, applyLayout]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="ml-64 h-screen flex flex-col">
        <TopBar />
        <div className="pt-16 flex-1 flex">
          <div className="flex-1 relative overflow-hidden bg-surface-container-lowest">
            <div
              className="absolute inset-0 pointer-events-none opacity-[0.06]"
              style={{ backgroundImage: "radial-gradient(#dae2fd 1px, transparent 1px)", backgroundSize: "32px 32px" }}
            />

            {/* Top-left: search + legend */}
            <div className="absolute top-6 left-6 z-10 flex flex-col gap-3">
              <GraphSearch
                ref={searchRef}
                nodes={nodes.map((n) => ({ id: n.id, title: n.title, kind: KIND_META[n.kind].label }))}
                query={query}
                onQueryChange={setQuery}
                onSelect={(id) => { setSelectedId(id); setSelectedPair([id]); setQuery(""); }}
              />
              <div className="glass-card px-3 py-1.5 rounded-full flex items-center gap-4 text-[12px] font-medium w-fit">
                <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-primary mr-2" /> Code</div>
                <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-secondary mr-2" /> Docs</div>
                <div className="flex items-center"><span className="w-2 h-2 rounded-full bg-tertiary mr-2" /> People</div>
              </div>
            </div>

            {/* Top-right toolbar */}
            <div className="absolute top-6 right-6 z-10 flex items-center gap-2 flex-wrap justify-end">
              <LayoutControls
                layout={layout}
                onLayoutChange={handleLayoutChange}
                onRerun={() => applyLayout(layout)}
                showLabels={showLabels}
                onToggleLabels={() => setShowLabels((v) => !v)}
                onShare={handleShare}
              />
              {(selectedId || selectedPair.length > 0) && (
                <button
                  onClick={clearSelection}
                  className="glass-card rounded-lg px-3 py-2 inline-flex items-center gap-2 text-sm hover:bg-white/5"
                >
                  <X className="w-4 h-4" /> Clear
                </button>
              )}
              <ImportExportMenu onExportJson={exportJson} onExportPng={exportPng} onImportJson={importJson} />
              <ShortcutsDialog open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
            </div>

            {/* Hints */}
            {selectedPair.length === 1 && !path && (
              <div className="absolute bottom-6 right-6 z-10 glass-card rounded-lg px-3 py-2 text-xs text-muted-foreground">
                Shift-click another node to highlight a path
              </div>
            )}
            {path && (
              <div className="absolute bottom-6 right-6 z-10 glass-card rounded-lg px-3 py-2 text-xs max-w-md">
                Path: <span className="font-mono-code text-primary">{path.map((id) => nodesById[id]?.title ?? id).join(" → ")}</span>
              </div>
            )}
            {selectedPair.length === 2 && !path && (
              <div className="absolute bottom-6 right-6 z-10 glass-card rounded-lg px-3 py-2 text-xs text-destructive">
                No path between selected nodes
              </div>
            )}

            {/* Zoom controls */}
            <div className="absolute bottom-6 left-6 z-10">
              <div className="glass-card flex flex-col p-1 rounded-lg space-y-1">
                <button onClick={() => setZoom((z) => Math.min(2, +(z + 0.1).toFixed(2)))} className="p-2 hover:bg-white/5 rounded text-muted-foreground hover:text-foreground"><Plus className="w-4 h-4" /></button>
                <button onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))} className="p-2 hover:bg-white/5 rounded text-muted-foreground hover:text-foreground"><Minus className="w-4 h-4" /></button>
                <button onClick={() => { setZoom(1); clearSelection(); }} className="p-2 hover:bg-white/5 rounded text-muted-foreground hover:text-foreground"><Focus className="w-4 h-4" /></button>
              </div>
            </div>

            <svg ref={svgRef} className="w-full h-full" viewBox="0 0 1000 800" preserveAspectRatio="xMidYMid meet">
              <defs>
                <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="oklch(0.66 0.21 275)" stopOpacity="0.12" />
                  <stop offset="100%" stopColor="oklch(0.66 0.21 275)" stopOpacity="0" />
                </radialGradient>
              </defs>
              <g transform={`translate(500 400) scale(${zoom}) translate(-500 -400)`}>
                <circle cx="500" cy="400" r="320" fill="url(#bgGlow)" />

                {edges.map((e) => {
                  const s = positions[e.source]; const t = positions[e.target];
                  if (!s || !t) return null;
                  const k = edgeKey(e.source, e.target);
                  const onPath = pathKeys.has(k);
                  const dim = (matchingIds && !(matchingIds.has(e.source) && matchingIds.has(e.target))) || (path && !onPath);
                  const mx = (s.x + t.x) / 2;
                  const my = (s.y + t.y) / 2;
                  const labelVisible = showLabels || onPath;
                  return (
                    <g key={k} style={{ transition: "opacity 200ms" }} opacity={dim ? 0.12 : 1}>
                      <line
                        x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                        stroke={onPath ? "oklch(0.66 0.21 275)" : e.color}
                        strokeWidth={onPath ? 3 : 1.4}
                        opacity={onPath ? 0.95 : 0.5}
                        className="cursor-pointer hover:opacity-100"
                        style={{ transition: "stroke-width 150ms" }}
                      >
                        <title>{`${nodesById[e.source]?.title} — ${e.type}${e.weight ? ` (w=${e.weight})` : ""} → ${nodesById[e.target]?.title}`}</title>
                      </line>
                      {labelVisible && (
                        <g transform={`translate(${mx} ${my})`} pointerEvents="none">
                          <rect x={-getLabelWidth(e) / 2} y={-9} width={getLabelWidth(e)} height={18} rx={9}
                            fill="#0f1530" stroke={onPath ? "oklch(0.66 0.21 275)" : "rgba(255,255,255,0.12)"} strokeWidth={1} />
                          <text x={0} y={3} textAnchor="middle" fill={onPath ? "#c0c1ff" : "#a8b3cf"}
                            className="text-[10px] font-mono-code uppercase tracking-tight">
                            {e.type}{e.weight !== undefined ? ` · w=${e.weight}` : ""}
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}

                {nodes.map((n) => {
                  const p = positions[n.id] ?? { x: n.x, y: n.y };
                  const dim = (matchingIds && !matchingIds.has(n.id)) || (path && !pathNodes.has(n.id));
                  const active = selectedId === n.id || selectedPair.includes(n.id);
                  return (
                    <g key={n.id} transform={`translate(${p.x} ${p.y})`} style={{ transition: "transform 350ms ease" }}>
                      <GraphNode node={n} active={active} dim={!!dim} onClick={(shift) => handleNodeClick(n.id, shift)} />
                    </g>
                  );
                })}
              </g>
            </svg>
          </div>

          {selected && (
            <NodeInspector
              node={{ ...selected, connections: edges.filter((e) => e.source === selected.id || e.target === selected.id).length }}
              meta={KIND_META[selected.kind] as InspectorMeta}
              relationships={relationships}
              metrics={metrics}
              onClose={clearSelection}
              onJumpTo={(id) => { setSelectedId(id); setSelectedPair([id]); }}
            />
          )}
        </div>
      </main>
      <Toaster />
    </div>
  );
}

function getLabelWidth(e: EdgeData): number {
  const text = e.type + (e.weight !== undefined ? ` · w=${e.weight}` : "");
  return Math.max(40, text.length * 6.2 + 14);
}

function GraphNode({
  node, active, dim, onClick,
}: { node: NodeData; active: boolean; dim: boolean; onClick: (shift: boolean) => void }) {
  const meta = KIND_META[node.kind];
  const r = node.small ? 24 : 30;
  const opacity = dim ? 0.25 : 1;
  const handler = (e: React.MouseEvent) => onClick(e.shiftKey);

  if (node.shape === "rect") {
    const w = 60, h = 60;
    return (
      <g className="cursor-pointer" opacity={opacity} onClick={handler} style={{ transition: "opacity 200ms" }}>
        <rect x={-w / 2 - 4} y={-h / 2 - 4} width={w + 8} height={h + 8} rx={10} fill={meta.color} opacity={active ? 0.18 : 0} />
        <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={8} fill="#171f33" stroke={meta.color} strokeWidth={active ? 3 : 2} />
        <foreignObject x={-10} y={-10} width={20} height={20} pointerEvents="none">
          <div className={`flex items-center justify-center ${meta.ringClass}`}>
            <meta.Icon className="w-5 h-5" />
          </div>
        </foreignObject>
        <text x={0} y={h / 2 + 20} textAnchor="middle" fill={meta.color} className="text-[11px] font-mono-code uppercase tracking-tight">
          {node.title}
        </text>
      </g>
    );
  }

  return (
    <g className="cursor-pointer" opacity={opacity} onClick={handler} style={{ transition: "opacity 200ms" }}>
      <circle cx={0} cy={0} r={r + 6} fill={meta.color} opacity={active ? 0.18 : 0} />
      <circle cx={0} cy={0} r={r} fill="#171f33" stroke={meta.color} strokeWidth={active ? 3 : 2} />
      <foreignObject x={-10} y={-10} width={20} height={20} pointerEvents="none">
        <div className={`flex items-center justify-center ${meta.ringClass}`}>
          <meta.Icon className="w-5 h-5" />
        </div>
      </foreignObject>
      <text x={0} y={r + 18} textAnchor="middle" fill={meta.color} className="text-[11px] font-mono-code uppercase tracking-tight">
        {node.title}
      </text>
    </g>
  );
}

function round(n: number, p = 1): number {
  const f = Math.pow(10, p);
  return Math.round(n * f) / f;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

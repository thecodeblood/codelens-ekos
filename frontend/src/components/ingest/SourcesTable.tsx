import { Database, FileText, CloudOff, MoreHorizontal, Filter, RefreshCw, FolderArchive, type LucideIcon } from "lucide-react";

export type SourceStatus =
  | { kind: "synced" }
  | { kind: "indexing"; progress: number }
  | { kind: "failed" }
  | { kind: "queued" };

export type SourceRow = {
  id: string;
  name: string;
  type: string;
  icon: LucideIcon;
  iconTone: string;
  status: SourceStatus;
  lastSync: string;
};

export const ICONS = { Database, FileText, CloudOff, FolderArchive };

function StatusCell({ status }: { status: SourceStatus }) {
  if (status.kind === "synced") {
    return (
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 bg-secondary rounded-full animate-pulse" />
        <span className="text-secondary font-medium text-sm">Synced</span>
      </div>
    );
  }
  if (status.kind === "indexing") {
    return (
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
          <span className="text-primary font-medium text-sm">Indexing {status.progress}%</span>
        </div>
        <div className="w-24 h-1 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full bg-primary" style={{ width: `${status.progress}%` }} />
        </div>
      </div>
    );
  }
  if (status.kind === "failed") {
    return (
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 bg-destructive rounded-full" />
        <span className="text-destructive font-medium text-sm">Failed</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <span className="w-2 h-2 bg-muted-foreground rounded-full" />
      <span className="text-muted-foreground font-medium text-sm">Queued</span>
    </div>
  );
}

export function SourcesTable({
  rows,
  onRefresh,
}: {
  rows: SourceRow[];
  onRefresh?: () => void;
}) {
  const active = rows.filter((r) => r.status.kind !== "failed").length;
  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="p-6 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-lg">Connected Entities</h3>
          <span className="bg-secondary/10 text-secondary text-[11px] px-2 py-0.5 rounded border border-secondary/20 uppercase tracking-wider">
            {active} Active
          </span>
        </div>
        <div className="flex gap-2">
          <button className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground" aria-label="Filter">
            <Filter className="w-4 h-4" />
          </button>
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-white/5 rounded-lg text-muted-foreground"
            aria-label="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/[0.02]">
              {["Source Entity", "Type", "Status", "Last Sync", ""].map((h, i) => (
                <th
                  key={i}
                  className={`px-6 py-4 text-xs text-muted-foreground uppercase tracking-wider ${i === 4 ? "text-right" : ""}`}
                >
                  {h || "Actions"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((r) => (
              <tr key={r.id} className="hover:bg-white/5 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <r.icon className={`w-4 h-4 ${r.iconTone}`} />
                    <span className="text-sm font-semibold">{r.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className="text-xs px-2 py-1 bg-white/5 rounded text-muted-foreground">{r.type}</span>
                </td>
                <td className="px-6 py-4">
                  <StatusCell status={r.status} />
                </td>
                <td className="px-6 py-4 text-muted-foreground text-sm">{r.lastSync}</td>
                <td className="px-6 py-4 text-right">
                  <button className="text-muted-foreground hover:text-primary" aria-label="More">
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

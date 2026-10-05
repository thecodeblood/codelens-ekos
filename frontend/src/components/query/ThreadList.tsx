import { Link, useParams } from "@tanstack/react-router";
import { Plus, Trash2, MessagesSquare } from "lucide-react";
import { useThreads, createThread, deleteThread } from "@/lib/query-store";
import { useNavigate } from "@tanstack/react-router";

export function ThreadList() {
  const threads = useThreads();
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { threadId?: string };
  const activeId = params.threadId;

  return (
    <aside className="w-64 border-r border-border bg-surface/40 backdrop-blur-xl flex flex-col">
      <div className="px-4 h-14 flex items-center justify-between border-b border-border">
        <div className="text-xs uppercase tracking-widest text-muted-foreground font-mono-code">Threads</div>
        <button
          onClick={() => {
            const t = createThread();
            navigate({ to: "/query/$threadId", params: { threadId: t.id } });
          }}
          className="inline-flex items-center gap-1 rounded-md bg-primary/15 border border-primary/30 text-primary text-xs px-2 py-1 hover:bg-primary/25"
        >
          <Plus className="w-3.5 h-3.5" /> New
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {threads.length === 0 && (
          <div className="text-xs text-muted-foreground px-3 py-6 text-center">
            No conversations yet. Start by asking a question.
          </div>
        )}
        {threads.map((t) => {
          const isActive = t.id === activeId;
          return (
            <div
              key={t.id}
              className={`group rounded-md px-2 py-2 flex items-start gap-2 ${
                isActive
                  ? "bg-primary/10 border border-primary/20"
                  : "hover:bg-white/5 border border-transparent"
              }`}
            >
              <Link
                to="/query/$threadId"
                params={{ threadId: t.id }}
                className="flex-1 min-w-0 flex items-start gap-2"
              >
                <MessagesSquare className={`w-3.5 h-3.5 mt-0.5 ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                <div className="min-w-0">
                  <div className={`text-sm truncate ${isActive ? "text-foreground" : "text-foreground/90"}`}>
                    {t.title}
                  </div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono-code">
                    {new Date(t.updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                </div>
              </Link>
              <button
                onClick={() => {
                  deleteThread(t.id);
                  if (isActive) navigate({ to: "/query" });
                }}
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive p-1"
                aria-label="Delete thread"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { createThread, useThreads } from "@/lib/query-store";

export const Route = createFileRoute("/query/")({
  component: QueryIndex,
});

function QueryIndex() {
  const threads = useThreads();
  const navigate = useNavigate();
  useEffect(() => {
    const target = threads[0] ?? createThread();
    navigate({ to: "/query/$threadId", params: { threadId: target.id }, replace: true });
  }, [threads, navigate]);
  return (
    <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
      Loading…
    </div>
  );
}

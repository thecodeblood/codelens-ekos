import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { sendUserMessage, useThread, createThread } from "@/lib/query-store";
import { MessageBubble } from "@/components/query/MessageBubble";
import { Composer, ComposerHandle } from "@/components/query/Composer";
import { EmptyState } from "@/components/query/EmptyState";
import { GraphTraversalPanel } from "@/components/query/GraphTraversalPanel";

export const Route = createFileRoute("/query/$threadId")({
  component: QueryThread,
});

function QueryThread() {
  const { threadId } = Route.useParams();
  const thread = useThread(threadId);
  const navigate = useNavigate();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const composerRef = useRef<ComposerHandle | null>(null);

  // Auto-scroll to latest message on update
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [thread?.messages.length, thread?.messages[thread.messages.length - 1]?.pending]);

  // If the URL points at a non-existent thread, create a fresh one and redirect.
  useEffect(() => {
    if (!thread) {
      const t = createThread();
      navigate({ to: "/query/$threadId", params: { threadId: t.id }, replace: true });
    }
  }, [thread, navigate]);

  // ⌘K / Ctrl+K focuses the composer
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        composerRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Focus the composer when the thread changes
  useEffect(() => {
    composerRef.current?.focus();
  }, [threadId]);

  if (!thread) return null;

  const lastMessage = thread.messages[thread.messages.length - 1];
  const sending = !!lastMessage?.pending;

  return (
    <>
      <div className="flex-1 flex flex-col relative overflow-hidden">
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6">
          <div className="max-w-3xl mx-auto w-full space-y-6 pt-8 pb-48">
            {thread.messages.length === 0 ? (
              <EmptyState />
            ) : (
              thread.messages.map((m) => <MessageBubble key={m.id} message={m} />)
            )}
          </div>
        </div>
        <Composer
          ref={composerRef}
          disabled={sending}
          onSend={(text) => {
            void sendUserMessage(thread.id, text);
          }}
        />
      </div>
      <GraphTraversalPanel messages={thread.messages} />
    </>
  );
}

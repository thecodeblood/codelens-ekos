import { createFileRoute, Outlet } from "@tanstack/react-router";
import { Sidebar } from "@/components/landing/Sidebar";
import { TopBar } from "@/components/landing/TopBar";
import { ThreadList } from "@/components/query/ThreadList";

export const Route = createFileRoute("/query")({
  head: () => ({
    meta: [
      { title: "AI Query — CodeLens" },
      { name: "description", content: "Ask natural-language questions about your codebase and traverse the engineering knowledge graph." },
      { property: "og:title", content: "AI Query — CodeLens" },
      { property: "og:description", content: "Conversational interface over the CodeLens knowledge graph." },
    ],
  }),
  component: QueryLayout,
});

function QueryLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="ml-64 h-screen flex flex-col">
        <TopBar />
        <div className="pt-16 flex-1 flex overflow-hidden">
          <ThreadList />
          <Outlet />
        </div>
      </main>
    </div>
  );
}

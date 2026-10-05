import { createFileRoute } from "@tanstack/react-router";
import { Sidebar } from "@/components/landing/Sidebar";
import { TopBar } from "@/components/landing/TopBar";
import { Hero } from "@/components/landing/Hero";
import { Features } from "@/components/landing/Features";
import { Integrations } from "@/components/landing/Integrations";
import { CTASection } from "@/components/landing/CTASection";
import { Footer } from "@/components/landing/Footer";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "CodeLens — Engineering Knowledge Operating System" },
      { name: "description", content: "Unify codebases, documentation, and operational data into a deterministic, queryable knowledge graph." },
      { property: "og:title", content: "CodeLens — Engineering Knowledge OS" },
      { property: "og:description", content: "Unify codebases, docs, and ops data into a queryable knowledge graph." },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <main className="ml-64 min-h-screen relative">
        <TopBar />
        <div className="pt-16 pb-20 px-8 md:px-12">
          <Hero />
          <Features />
          <Integrations />
          <CTASection />
          <Footer />
        </div>
      </main>
    </div>
  );
}

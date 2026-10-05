import { Box } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border py-12 mt-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
        <div className="col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-primary/15 border border-primary/30 flex items-center justify-center">
              <Box className="w-4 h-4 text-primary" />
            </div>
            <span className="font-bold">CodeLens</span>
          </div>
          <p className="text-sm text-muted-foreground max-w-xs">
            The engineering knowledge operating system for modern software organizations.
          </p>
        </div>
        {[
          { title: "Product", links: ["Graph", "Ingest", "Query", "Pricing"] },
          { title: "Resources", links: ["Docs", "API", "Changelog", "Status"] },
          { title: "Company", links: ["About", "Careers", "Security", "Contact"] },
        ].map((col) => (
          <div key={col.title}>
            <div className="font-mono-code text-[10px] uppercase tracking-widest text-muted-foreground mb-3">{col.title}</div>
            <ul className="space-y-2">
              {col.links.map((l) => (
                <li key={l}>
                  <a href="#" className="text-sm text-foreground/80 hover:text-primary">{l}</a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="mt-12 pt-6 border-t border-border flex flex-col md:flex-row items-center justify-between gap-3 text-xs text-muted-foreground">
        <div>© 2026 CodeLens, Inc. All rights reserved.</div>
        <div className="font-mono-code">v1.0.4 · build a7f9c</div>
      </div>
    </footer>
  );
}

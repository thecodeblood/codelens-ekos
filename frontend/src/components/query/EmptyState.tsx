import { Sparkles } from "lucide-react";

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center opacity-70">
      <div className="w-14 h-14 rounded-2xl bg-primary/15 border border-primary/30 flex items-center justify-center glow-primary mb-5">
        <Sparkles className="w-6 h-6 text-primary" />
      </div>
      <h2 className="text-2xl font-bold tracking-tight">How can I help you explore the codebase?</h2>
      <p className="text-sm text-muted-foreground mt-2">
        I have indexed <span className="font-mono-code text-foreground">4,520</span> services and mapped{" "}
        <span className="font-mono-code text-foreground">12,042</span> call edges.
      </p>
    </div>
  );
}

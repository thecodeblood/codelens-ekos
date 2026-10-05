import { Github, GitMerge, ListTodo, FileText } from "lucide-react";

const integrations = [
  { icon: Github, name: "GitHub", color: "text-primary" },
  { icon: GitMerge, name: "GitLab", color: "text-secondary" },
  { icon: ListTodo, name: "Jira", color: "text-tertiary" },
  { icon: FileText, name: "Confluence", color: "text-primary" },
];

export function Integrations() {
  return (
    <section className="py-20 border-t border-border">
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Seamless Ingestion Ecosystem</h2>
        <p className="text-sm text-muted-foreground">Connect your stack and start modeling in minutes.</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {integrations.map((i) => (
          <button
            key={i.name}
            className="glass-card p-6 rounded-lg flex items-center gap-4 justify-center grayscale hover:grayscale-0 hover:border-primary/30 transition-all cursor-pointer"
          >
            <i.icon className={`w-5 h-5 ${i.color}`} />
            <span className="font-mono-code text-sm font-bold">{i.name}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

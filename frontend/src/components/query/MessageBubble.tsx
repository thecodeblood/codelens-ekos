import { Sparkles } from "lucide-react";
import type { Message } from "@/lib/query-store";

export function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary/15 border border-primary/25 px-4 py-3 text-sm text-foreground">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-4">
      <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center shrink-0 border border-primary/30 ai-glow">
        <Sparkles className="w-4 h-4 text-primary" />
      </div>
      <div className="glass-panel-accent p-6 rounded-xl w-full">
        {message.pending ? (
          <ThinkingShimmer />
        ) : (
          <AssistantBody message={message} />
        )}
      </div>
    </div>
  );
}

function AssistantBody({ message }: { message: Message }) {
  return (
    <div>
      {message.heading && (
        <h3 className="text-primary text-lg font-semibold mb-3">{message.heading}</h3>
      )}
      {message.text && (
        <p className="text-sm text-foreground/90 leading-relaxed mb-4">
          <InlineMd text={message.text} />
        </p>
      )}
      {message.bullets && message.bullets.length > 0 && (
        <ul className="space-y-2.5 text-sm text-muted-foreground">
          {message.bullets.map((b, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-primary mt-1 leading-none">●</span>
              <span>
                <strong className="text-foreground">{b.label}:</strong> {b.body}
              </span>
            </li>
          ))}
        </ul>
      )}
      {message.codeBlock && (
        <div className="mt-5 p-4 bg-background/80 rounded-lg border border-white/5 font-mono-code text-[12px] leading-relaxed">
          <div className="flex justify-between items-center mb-2 border-b border-white/10 pb-2">
            <span className="text-muted-foreground/70 text-[11px] uppercase tracking-wider">
              {message.codeBlock.title}
            </span>
            <span className="text-secondary text-[11px]">{message.codeBlock.language}</span>
          </div>
          <CypherCode code={message.codeBlock.code} />
        </div>
      )}
    </div>
  );
}

const CYPHER_KEYWORDS = new Set([
  "MATCH", "RETURN", "WHERE", "ORDER BY", "LIMIT", "CALL", "AS", "WITH",
  "UNWIND", "CREATE", "MERGE", "SET", "DELETE",
]);
const CYPHER_SPLIT = /\b(MATCH|RETURN|WHERE|ORDER BY|LIMIT|CALL|AS|WITH|UNWIND|CREATE|MERGE|SET|DELETE)\b/;

function CypherCode({ code }: { code: string }) {
  const parts: { type: "kw" | "str" | "txt"; value: string }[] = [];
  const rest = code;
  const re = /'[^']*'|"[^"]*"/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(rest))) {
    if (m.index > last) parts.push({ type: "txt", value: rest.slice(last, m.index) });
    parts.push({ type: "str", value: m[0] });
    last = m.index + m[0].length;
  }
  if (last < rest.length) parts.push({ type: "txt", value: rest.slice(last) });

  return (
    <pre className="whitespace-pre-wrap break-words">
      {parts.map((p, i) => {
        if (p.type === "str") return <span key={i} className="text-tertiary">{p.value}</span>;
        const chunks = p.value.split(CYPHER_SPLIT);
        return (
          <span key={i}>
            {chunks.map((c, j) =>
              CYPHER_KEYWORDS.has(c) ? (
                <span key={j} className="text-primary font-semibold">{c}</span>
              ) : (
                <span key={j}>{c}</span>
              ),
            )}
          </span>
        );
      })}
    </pre>
  );
}

/** Minimal inline markdown: **bold** and `code`. */
function InlineMd({ text }: { text: string }) {
  const nodes: React.ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*|`([^`]+)`/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    if (m[1]) nodes.push(<strong key={i++} className="text-foreground">{m[1]}</strong>);
    else if (m[2]) nodes.push(<code key={i++} className="font-mono-code text-[12.5px] text-primary bg-primary/10 px-1.5 py-0.5 rounded">{m[2]}</code>);
    last = m.index + m[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return <>{nodes}</>;
}

function ThinkingShimmer() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-pulse" style={{ animationDelay: "0ms" }} />
        <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-pulse" style={{ animationDelay: "150ms" }} />
        <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-pulse" style={{ animationDelay: "300ms" }} />
      </div>
      <span className="text-sm text-muted-foreground">Traversing the knowledge graph…</span>
    </div>
  );
}

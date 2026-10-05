import { Search } from "lucide-react";
import { forwardRef, useImperativeHandle, useMemo, useRef, useState } from "react";

export type SearchableNode = { id: string; title: string; kind: string };

export type GraphSearchHandle = { focus: () => void };

export const GraphSearch = forwardRef<
  GraphSearchHandle,
  {
    nodes: SearchableNode[];
    query: string;
    onQueryChange: (q: string) => void;
    onSelect: (id: string) => void;
  }
>(function GraphSearch({ nodes, query, onQueryChange, onSelect }, ref) {
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  useImperativeHandle(ref, () => ({ focus: () => inputRef.current?.focus() }));

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return nodes
      .filter((n) => n.title.toLowerCase().includes(q) || n.kind.toLowerCase().includes(q))
      .slice(0, 5);
  }, [nodes, query]);

  return (
    <div className="relative w-72">
      <div className="glass-card rounded-lg flex items-center px-3 py-2 gap-2">
        <Search className="w-4 h-4 text-muted-foreground" />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            onQueryChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          placeholder="Search nodes…  (press / )"
          className="bg-transparent flex-1 text-sm outline-none placeholder:text-muted-foreground"
        />
        {query && (
          <button
            onClick={() => onQueryChange("")}
            className="text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground"
          >
            clear
          </button>
        )}
      </div>
      {open && matches.length > 0 && (
        <div className="absolute left-0 right-0 mt-2 glass-card rounded-lg overflow-hidden z-20">
          {matches.map((m) => (
            <button
              key={m.id}
              onMouseDown={(e) => {
                e.preventDefault();
                onSelect(m.id);
                setOpen(false);
              }}
              className="w-full flex items-center justify-between px-3 py-2 text-left text-sm hover:bg-white/5"
            >
              <span>{m.title}</span>
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono-code">
                {m.kind}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
});

import { forwardRef, useImperativeHandle, useRef, useState, KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { SUGGESTIONS } from "@/lib/query-mocks";

export type ComposerHandle = { focus: () => void };

export const Composer = forwardRef<
  ComposerHandle,
  { onSend: (text: string) => void; disabled?: boolean }
>(function Composer({ onSend, disabled }, ref) {
  const [value, setValue] = useState("");
  const taRef = useRef<HTMLTextAreaElement | null>(null);
  useImperativeHandle(ref, () => ({ focus: () => taRef.current?.focus() }));

  function submit(text?: string) {
    const t = (text ?? value).trim();
    if (!t || disabled) return;
    onSend(t);
    setValue("");
  }

  function onKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl px-4 z-40">
      <div className="glass-card ai-glow p-3 rounded-2xl shadow-2xl">
        <div className="flex items-end gap-3">
          <div className="flex-grow relative">
            <textarea
              ref={taRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={onKey}
              rows={1}
              placeholder="e.g., 'Trace the call chain for the Auth service' or 'Summarize the Checkout domain'"
              className="w-full bg-background/60 border border-white/10 rounded-xl py-3.5 pl-5 pr-24 text-sm text-foreground focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none resize-none max-h-40"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <kbd className="hidden md:inline-flex h-6 items-center gap-1 rounded border border-white/20 bg-white/5 px-1.5 font-mono-code text-[10px] text-muted-foreground">
                <span>⌘</span>K
              </kbd>
              <button
                onClick={() => submit()}
                disabled={disabled || !value.trim()}
                className="bg-primary text-primary-foreground p-2 rounded-lg hover:scale-105 active:scale-95 transition-transform flex items-center justify-center disabled:opacity-40 disabled:hover:scale-100"
                aria-label="Send"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-3 px-1 flex-wrap">
          <span className="text-[10px] uppercase font-bold text-muted-foreground/70 tracking-wider">
            Suggestions:
          </span>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => submit(s)}
              className="text-xs bg-white/5 hover:bg-white/10 px-2 py-1 rounded border border-white/5 transition-colors text-muted-foreground"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
});

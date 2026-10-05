import { useRef } from "react";
import { Download, FileJson, ImageDown, Upload } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function ImportExportMenu({
  onExportJson,
  onExportPng,
  onImportJson,
}: {
  onExportJson: () => void;
  onExportPng: () => void;
  onImportJson: (text: string) => void;
}) {
  const fileRef = useRef<HTMLInputElement | null>(null);

  return (
    <>
      <input
        ref={fileRef}
        type="file"
        accept="application/json"
        className="hidden"
        onChange={async (e) => {
          const f = e.target.files?.[0];
          if (!f) return;
          const text = await f.text();
          onImportJson(text);
          e.target.value = "";
        }}
      />
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="glass-card rounded-lg px-3 py-2 inline-flex items-center gap-2 text-sm hover:bg-white/5">
            <Download className="w-4 h-4" /> Export
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem onClick={onExportJson}>
            <FileJson className="w-4 h-4 mr-2" /> Download JSON
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onExportPng}>
            <ImageDown className="w-4 h-4 mr-2" /> Download PNG
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => fileRef.current?.click()}>
            <Upload className="w-4 h-4 mr-2" /> Import JSON…
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}

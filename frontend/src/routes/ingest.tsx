import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState, useEffect } from "react";
import { Sidebar } from "@/components/landing/Sidebar";
import { TopBar } from "@/components/landing/TopBar";
import { ConnectionCard } from "@/components/ingest/ConnectionCard";
import { SourcesTable, ICONS, type SourceRow } from "@/components/ingest/SourcesTable";
import { Terminal, FolderArchive, BookOpen, ChevronDown, Cloud, Shield, UploadCloud } from "lucide-react";

export const Route = createFileRoute("/ingest")({
  head: () => ({
    meta: [
      { title: "Ingest Sources — CodeLens" },
      { name: "description", content: "Connect Git repos, upload local source archives, and index documentation into your CodeLens knowledge graph." },
      { property: "og:title", content: "Ingest Sources — CodeLens" },
      { property: "og:description", content: "Connect your engineering ecosystem to CodeLens." },
    ],
  }),
  component: IngestPage,
});

const INITIAL_ROWS: SourceRow[] = [
  { id: "1", name: "auth-service", type: "GitHub Repo", icon: ICONS.Database, iconTone: "text-secondary", status: { kind: "synced" }, lastSync: "2 min ago" },
  { id: "2", name: "api-docs-v2", type: "Confluence", icon: ICONS.FileText, iconTone: "text-primary", status: { kind: "indexing", progress: 45 }, lastSync: "In progress" },
  { id: "3", name: "legacy-gateway", type: "Bitbucket", icon: ICONS.CloudOff, iconTone: "text-destructive", status: { kind: "failed" }, lastSync: "4 hours ago" },
  { id: "4", name: "design-system", type: "Notion", icon: ICONS.FileText, iconTone: "text-primary", status: { kind: "synced" }, lastSync: "1 hour ago" },
];

const DOC_SOURCES = ["Confluence Space", "Notion Workspace", "Swagger / OpenAPI URL", "Static Site (Docusaurus)"];

function IngestPage() {
  const [rows, setRows] = useState<SourceRow[]>(INITIAL_ROWS);
  const [gitUrl, setGitUrl] = useState("");
  const [docSource, setDocSource] = useState(DOC_SOURCES[0]);
  const [docUrl, setDocUrl] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/v1/sources")
      .then(r => r.json())
      .then(data => {
        const fetchedRows = data.map((d: any) => ({
          id: d.id,
          name: d.name,
          type: d.type,
          icon: ICONS.Database,
          iconTone: "text-secondary",
          status: { kind: d.status === "error" ? "failed" : d.status === "ingested" ? "synced" : "indexing" },
          lastSync: d.last_ingested || "Never"
        }));
        setRows(fetchedRows);
      })
      .catch(console.error);
  }, []);

  const addRow = async (row: Omit<SourceRow, "id">, uri: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: row.type, uri: uri, name: row.name })
      });
      const data = await res.json();
      if (data.id) {
        setRows((r) => [{ ...row, id: data.id }, ...r]);
      }
    } catch(err) {
      console.error("Failed to add source:", err);
    }
  };

  const handleGit = () => {
    if (!gitUrl.trim()) return;
    const name = gitUrl.replace(/\/$/, "").split("/").slice(-2).join("/") || gitUrl;
    addRow({ name, type: "git", icon: ICONS.Database, iconTone: "text-secondary", status: { kind: "queued" }, lastSync: "Just now" }, gitUrl);
    setGitUrl("");
  };

  const handleDocs = () => {
    if (!docUrl.trim()) return;
    addRow({ name: docUrl.replace(/^https?:\/\//, ""), type: "doc", icon: ICONS.FileText, iconTone: "text-primary", status: { kind: "indexing", progress: 5 }, lastSync: "Just now" }, docUrl);
    setDocUrl("");
  };

  const handleFiles = async (files: FileList | null) => {
    if (!files || !files.length) return;
    for (const f of Array.from(files)) {
      const formData = new FormData();
      formData.append("file", f);
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/sources/upload", {
          method: "POST",
          body: formData
        });
        const data = await res.json();
        if (data.id) {
          setRows((r) => [{ name: f.name, id: data.id, type: "local", icon: ICONS.FolderArchive, iconTone: "text-tertiary", status: { kind: "indexing", progress: 12 }, lastSync: "Just now" }, ...r]);
        }
      } catch(err) {
        console.error("Failed to upload file:", err);
      }
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Sidebar />
      <TopBar />
      <main className="ml-64 pt-24 px-8 pb-12 min-h-screen relative">
        <div className="mb-10">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Connect Your Ecosystem</h2>
          <p className="text-muted-foreground max-w-2xl">
            CodeLens builds a deterministic model by ingesting your code and docs. Start by adding your primary source of truth.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          <ConnectionCard
            icon={Terminal}
            iconTone="text-secondary"
            title="Git Source"
            description="Connect GitHub, GitLab, or Bitbucket repositories via OAuth or HTTPS."
            headerAccessory={
              <div className="flex gap-2 text-muted-foreground">
                <Cloud className="w-4 h-4" />
                <Shield className="w-4 h-4" />
              </div>
            }
          >
            <input
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              placeholder="https://github.com/org/repo"
              className="w-full bg-zinc-950 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-primary focus:ring-1 focus:ring-primary/50 outline-none transition-all"
            />
            <button
              onClick={handleGit}
              className="w-full py-2.5 bg-primary text-primary-foreground font-bold rounded-lg hover:brightness-110 active:scale-[0.98] transition-all shadow-[0_0_15px_rgba(120,120,255,0.25)]"
            >
              Connect
            </button>
          </ConnectionCard>

          <ConnectionCard icon={FolderArchive} iconTone="text-tertiary" title="Local Source">
            <input
              ref={fileRef}
              type="file"
              accept=".zip,.gz,.tar"
              multiple
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <div
              onClick={() => fileRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                handleFiles(e.dataTransfer.files);
              }}
              className={`flex-grow border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 cursor-pointer transition-colors group ${
                dragOver ? "border-tertiary bg-white/5" : "border-white/10 hover:bg-white/5"
              }`}
            >
              <UploadCloud className="w-10 h-10 text-muted-foreground group-hover:text-tertiary group-hover:-translate-y-1 transition-all mb-3" />
              <p className="font-semibold mb-1">Upload Repository AST</p>
              <p className="text-sm text-muted-foreground text-center">
                Drag and drop ZIP or folder containing source trees.
              </p>
            </div>
            <p className="text-[11px] text-muted-foreground text-center uppercase tracking-wider">
              Max Size: 2.4 GB · Supports: .zip, .tar.gz
            </p>
          </ConnectionCard>

          <ConnectionCard
            icon={BookOpen}
            iconTone="text-primary"
            title="Documentation"
            description="Index Confluence, Notion, or any public technical documentation URL."
          >
            <div className="relative">
              <select
                value={docSource}
                onChange={(e) => setDocSource(e.target.value)}
                className="w-full bg-zinc-950 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-primary outline-none appearance-none"
              >
                {DOC_SOURCES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground" />
            </div>
            <input
              value={docUrl}
              onChange={(e) => setDocUrl(e.target.value)}
              placeholder="https://docs.acme.com"
              className="w-full bg-zinc-950 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-primary focus:ring-1 focus:ring-primary/50 outline-none transition-all"
            />
            <button
              onClick={handleDocs}
              className="w-full py-2.5 bg-zinc-950 border border-white/15 text-foreground font-bold rounded-lg hover:bg-white/5 active:scale-[0.98] transition-all"
            >
              Index Docs
            </button>
          </ConnectionCard>
        </div>

        <SourcesTable rows={rows} onRefresh={() => setRows((r) => [...r])} />

        <div className="fixed inset-0 pointer-events-none -z-10">
          <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[50%] bg-primary/10 blur-[120px] rounded-full" />
          <div className="absolute bottom-[-5%] left-[-5%] w-[30%] h-[40%] bg-secondary/5 blur-[100px] rounded-full" />
        </div>
      </main>
    </div>
  );
}

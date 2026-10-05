## Ingest Page

Create `/ingest` route matching the existing dark glass-card design system.

### Files
- **`src/routes/ingest.tsx`** — page with header ("Connect Your Ecosystem"), 3-card connection grid, and Connected Entities table.
- **`src/components/ingest/ConnectionCard.tsx`** — reusable glass-card wrapper for the 3 source types.
- **`src/components/ingest/SourcesTable.tsx`** — table with status pills (Synced/Indexing with progress bar/Failed), type badges, last sync, row actions.
- **`src/components/landing/Sidebar.tsx`** — add "Ingest" link → `/ingest` (lucide `Download` or `Plug` icon).

### Sections
1. **Header** — "Connect Your Ecosystem" + subcopy.
2. **Connection grid** (3 cards):
   - **Git Source** — URL input + Connect primary button (GitHub/GitLab/Bitbucket).
   - **Local Source** — dashed drop zone, file input for .zip/.tar.gz, size hint.
   - **Documentation** — source-type select (Confluence/Notion/Swagger/Docusaurus) + URL + Index button.
3. **Connected Entities table** — title, "4 Active" badge, filter/refresh actions; rows for auth-service (Synced, pulse dot), api-docs-v2 (Indexing 45% with progress bar), legacy-gateway (Failed).

### Behavior (UI-only, mocked)
- Inputs controlled with `useState`; Connect/Index buttons append a new "Queued" row to local state.
- Drop zone supports click + drag-over highlight; file selection adds a "Local Upload" row.
- Filter/refresh are visual (toast or no-op for now).

Icons via `lucide-react` to stay consistent with the rest of the app (Terminal, FolderArchive, BookOpen, Database, FileText, CloudOff, MoreHorizontal, Filter, RefreshCw). Background atmosphere blobs reused via existing styles.

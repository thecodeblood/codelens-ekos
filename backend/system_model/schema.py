"""SQLite schema definition for the System Model.

All DDL is expressed as idempotent ``CREATE TABLE IF NOT EXISTS`` / ``CREATE
INDEX IF NOT EXISTS`` statements so that ``create_schema`` can be called
safely on an already-initialised database.
"""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Core tables
# ---------------------------------------------------------------------------

_NODES_TABLE = """
CREATE TABLE IF NOT EXISTS nodes (
    id              TEXT PRIMARY KEY,
    node_type       TEXT NOT NULL,
    name            TEXT NOT NULL,
    qualified_name  TEXT,
    description     TEXT,
    properties_json TEXT NOT NULL DEFAULT '{}',
    tags_json       TEXT NOT NULL DEFAULT '[]',
    confidence      REAL NOT NULL DEFAULT 1.0,
    extraction_method TEXT NOT NULL DEFAULT 'manual',
    first_seen_run  TEXT,
    last_updated_run TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
"""

_EDGES_TABLE = """
CREATE TABLE IF NOT EXISTS edges (
    id              TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL,
    target_id       TEXT NOT NULL,
    edge_type       TEXT NOT NULL,
    properties_json TEXT NOT NULL DEFAULT '{}',
    confidence      REAL NOT NULL DEFAULT 1.0,
    extraction_method TEXT NOT NULL DEFAULT 'manual',
    first_seen_run  TEXT,
    last_updated_run TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE
);
"""

# ---------------------------------------------------------------------------
# FTS5 virtual tables
# ---------------------------------------------------------------------------

_NODES_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name,
    qualified_name,
    description,
    content='nodes',
    content_rowid='rowid'
);
"""

_NODES_FTS_TRIGGERS = """
-- Keep FTS index in sync with the nodes table.
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, qualified_name, description)
    VALUES (new.rowid, new.name, new.qualified_name, new.description);
END;

CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, qualified_name, description)
    VALUES ('delete', old.rowid, old.name, old.qualified_name, old.description);
END;

CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, qualified_name, description)
    VALUES ('delete', old.rowid, old.name, old.qualified_name, old.description);
    INSERT INTO nodes_fts(rowid, name, qualified_name, description)
    VALUES (new.rowid, new.name, new.qualified_name, new.description);
END;
"""

# ---------------------------------------------------------------------------
# Canonical Entity Registry
# ---------------------------------------------------------------------------

_CANONICAL_ENTITIES = """
CREATE TABLE IF NOT EXISTS canonical_entities (
    canonical_id    TEXT PRIMARY KEY,
    primary_name    TEXT NOT NULL,
    node_type       TEXT NOT NULL,
    created_in_run  TEXT
);
"""

_ENTITY_ALIASES = """
CREATE TABLE IF NOT EXISTS entity_aliases (
    alias           TEXT NOT NULL,
    canonical_id    TEXT NOT NULL,
    alias_type      TEXT NOT NULL DEFAULT 'alias',
    confidence      REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (alias, canonical_id),
    FOREIGN KEY (canonical_id) REFERENCES canonical_entities(canonical_id) ON DELETE CASCADE
);
"""

_ALIASES_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS aliases_fts USING fts5(
    alias,
    content='entity_aliases',
    content_rowid='rowid'
);
"""

_ALIASES_FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS aliases_ai AFTER INSERT ON entity_aliases BEGIN
    INSERT INTO aliases_fts(rowid, alias) VALUES (new.rowid, new.alias);
END;

CREATE TRIGGER IF NOT EXISTS aliases_ad AFTER DELETE ON entity_aliases BEGIN
    INSERT INTO aliases_fts(aliases_fts, rowid, alias) VALUES ('delete', old.rowid, old.alias);
END;

CREATE TRIGGER IF NOT EXISTS aliases_au AFTER UPDATE ON entity_aliases BEGIN
    INSERT INTO aliases_fts(aliases_fts, rowid, alias) VALUES ('delete', old.rowid, old.alias);
    INSERT INTO aliases_fts(rowid, alias) VALUES (new.rowid, new.alias);
END;
"""

# ---------------------------------------------------------------------------
# Evidence & Conflicts
# ---------------------------------------------------------------------------

_EVIDENCE_TABLE = """
CREATE TABLE IF NOT EXISTS evidence (
    id              TEXT PRIMARY KEY,
    entity_id       TEXT NOT NULL,
    entity_type     TEXT NOT NULL DEFAULT 'node',
    source_type     TEXT NOT NULL,
    source_uri      TEXT NOT NULL,
    source_location TEXT,
    extraction_method TEXT NOT NULL,
    confidence      REAL NOT NULL DEFAULT 1.0,
    extracted_in_run TEXT,
    raw_excerpt     TEXT
);
"""

_CONFLICTS_TABLE = """
CREATE TABLE IF NOT EXISTS conflicts (
    id                  TEXT PRIMARY KEY,
    entity_id           TEXT NOT NULL,
    conflict_type       TEXT NOT NULL,
    existing_evidence_id TEXT,
    new_evidence_id     TEXT,
    status              TEXT NOT NULL DEFAULT 'open',
    resolution          TEXT,
    detected_in_run     TEXT,
    description         TEXT,
    FOREIGN KEY (existing_evidence_id) REFERENCES evidence(id),
    FOREIGN KEY (new_evidence_id) REFERENCES evidence(id)
);
"""

# ---------------------------------------------------------------------------
# Model Snapshots & Ingestion Tracking
# ---------------------------------------------------------------------------

_MODEL_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS model_snapshots (
    id          TEXT PRIMARY KEY,
    run_id      TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    node_count  INTEGER NOT NULL DEFAULT 0,
    edge_count  INTEGER NOT NULL DEFAULT 0,
    delta_json  TEXT NOT NULL DEFAULT '{}'
);
"""

_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    uri TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'registered',
    last_ingested TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

_INGESTION_RUNS = """
CREATE TABLE IF NOT EXISTS ingestion_runs (
    id                      TEXT PRIMARY KEY,
    source_id               TEXT,
    status                  TEXT NOT NULL DEFAULT 'pending',
    started_at              TEXT,
    completed_at            TEXT,
    files_total             INTEGER NOT NULL DEFAULT 0,
    files_processed         INTEGER NOT NULL DEFAULT 0,
    files_failed            INTEGER NOT NULL DEFAULT 0,
    entities_extracted      INTEGER NOT NULL DEFAULT 0,
    relationships_extracted INTEGER NOT NULL DEFAULT 0,
    conflicts_detected      INTEGER NOT NULL DEFAULT 0,
    error_log               TEXT
);
"""

_INGESTION_FILE_STATUS = """
CREATE TABLE IF NOT EXISTS ingestion_file_status (
    run_id      TEXT NOT NULL,
    file_path   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    error       TEXT,
    PRIMARY KEY (run_id, file_path),
    FOREIGN KEY (run_id) REFERENCES ingestion_runs(id) ON DELETE CASCADE
);
"""

# ---------------------------------------------------------------------------
# Corrections (user / automated fixes)
# ---------------------------------------------------------------------------

_CORRECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS corrections (
    id              TEXT PRIMARY KEY,
    entity_id       TEXT NOT NULL,
    correction_type TEXT NOT NULL,
    original_value  TEXT,
    corrected_value TEXT,
    timestamp       TEXT NOT NULL,
    note            TEXT
);
"""

# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------

_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_nodes_qualified_name ON nodes(qualified_name);
CREATE INDEX IF NOT EXISTS idx_nodes_first_seen_run ON nodes(first_seen_run);
CREATE INDEX IF NOT EXISTS idx_nodes_last_updated_run ON nodes(last_updated_run);

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_source_type ON edges(source_id, edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_target_type ON edges(target_id, edge_type);

CREATE INDEX IF NOT EXISTS idx_canonical_name ON canonical_entities(primary_name);
CREATE INDEX IF NOT EXISTS idx_canonical_type ON canonical_entities(node_type);
CREATE INDEX IF NOT EXISTS idx_aliases_canonical ON entity_aliases(canonical_id);

CREATE INDEX IF NOT EXISTS idx_evidence_entity ON evidence(entity_id);
CREATE INDEX IF NOT EXISTS idx_evidence_run ON evidence(extracted_in_run);

CREATE INDEX IF NOT EXISTS idx_conflicts_entity ON conflicts(entity_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(status);

CREATE INDEX IF NOT EXISTS idx_snapshots_run ON model_snapshots(run_id);

CREATE INDEX IF NOT EXISTS idx_ingestion_status ON ingestion_runs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_file_run ON ingestion_file_status(run_id);

CREATE INDEX IF NOT EXISTS idx_corrections_entity ON corrections(entity_id);
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all System Model tables, FTS indexes, triggers, and indexes.

    This function is idempotent — safe to call on an already-initialised
    database.  All DDL uses ``IF NOT EXISTS`` guards.

    Args:
        conn: An open SQLite connection.
    """
    logger.info("Creating / verifying System Model schema …")

    # Enable foreign key enforcement.
    conn.execute("PRAGMA foreign_keys = ON;")

    statements: list[str] = [
        _NODES_TABLE,
        _EDGES_TABLE,
        _NODES_FTS,
        _CANONICAL_ENTITIES,
        _ENTITY_ALIASES,
        _ALIASES_FTS,
        _EVIDENCE_TABLE,
        _CONFLICTS_TABLE,
        _MODEL_SNAPSHOTS,
        _SOURCES_TABLE,
        _INGESTION_RUNS,
        _INGESTION_FILE_STATUS,
        _CORRECTIONS_TABLE,
    ]

    for ddl in statements:
        conn.executescript(ddl)

    # Triggers and indexes are multi-statement blocks; use executescript.
    conn.executescript(_NODES_FTS_TRIGGERS)
    conn.executescript(_ALIASES_FTS_TRIGGERS)
    conn.executescript(_INDEXES)

    conn.commit()
    logger.info("System Model schema is ready.")

"""SystemModel — central interface for the multi-graph knowledge store.

Provides CRUD operations, full-text search, and on-demand NetworkX graph
algorithm execution.  SQLite is the sole persistence layer; NetworkX graphs
are materialised transiently for algorithmic queries.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Optional

import networkx as nx
from pydantic import BaseModel, Field

from backend.system_model.edges import EdgeType, SystemEdge
from backend.system_model.nodes import (
    ExtractionMethod,
    NodeType,
    SystemNode,
    NODE_PROPERTIES_REGISTRY,
)
from backend.system_model.schema import create_schema

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper Pydantic models
# ---------------------------------------------------------------------------


class ModelStats(BaseModel):
    """Aggregate statistics for the current model state."""

    total_nodes: int = 0
    total_edges: int = 0
    nodes_by_type: dict[str, int] = Field(default_factory=dict)
    edges_by_type: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.utcnow().isoformat()


def _row_to_node(row: sqlite3.Row) -> SystemNode:
    """Deserialise a database row into a ``SystemNode``."""
    node_type = NodeType(row["node_type"])
    raw_props = json.loads(row["properties_json"])

    # Hydrate into the typed properties model when available.
    props_cls = NODE_PROPERTIES_REGISTRY.get(node_type)
    if props_cls is not None:
        properties: Any = props_cls(**raw_props)
    else:
        properties = raw_props

    return SystemNode(
        id=row["id"],
        node_type=node_type,
        name=row["name"],
        qualified_name=row["qualified_name"],
        description=row["description"],
        properties=properties,
        tags=json.loads(row["tags_json"]),
        confidence=row["confidence"],
        extraction_method=ExtractionMethod(row["extraction_method"]),
        first_seen_run=row["first_seen_run"],
        last_updated_run=row["last_updated_run"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _row_to_edge(row: sqlite3.Row) -> SystemEdge:
    """Deserialise a database row into a ``SystemEdge``."""
    return SystemEdge(
        id=row["id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        edge_type=EdgeType(row["edge_type"]),
        properties=json.loads(row["properties_json"]),
        confidence=row["confidence"],
        extraction_method=ExtractionMethod(row["extraction_method"]),
        first_seen_run=row["first_seen_run"],
        last_updated_run=row["last_updated_run"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


# ---------------------------------------------------------------------------
# SystemModel
# ---------------------------------------------------------------------------


class SystemModel:
    """Central read/write interface to the System Model knowledge graph.

    The model stores everything in SQLite (WAL journal mode) and materialises
    NetworkX graphs on demand for algorithmic queries such as shortest-path
    and cycle detection.

    Usage::

        model = SystemModel("my_project.db")
        model.add_node(node)
        model.add_edge(edge)
        stats = model.get_stats()
        model.close()
    """

    # ------------------------------------------------------------------ init

    def __init__(self, db_path: str) -> None:
        """Open (or create) the SQLite database and ensure the schema exists.

        Args:
            db_path: Filesystem path to the SQLite database file.  Use
                ``\":memory:\"`` for an ephemeral in-memory database.
        """
        logger.info("Opening SystemModel at %s", db_path)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        create_schema(self._conn)

    @property
    def conn(self) -> sqlite3.Connection:
        """Expose the underlying connection for subsystems that share it."""
        return self._conn

    # -------------------------------------------------------------- Node CRUD

    def add_node(self, node: SystemNode) -> None:
        """Insert a new node into the model.

        If a node with the same ``id`` already exists the call will raise
        ``sqlite3.IntegrityError``.

        Args:
            node: The fully-populated node to store.
        """
        now = _now_iso()
        props_json = json.dumps(node.properties_dict())
        tags_json = json.dumps(node.tags)
        self._conn.execute(
            """
            INSERT INTO nodes
                (id, node_type, name, qualified_name, description,
                 properties_json, tags_json, confidence, extraction_method,
                 first_seen_run, last_updated_run, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node.id,
                node.node_type.value,
                node.name,
                node.qualified_name,
                node.description,
                props_json,
                tags_json,
                node.confidence,
                node.extraction_method.value,
                node.first_seen_run,
                node.last_updated_run,
                now,
                now,
            ),
        )
        self._conn.commit()
        logger.debug("Added node %s (%s)", node.id, node.node_type.value)

    def get_node(self, node_id: str) -> Optional[SystemNode]:
        """Retrieve a node by its unique ID.

        Returns:
            The hydrated ``SystemNode``, or ``None`` if not found.
        """
        cur = self._conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return _row_to_node(row)

    def update_node(self, node: SystemNode) -> bool:
        """Update an existing node in-place.

        All mutable fields are overwritten.  ``created_at`` is preserved.

        Returns:
            ``True`` if a row was updated, ``False`` if the node was not found.
        """
        now = _now_iso()
        props_json = json.dumps(node.properties_dict())
        tags_json = json.dumps(node.tags)
        cur = self._conn.execute(
            """
            UPDATE nodes SET
                node_type = ?,
                name = ?,
                qualified_name = ?,
                description = ?,
                properties_json = ?,
                tags_json = ?,
                confidence = ?,
                extraction_method = ?,
                first_seen_run = ?,
                last_updated_run = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                node.node_type.value,
                node.name,
                node.qualified_name,
                node.description,
                props_json,
                tags_json,
                node.confidence,
                node.extraction_method.value,
                node.first_seen_run,
                node.last_updated_run,
                now,
                node.id,
            ),
        )
        self._conn.commit()
        updated = cur.rowcount > 0
        if updated:
            logger.debug("Updated node %s", node.id)
        return updated

    def remove_node(self, node_id: str) -> bool:
        """Delete a node and its connected edges (via FK cascade).

        Returns:
            ``True`` if a row was deleted.
        """
        # Manually delete edges first to be safe even when FK cascade is off.
        self._conn.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
            (node_id, node_id),
        )
        cur = self._conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        self._conn.commit()
        deleted = cur.rowcount > 0
        if deleted:
            logger.debug("Removed node %s (and connected edges)", node_id)
        return deleted

    # -------------------------------------------------------------- Edge CRUD

    def add_edge(self, edge: SystemEdge) -> None:
        """Insert a new edge into the model.

        Args:
            edge: The fully-populated edge to store.

        Raises:
            sqlite3.IntegrityError: If the edge ID is duplicated or
                source/target nodes do not exist.
        """
        now = _now_iso()
        props_json = json.dumps(edge.properties)
        self._conn.execute(
            """
            INSERT INTO edges
                (id, source_id, target_id, edge_type, properties_json,
                 confidence, extraction_method, first_seen_run,
                 last_updated_run, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edge.id,
                edge.source_id,
                edge.target_id,
                edge.edge_type.value,
                props_json,
                edge.confidence,
                edge.extraction_method.value,
                edge.first_seen_run,
                edge.last_updated_run,
                now,
                now,
            ),
        )
        self._conn.commit()
        logger.debug("Added edge %s (%s)", edge.id, edge.edge_type.value)

    def get_edge(self, edge_id: str) -> Optional[SystemEdge]:
        """Retrieve an edge by its unique ID.

        Returns:
            The hydrated ``SystemEdge``, or ``None`` if not found.
        """
        cur = self._conn.execute("SELECT * FROM edges WHERE id = ?", (edge_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return _row_to_edge(row)

    def update_edge(self, edge: SystemEdge) -> bool:
        now = _now_iso()
        props_json = json.dumps(edge.properties)
        cur = self._conn.execute(
            """
            UPDATE edges SET
                source_id = ?,
                target_id = ?,
                edge_type = ?,
                properties_json = ?,
                confidence = ?,
                extraction_method = ?,
                first_seen_run = ?,
                last_updated_run = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                edge.source_id,
                edge.target_id,
                edge.edge_type.value,
                props_json,
                edge.confidence,
                edge.extraction_method.value,
                edge.first_seen_run,
                edge.last_updated_run,
                now,
                edge.id,
            ),
        )
        self._conn.commit()
        updated = cur.rowcount > 0
        if updated:
            logger.debug("Updated edge %s", edge.id)
        return updated

    def remove_edge(self, edge_id: str) -> bool:
        """Delete an edge by ID.

        Returns:
            ``True`` if a row was deleted.
        """
        cur = self._conn.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        self._conn.commit()
        deleted = cur.rowcount > 0
        if deleted:
            logger.debug("Removed edge %s", edge_id)
        return deleted

    # ------------------------------------------------------------ Queries

    def get_all_nodes(self) -> list[SystemNode]:
        cur = self._conn.execute("SELECT * FROM nodes")
        return [_row_to_node(row) for row in cur.fetchall()]

    def get_all_edges(self) -> list[SystemEdge]:
        cur = self._conn.execute("SELECT * FROM edges")
        return [_row_to_edge(row) for row in cur.fetchall()]

    def get_edges_for_node(self, node_id: str) -> list[SystemEdge]:
        cur = self._conn.execute(
            "SELECT * FROM edges WHERE source_id = ? OR target_id = ?",
            (node_id, node_id)
        )
        return [_row_to_edge(row) for row in cur.fetchall()]

    def get_nodes_by_type(self, node_type: NodeType) -> list[SystemNode]:
        """Return all nodes of a given type.

        Args:
            node_type: The ``NodeType`` to filter on.
        """
        cur = self._conn.execute(
            "SELECT * FROM nodes WHERE node_type = ?", (node_type.value,)
        )
        return [_row_to_node(row) for row in cur.fetchall()]

    def get_edges_by_type(self, edge_type: EdgeType) -> list[SystemEdge]:
        """Return all edges of a given type.

        Args:
            edge_type: The ``EdgeType`` to filter on.
        """
        cur = self._conn.execute(
            "SELECT * FROM edges WHERE edge_type = ?", (edge_type.value,)
        )
        return [_row_to_edge(row) for row in cur.fetchall()]

    def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        edge_type: Optional[EdgeType] = None,
    ) -> list[SystemEdge]:
        """Flexible edge query with optional source, target, and type filters.

        At least one filter should be supplied; calling with no arguments
        will return *all* edges (potentially expensive).
        """
        clauses: list[str] = []
        params: list[Any] = []

        if source_id is not None:
            clauses.append("source_id = ?")
            params.append(source_id)
        if target_id is not None:
            clauses.append("target_id = ?")
            params.append(target_id)
        if edge_type is not None:
            clauses.append("edge_type = ?")
            params.append(edge_type.value)

        where = " AND ".join(clauses) if clauses else "1=1"
        cur = self._conn.execute(f"SELECT * FROM edges WHERE {where}", params)
        return [_row_to_edge(row) for row in cur.fetchall()]

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        edge_type: Optional[EdgeType] = None,
    ) -> list[SystemNode]:
        """Return neighbouring nodes reachable from *node_id*.

        Args:
            node_id: The starting node.
            direction: ``\"out\"`` (outgoing), ``\"in\"`` (incoming), or
                ``\"both\"``.
            edge_type: Optionally restrict to a single edge type.

        Returns:
            Deduplicated list of neighbouring ``SystemNode`` instances.
        """
        neighbor_ids: set[str] = set()

        if direction in ("out", "both"):
            edges_out = self.get_edges(source_id=node_id, edge_type=edge_type)
            neighbor_ids.update(e.target_id for e in edges_out)
        if direction in ("in", "both"):
            edges_in = self.get_edges(target_id=node_id, edge_type=edge_type)
            neighbor_ids.update(e.source_id for e in edges_in)

        neighbors: list[SystemNode] = []
        for nid in neighbor_ids:
            node = self.get_node(nid)
            if node is not None:
                neighbors.append(node)
        return neighbors

    def search_nodes(
        self,
        query: str,
        node_type: Optional[NodeType] = None,
        limit: int = 20,
    ) -> list[SystemNode]:
        """Full-text search across node names, qualified names, and descriptions.

        Uses SQLite FTS5 with ``MATCH`` for efficient fuzzy search.

        Args:
            query: The search terms (FTS5 syntax is supported).
            node_type: Optionally restrict results to a single node type.
            limit: Maximum results to return.

        Returns:
            Matching nodes ordered by FTS5 rank (best match first).
        """
        # FTS5 match query — append '*' for prefix matching if not already
        # using FTS5 operators.
        safe_query = query.replace('"', '""')
        fts_query = query if any(c in query for c in ('"', "*", "OR", "AND", "NOT")) else f'"{safe_query}"*'

        if node_type is not None:
            sql = """
                SELECT n.* FROM nodes n
                JOIN nodes_fts fts ON n.rowid = fts.rowid
                WHERE nodes_fts MATCH ? AND n.node_type = ?
                ORDER BY fts.rank
                LIMIT ?
            """
            cur = self._conn.execute(sql, (fts_query, node_type.value, limit))
        else:
            sql = """
                SELECT n.* FROM nodes n
                JOIN nodes_fts fts ON n.rowid = fts.rowid
                WHERE nodes_fts MATCH ?
                ORDER BY fts.rank
                LIMIT ?
            """
            cur = self._conn.execute(sql, (fts_query, limit))

        return [_row_to_node(row) for row in cur.fetchall()]

    # --------------------------------------------------- Graph Algorithms

    def _build_networkx_graph(
        self,
        edge_types: Optional[list[EdgeType]] = None,
        node_types: Optional[list[NodeType]] = None,
    ) -> nx.DiGraph:
        """Materialise the current model (or a filtered subset) as a NetworkX DiGraph.

        This is intentionally *not* cached — the graph is rebuilt each time
        to guarantee freshness.

        Args:
            edge_types: If supplied, only include these edge types.
            node_types: If supplied, only include nodes of these types.

        Returns:
            A directed graph with string node IDs and edge metadata.
        """
        g = nx.DiGraph()

        # --- Nodes ---
        if node_types:
            placeholders = ",".join("?" for _ in node_types)
            sql = f"SELECT * FROM nodes WHERE node_type IN ({placeholders})"
            cur = self._conn.execute(sql, [nt.value for nt in node_types])
        else:
            cur = self._conn.execute("SELECT * FROM nodes")

        node_ids: set[str] = set()
        for row in cur.fetchall():
            node_ids.add(row["id"])
            g.add_node(
                row["id"],
                node_type=row["node_type"],
                name=row["name"],
                qualified_name=row["qualified_name"],
            )

        # --- Edges ---
        if edge_types:
            placeholders = ",".join("?" for _ in edge_types)
            sql = f"SELECT * FROM edges WHERE edge_type IN ({placeholders})"
            cur = self._conn.execute(sql, [et.value for et in edge_types])
        else:
            cur = self._conn.execute("SELECT * FROM edges")

        for row in cur.fetchall():
            src, tgt = row["source_id"], row["target_id"]
            # Only add edges whose endpoints exist in our (possibly filtered) node set.
            if node_types and (src not in node_ids or tgt not in node_ids):
                continue
            g.add_edge(
                src,
                tgt,
                edge_type=row["edge_type"],
                edge_id=row["id"],
                confidence=row["confidence"],
            )

        logger.debug(
            "Built NetworkX graph: %d nodes, %d edges",
            g.number_of_nodes(),
            g.number_of_edges(),
        )
        return g

    def get_call_chain(
        self,
        start_node_id: str,
        max_depth: int = 10,
    ) -> list[list[str]]:
        """Compute all call chains originating from *start_node_id*.

        Follows ``CALLS`` edges up to *max_depth* hops using DFS.

        Returns:
            A list of paths, each path being a list of node IDs.
        """
        g = self._build_networkx_graph(edge_types=[EdgeType.CALLS])

        if start_node_id not in g:
            return []

        paths: list[list[str]] = []
        visited: set[str] = set()

        def _dfs(current: str, path: list[str], depth: int) -> None:
            if depth > max_depth:
                return
            visited.add(current)
            successors = list(g.successors(current))
            if not successors:
                paths.append(list(path))
            else:
                for succ in successors:
                    if succ not in visited:
                        path.append(succ)
                        _dfs(succ, path, depth + 1)
                        path.pop()
                if not any(s not in visited for s in successors):
                    paths.append(list(path))
            visited.discard(current)

        _dfs(start_node_id, [start_node_id], 0)
        return paths

    def get_shortest_path(
        self,
        source_id: str,
        target_id: str,
        edge_types: Optional[list[EdgeType]] = None,
    ) -> Optional[list[str]]:
        """Find the shortest directed path between two nodes.

        Args:
            source_id: Starting node ID.
            target_id: Destination node ID.
            edge_types: Optionally restrict traversal to these edge types.

        Returns:
            Ordered list of node IDs forming the shortest path, or ``None``
            if no path exists.
        """
        g = self._build_networkx_graph(edge_types=edge_types)
        try:
            return nx.shortest_path(g, source_id, target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def detect_cycles(
        self,
        edge_types: Optional[list[EdgeType]] = None,
    ) -> list[list[str]]:
        """Detect all simple cycles in the graph.

        Args:
            edge_types: Optionally restrict to these edge types.

        Returns:
            A list of cycles, each cycle being a list of node IDs.
        """
        g = self._build_networkx_graph(edge_types=edge_types)
        return list(nx.simple_cycles(g))

    def get_connected_subgraph(
        self,
        node_id: str,
        max_depth: int = 3,
        edge_types: Optional[list[EdgeType]] = None,
    ) -> tuple[list[SystemNode], list[SystemEdge]]:
        """Extract a subgraph rooted at *node_id* within *max_depth* hops.

        Uses undirected BFS from the starting node.

        Returns:
            Tuple of (nodes, edges) within the subgraph.
        """
        g = self._build_networkx_graph(edge_types=edge_types)

        if node_id not in g:
            return [], []

        # BFS on undirected view to capture both incoming and outgoing.
        undirected = g.to_undirected()
        reachable: set[str] = set()
        frontier = {node_id}
        for _ in range(max_depth + 1):
            reachable.update(frontier)
            next_frontier: set[str] = set()
            for n in frontier:
                next_frontier.update(undirected.neighbors(n))
            next_frontier -= reachable
            frontier = next_frontier
            if not frontier:
                break

        # Hydrate from the database.
        nodes: list[SystemNode] = []
        for nid in reachable:
            node = self.get_node(nid)
            if node is not None:
                nodes.append(node)

        edge_set: set[str] = set()
        edges: list[SystemEdge] = []
        for u, v, data in g.edges(data=True):
            if u in reachable and v in reachable:
                eid = data.get("edge_id", "")
                if eid and eid not in edge_set:
                    edge_set.add(eid)
                    edge = self.get_edge(eid)
                    if edge is not None:
                        edges.append(edge)

        return nodes, edges

    # ------------------------------------------------------------ Stats

    def get_stats(self) -> ModelStats:
        """Return aggregate statistics about the current model state.

        Returns:
            A ``ModelStats`` object with total counts and per-type breakdowns.
        """
        cur = self._conn.execute("SELECT COUNT(*) FROM nodes")
        total_nodes: int = cur.fetchone()[0]

        cur = self._conn.execute("SELECT COUNT(*) FROM edges")
        total_edges: int = cur.fetchone()[0]

        cur = self._conn.execute(
            "SELECT node_type, COUNT(*) as cnt FROM nodes GROUP BY node_type"
        )
        nodes_by_type = {row["node_type"]: row["cnt"] for row in cur.fetchall()}

        cur = self._conn.execute(
            "SELECT edge_type, COUNT(*) as cnt FROM edges GROUP BY edge_type"
        )
        edges_by_type = {row["edge_type"]: row["cnt"] for row in cur.fetchall()}

        return ModelStats(
            total_nodes=total_nodes,
            total_edges=total_edges,
            nodes_by_type=nodes_by_type,
            edges_by_type=edges_by_type,
        )

    # ---------------------------------------------------------- Lifecycle

    def close(self) -> None:
        """Close the underlying SQLite connection.

        The model should not be used after calling this method.
        """
        logger.info("Closing SystemModel at %s", self.db_path)
        self._conn.close()

    def __enter__(self) -> SystemModel:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

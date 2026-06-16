import sqlite3

class CanonicalEntityRegistry:
    """
    Persistent registry mapping surface forms to canonical entity IDs.
    Lives in the System Model Layer.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def register(self, canonical_id: str, name: str, node_type: str,
                 aliases: list[str] = None, run_id: str = "init") -> None:
        """Register a new canonical entity with its primary name and aliases."""
        cursor = self._conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO canonical_entities (canonical_id, primary_name, node_type, created_in_run)
            VALUES (?, ?, ?, ?)
        ''', (canonical_id, name, node_type, run_id))
        
        if aliases:
            for alias in aliases:
                self.add_alias(canonical_id, alias, alias_type='auto')
        self._conn.commit()

    def resolve(self, surface_form: str, node_type: str = None) -> str | None:
        """
        Given a surface form (e.g., 'auth-service'), find its canonical entity id.
        Resolution order:
        1. Exact match on canonical name
        2. Exact match on alias
        3. Normalized match (lowercase, strip hyphens/underscores)
        4. FTS5 fuzzy match (above threshold)
        """
        cursor = self._conn.cursor()
        
        # 1. Exact match on canonical name
        query1 = "SELECT canonical_id FROM canonical_entities WHERE primary_name = ?"
        params1 = [surface_form]
        if node_type:
            query1 += " AND node_type = ?"
            params1.append(node_type)
        res = cursor.execute(query1, params1).fetchone()
        if res:
            return res[0]
            
        # 2. Exact match on alias
        query2 = """
            SELECT e.canonical_id FROM entity_aliases a
            JOIN canonical_entities e ON a.canonical_id = e.canonical_id
            WHERE a.alias = ?
        """
        params2 = [surface_form]
        if node_type:
            query2 += " AND e.node_type = ?"
            params2.append(node_type)
        res = cursor.execute(query2, params2).fetchone()
        if res:
            return res[0]
            
        # 3. Normalized match
        norm_form = self._normalize(surface_form)
        # Note: In SQLite, lowercasing logic might be needed if not fully handled by _normalize.
        query3 = """
            SELECT e.canonical_id FROM entity_aliases a
            JOIN canonical_entities e ON a.canonical_id = e.canonical_id
            WHERE REPLACE(REPLACE(REPLACE(LOWER(a.alias), '-', ''), '_', ''), ' ', '') = ?
        """
        params3 = [norm_form]
        if node_type:
            query3 += " AND e.node_type = ?"
            params3.append(node_type)
        res = cursor.execute(query3, params3).fetchone()
        if res:
            return res[0]
            
        # 4. FTS5 fuzzy match (simplified)
        query4 = """
            SELECT e.canonical_id FROM aliases_fts f
            JOIN entity_aliases e ON f.rowid = e.rowid
            WHERE f.alias MATCH ?
            ORDER BY f.rank LIMIT 1
        """
        # A basic prefix match for FTS5, wrapped in quotes to handle special chars like ':'
        # Escape quotes in the surface form just in case
        safe_form = surface_form.replace('"', '""')
        fts_query = f'"{safe_form}"*'
        res = cursor.execute(query4, (fts_query,)).fetchone()
        if res:
            # Check type if needed
            if node_type:
                type_check = cursor.execute(
                    "SELECT 1 FROM canonical_entities WHERE canonical_id = ? AND node_type = ?", 
                    (res[0], node_type)
                ).fetchone()
                if type_check:
                    return res[0]
            else:
                return res[0]
            
        return None

    def add_alias(self, canonical_id: str, alias: str, alias_type: str = 'auto', confidence: float = 1.0) -> None:
        """Add an alias to an existing canonical entity."""
        cursor = self._conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO entity_aliases (alias, canonical_id, alias_type, confidence)
            VALUES (?, ?, ?, ?)
        ''', (alias, canonical_id, alias_type, confidence))
        self._conn.commit()

    def merge(self, keep_id: str, absorb_id: str) -> None:
        """
        Merge two canonical entities. All references to absorb_id
        are rewritten to keep_id. Aliases are combined.
        """
        cursor = self._conn.cursor()
        # Move aliases
        cursor.execute('''
            UPDATE OR IGNORE entity_aliases
            SET canonical_id = ?
            WHERE canonical_id = ?
        ''', (keep_id, absorb_id))
        
        # Rewrite edges
        cursor.execute('UPDATE edges SET source_id = ? WHERE source_id = ?', (keep_id, absorb_id))
        cursor.execute('UPDATE edges SET target_id = ? WHERE target_id = ?', (keep_id, absorb_id))
        
        # Rewrite evidence
        cursor.execute("UPDATE evidence SET entity_id = ? WHERE entity_id = ? AND entity_type = 'node'", (keep_id, absorb_id))
        
        # Delete absorbed entity
        cursor.execute('DELETE FROM canonical_entities WHERE canonical_id = ?', (absorb_id,))
        cursor.execute('DELETE FROM nodes WHERE id = ?', (absorb_id,))
        self._conn.commit()

    def get_aliases(self, canonical_id: str) -> list[str]:
        """Return all known surface forms for a canonical entity."""
        cursor = self._conn.cursor()
        rows = cursor.execute('SELECT alias FROM entity_aliases WHERE canonical_id = ?', (canonical_id,)).fetchall()
        return [row[0] for row in rows]
        
    def get_all(self) -> list[dict]:
        """List all canonical entities."""
        cursor = self._conn.cursor()
        rows = cursor.execute('SELECT canonical_id, primary_name, node_type FROM canonical_entities').fetchall()
        return [{"canonical_id": r[0], "primary_name": r[1], "node_type": r[2]} for r in rows]

    def _normalize(self, name: str) -> str:
        """Lowercase, strip hyphens/underscores/spaces."""
        return name.lower().replace("-", "").replace("_", "").replace(" ", "")

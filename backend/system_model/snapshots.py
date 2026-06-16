import sqlite3
import datetime
import uuid
import json

class SnapshotManager:
    """Manages model versioning and deltas."""

    @staticmethod
    def create_snapshot(conn: sqlite3.Connection, run_id: str) -> str:
        """Capture current model state counts + delta from last snapshot."""
        cursor = conn.cursor()
        
        # Get counts
        node_count = cursor.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        
        snapshot_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        # Simple delta for MVP: just a placeholder or basic stats.
        # Computing a full delta requires keeping track of previous state or extracting from last_updated_run.
        delta_json = json.dumps({
            "added_nodes_run": run_id
        })
        
        cursor.execute('''
            INSERT INTO model_snapshots (id, run_id, timestamp, node_count, edge_count, delta_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (snapshot_id, run_id, timestamp, node_count, edge_count, delta_json))
        conn.commit()
        
        return snapshot_id

    @staticmethod
    def get_snapshots(conn: sqlite3.Connection) -> list[dict]:
        """List all snapshots."""
        cursor = conn.cursor()
        rows = cursor.execute('SELECT id, run_id, timestamp, node_count, edge_count FROM model_snapshots ORDER BY timestamp DESC').fetchall()
        return [
            {"id": r[0], "run_id": r[1], "timestamp": r[2], "node_count": r[3], "edge_count": r[4]}
            for r in rows
        ]

    @staticmethod
    def get_delta(conn: sqlite3.Connection, snapshot_id: str) -> dict:
        """Get delta details."""
        cursor = conn.cursor()
        row = cursor.execute('SELECT delta_json FROM model_snapshots WHERE id = ?', (snapshot_id,)).fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}

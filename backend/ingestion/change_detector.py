import sqlite3
import hashlib

class ChangeDetector:
    """Detects changes in files based on content hash."""
    
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._ensure_table()

    def _ensure_table(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                source_id TEXT,
                file_path TEXT,
                content_hash TEXT,
                last_processed TEXT,
                PRIMARY KEY (source_id, file_path)
            )
        ''')
        self._conn.commit()

    def compute_hash(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()

    def has_changed(self, source_id: str, file_path: str, current_hash: str) -> bool:
        prev_hash = self.get_previous_hash(source_id, file_path)
        return current_hash != prev_hash

    def get_previous_hash(self, source_id: str, file_path: str) -> str | None:
        cursor = self._conn.cursor()
        row = cursor.execute('''
            SELECT content_hash FROM file_hashes
            WHERE source_id = ? AND file_path = ?
        ''', (source_id, file_path)).fetchone()
        return row[0] if row else None

    def store_hash(self, source_id: str, file_path: str, content_hash: str, timestamp: str) -> None:
        cursor = self._conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO file_hashes (source_id, file_path, content_hash, last_processed)
            VALUES (?, ?, ?, ?)
        ''', (source_id, file_path, content_hash, timestamp))
        self._conn.commit()

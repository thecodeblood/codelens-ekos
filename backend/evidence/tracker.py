import sqlite3
from typing import List, Dict, Optional
from .models import Evidence, Conflict

class EvidenceTracker:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def record(self, evidence: Evidence) -> None:
        """Store evidence record."""
        cursor = self._conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO evidence (
                id, entity_id, entity_type, source_type, source_uri, 
                source_location, extraction_method, confidence, extracted_in_run, raw_excerpt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            evidence.id, evidence.entity_id, evidence.entity_type, evidence.source_type,
            evidence.source_uri, evidence.source_location, evidence.extraction_method,
            evidence.confidence, evidence.extracted_in_run, evidence.raw_excerpt
        ))
        self._conn.commit()

    def get_evidence(self, entity_id: str) -> List[Evidence]:
        """Get all evidence for an entity."""
        cursor = self._conn.cursor()
        rows = cursor.execute('''
            SELECT id, entity_id, entity_type, source_type, source_uri, 
                   source_location, extraction_method, confidence, extracted_in_run, raw_excerpt
            FROM evidence WHERE entity_id = ?
        ''', (entity_id,)).fetchall()
        
        return [
            Evidence(
                id=r[0], entity_id=r[1], entity_type=r[2], source_type=r[3],
                source_uri=r[4], source_location=r[5], extraction_method=r[6],
                confidence=r[7], extracted_in_run=r[8], raw_excerpt=r[9]
            ) for r in rows
        ]

    def get_evidence_summary(self, entity_id: str) -> Dict[str, int]:
        """Count evidence by source type."""
        cursor = self._conn.cursor()
        rows = cursor.execute('''
            SELECT source_type, COUNT(*) FROM evidence WHERE entity_id = ? GROUP BY source_type
        ''', (entity_id,)).fetchall()
        return {r[0]: r[1] for r in rows}

    def record_conflict(self, conflict: Conflict) -> None:
        """Store conflict."""
        cursor = self._conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO conflicts (
                id, entity_id, conflict_type, existing_evidence_id, new_evidence_id, 
                status, resolution, detected_in_run, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            conflict.id, conflict.entity_id, conflict.conflict_type.value,
            conflict.existing_evidence_id, conflict.new_evidence_id,
            conflict.status, conflict.resolution, conflict.detected_in_run, conflict.description
        ))
        self._conn.commit()

    def get_conflicts(self, status: Optional[str] = None) -> List[dict]:
        """List conflicts."""
        cursor = self._conn.cursor()
        query = 'SELECT id, entity_id, conflict_type, status, description FROM conflicts'
        params = []
        if status:
            query += ' WHERE status = ?'
            params.append(status)
        rows = cursor.execute(query, params).fetchall()
        return [
            {"id": r[0], "entity_id": r[1], "conflict_type": r[2], "status": r[3], "description": r[4]}
            for r in rows
        ]

    def resolve_conflict(self, conflict_id: str, resolution: str) -> None:
        """Mark resolved."""
        cursor = self._conn.cursor()
        cursor.execute('''
            UPDATE conflicts SET status = 'resolved', resolution = ? WHERE id = ?
        ''', (resolution, conflict_id))
        self._conn.commit()

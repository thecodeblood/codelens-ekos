"""Evidence tracking package — provenance and conflict management.

Every fact in the System Model must have evidence linking it to source material.
"""

from backend.evidence.models import Evidence, Conflict, ConflictType
from backend.evidence.tracker import EvidenceTracker

__all__ = [
    "Evidence",
    "Conflict",
    "ConflictType",
    "EvidenceTracker",
]

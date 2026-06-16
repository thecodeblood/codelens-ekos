from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ConflictType(str, Enum):
    CONTRADICTION = "contradiction"
    STALE_REFERENCE = "stale"
    DUPLICATE = "duplicate"
    VERSION_MISMATCH = "version"

class Evidence(BaseModel):
    id: str
    entity_id: str
    entity_type: str                 # "node" or "edge"
    source_type: str                 # "code", "document", "git"
    source_uri: str
    source_location: Optional[str]
    extraction_method: str
    confidence: float
    extracted_in_run: str
    raw_excerpt: Optional[str]

class Conflict(BaseModel):
    id: str
    entity_id: str
    conflict_type: ConflictType
    existing_evidence_id: Optional[str]
    new_evidence_id: Optional[str]
    description: str
    status: str = "open"             # open, resolved, ignored
    resolution: Optional[str] = None
    detected_in_run: str

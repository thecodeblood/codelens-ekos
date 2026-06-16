"""Edge type definitions for the System Model knowledge graph.

Edges represent typed, directed relationships between nodes. Each edge
carries extraction provenance and a confidence score.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.system_model.nodes import ExtractionMethod

logger = logging.getLogger(__name__)


class EdgeType(str, Enum):
    """Complete taxonomy of relationship types in the System Model."""

    CONTAINS = "contains"
    PART_OF = "part_of"
    EXTENDS = "extends"
    IMPORTS = "imports"
    CALLS = "calls"
    EXPOSES = "exposes"
    READS = "reads"
    WRITES = "writes"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    DEPENDS_ON = "depends_on"
    DESCRIBES = "describes"
    IMPLEMENTS = "implements"
    INTRODUCES = "introduces"
    SUPERSEDES = "supersedes"
    AFFECTS = "affects"
    NEXT = "next"
    MODIFIED_BY = "modified_by"


class SystemEdge(BaseModel):
    """A directed, typed edge between two nodes in the System Model.

    Edges are first-class citizens with their own provenance tracking,
    confidence scores, and arbitrary properties.
    """

    id: str = Field(..., description="Unique identifier for this edge.")
    source_id: str = Field(..., description="ID of the source node.")
    target_id: str = Field(..., description="ID of the target node.")
    edge_type: EdgeType = Field(..., description="Semantic type of this relationship.")
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value properties for this edge.",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score [0..1].",
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.MANUAL,
        description="How this edge was extracted.",
    )
    first_seen_run: Optional[str] = Field(
        default=None,
        description="Ingestion run ID that first created this edge.",
    )
    last_updated_run: Optional[str] = Field(
        default=None,
        description="Ingestion run ID that last modified this edge.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

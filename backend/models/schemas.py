"""
CodeLens API Schemas Module.

Defines Pydantic models for all API request validation and response serialization.
These schemas ensure type safety and automatic documentation generation in the
OpenAPI specification served by FastAPI.
"""

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================


class AddSourceRequest(BaseModel):
    """Request body for adding a new source repository.

    Attributes:
        type: Source type identifier (e.g. "git").
        uri: Path or URL pointing to the source repository.
        name: Optional human-readable name. Derived from URI if omitted.
    """

    type: str = Field(..., description="Source type, e.g. 'git'")
    uri: str = Field(..., description="Path or URL to the source repository")
    name: str | None = Field(default=None, description="Optional display name for the source")


class IngestRequest(BaseModel):
    """Request body for triggering ingestion of a source.

    Attributes:
        source_id: Unique identifier of the source to ingest.
    """

    source_id: str = Field(..., description="ID of the source to ingest")


class SearchNodesRequest(BaseModel):
    """Request body for searching nodes in the system model.

    Attributes:
        query: Full-text search query string.
        node_type: Optional filter to restrict results to a specific node type.
        limit: Maximum number of results to return.
    """

    query: str = Field(..., description="Full-text search query")
    node_type: str | None = Field(default=None, description="Filter by node type")
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")


# =============================================================================
# Response Schemas
# =============================================================================


class NodeResponse(BaseModel):
    """Serialized representation of a system model node.

    Attributes:
        id: Unique node identifier.
        type: Node type (e.g. "module", "class", "function").
        name: Short display name.
        qualified_name: Fully-qualified dotted name.
        description: Optional human-readable description or docstring summary.
        properties: Arbitrary key-value metadata attached to the node.
        confidence: Extraction confidence score between 0.0 and 1.0.
        extraction_method: Method used to extract this node (e.g. "tree_sitter").
        tags: Categorization tags.
    """

    id: str
    type: str
    name: str
    qualified_name: str
    description: str | None = None
    properties: dict = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: str
    tags: list[str] = Field(default_factory=list)


class EdgeResponse(BaseModel):
    """Serialized representation of a system model edge (relationship).

    Attributes:
        id: Unique edge identifier.
        source_id: ID of the source node.
        target_id: ID of the target node.
        type: Relationship type (e.g. "calls", "imports", "inherits").
        properties: Arbitrary key-value metadata attached to the edge.
        confidence: Extraction confidence score between 0.0 and 1.0.
    """

    id: str
    source_id: str
    target_id: str
    type: str
    properties: dict = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class ModelStatsResponse(BaseModel):
    """Aggregate statistics about the current system model.

    Attributes:
        total_nodes: Total number of nodes in the model.
        total_edges: Total number of edges in the model.
        nodes_by_type: Count of nodes grouped by type.
        edges_by_type: Count of edges grouped by type.
    """

    total_nodes: int
    total_edges: int
    nodes_by_type: dict[str, int] = Field(default_factory=dict)
    edges_by_type: dict[str, int] = Field(default_factory=dict)


class NeighborResponse(BaseModel):
    """A node together with its immediate edges and neighbor nodes.

    Attributes:
        node: The requested node.
        edges: All edges connected to the node.
        neighbors: Nodes at the other end of each edge.
    """

    node: NodeResponse
    edges: list[EdgeResponse] = Field(default_factory=list)
    neighbors: list[NodeResponse] = Field(default_factory=list)


class SourceResponse(BaseModel):
    """Serialized representation of a registered source repository.

    Attributes:
        id: Unique source identifier.
        type: Source type (e.g. "git").
        uri: Path or URL of the source.
        name: Human-readable display name.
        status: Current status (e.g. "registered", "ingesting", "ingested", "error").
        last_ingested: ISO-8601 timestamp of the last successful ingestion, or None.
    """

    id: str
    type: str
    uri: str
    name: str
    status: str
    last_ingested: str | None = None


class IngestionStatusResponse(BaseModel):
    """Status report for an ingestion run.

    Attributes:
        run_id: Unique identifier for this ingestion run.
        status: Current status (e.g. "running", "completed", "failed").
        files_total: Total number of files discovered.
        files_processed: Number of files successfully processed.
        files_failed: Number of files that failed processing.
        entities_extracted: Total extracted entities count.
        relationships_extracted: Total extracted relationships count.
    """

    run_id: str
    status: str
    files_total: int = 0
    files_processed: int = 0
    files_failed: int = 0
    entities_extracted: int = 0
    relationships_extracted: int = 0


class QualityResponse(BaseModel):
    """Model quality and integrity metrics.

    Attributes:
        integrity_score: Overall integrity score between 0.0 and 1.0.
        total_nodes: Total number of nodes in the model.
        total_edges: Total number of edges in the model.
        orphan_nodes: Number of nodes with no connections.
        avg_confidence: Mean confidence score across all nodes.
        low_confidence_count: Number of nodes with confidence below threshold.
        nodes_by_type: Count of nodes grouped by type.
        edges_by_type: Count of edges grouped by type.
        violations: List of integrity violations found.
    """

    integrity_score: float = Field(ge=0.0, le=1.0)
    total_nodes: int
    total_edges: int
    orphan_nodes: int
    avg_confidence: float
    low_confidence_count: int
    nodes_by_type: dict[str, int] = Field(default_factory=dict)
    edges_by_type: dict[str, int] = Field(default_factory=dict)
    violations: list[dict] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error response body.

    Attributes:
        detail: Human-readable error message.
    """

    detail: str

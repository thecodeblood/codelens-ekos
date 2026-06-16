"""
CodeLens System Model API Routes.

Provides endpoints for inspecting the system model graph — listing, filtering,
and searching nodes and edges, retrieving node neighborhoods, and querying
provenance evidence.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from backend.models.schemas import (
    EdgeResponse,
    ErrorResponse,
    ModelStatsResponse,
    NeighborResponse,
    NodeResponse,
)
from backend.system_model.model import SystemModel
from backend.evidence.tracker import EvidenceTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/model", tags=["model"])


def _get_model(request: Request) -> SystemModel:
    """Extract the SystemModel instance from application state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The shared SystemModel instance.
    """
    return request.app.state.model


def _get_tracker(request: Request) -> EvidenceTracker:
    """Extract the EvidenceTracker instance from application state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The shared EvidenceTracker instance.
    """
    return request.app.state.tracker


@router.get(
    "/stats",
    response_model=ModelStatsResponse,
    summary="Get model statistics",
    description="Returns aggregate counts of nodes and edges grouped by type.",
)
async def get_model_stats(
    model: Annotated[SystemModel, Depends(_get_model)],
) -> ModelStatsResponse:
    """Return aggregate statistics for the system model.

    Computes total node/edge counts and breakdowns by type.
    """
    try:
        all_nodes = model.get_all_nodes()
        all_edges = model.get_all_edges()

        nodes_by_type: dict[str, int] = {}
        for node in all_nodes:
            nodes_by_type[node.node_type.value] = nodes_by_type.get(node.node_type.value, 0) + 1

        edges_by_type: dict[str, int] = {}
        for edge in all_edges:
            edges_by_type[edge.edge_type.value] = edges_by_type.get(edge.edge_type.value, 0) + 1

        return ModelStatsResponse(
            total_nodes=len(all_nodes),
            total_edges=len(all_edges),
            nodes_by_type=nodes_by_type,
            edges_by_type=edges_by_type,
        )
    except Exception as exc:
        logger.exception("Failed to compute model stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute model stats: {exc}",
        ) from exc


@router.get(
    "/nodes",
    response_model=list[NodeResponse],
    summary="List nodes",
    description="Returns all nodes in the model, optionally filtered by type.",
)
async def list_nodes(
    model: Annotated[SystemModel, Depends(_get_model)],
    type: Annotated[str | None, Query(description="Filter by node type")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Max results")] = 100,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
) -> list[NodeResponse]:
    """List system model nodes with optional type filtering and pagination."""
    try:
        if type is not None:
            nodes = model.get_nodes_by_type(type)
        else:
            nodes = model.get_all_nodes()

        paginated = nodes[offset : offset + limit]

        return [
            NodeResponse(
                id=node.id,
                type=node.node_type.value,
                name=node.name,
                qualified_name=node.qualified_name,
                description=node.description,
                properties=node.properties_dict(),
                confidence=node.confidence,
                extraction_method=node.extraction_method.value,
                tags=node.tags or [],
            )
            for node in paginated
        ]
    except Exception as exc:
        logger.exception("Failed to list nodes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list nodes: {exc}",
        ) from exc


@router.get(
    "/nodes/{node_id}",
    response_model=NodeResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get node by ID",
    description="Returns a single node by its unique identifier.",
)
async def get_node(
    node_id: str,
    model: Annotated[SystemModel, Depends(_get_model)],
) -> NodeResponse:
    """Retrieve a specific system model node by ID.

    Raises:
        HTTPException: 404 if the node does not exist.
    """
    node = model.get_node(node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found",
        )
    return NodeResponse(
        id=node.id,
        type=node.node_type.value,
        name=node.name,
        qualified_name=node.qualified_name,
        description=node.description,
        properties=node.properties_dict(),
        confidence=node.confidence,
        extraction_method=node.extraction_method.value,
        tags=node.tags or [],
    )


@router.get(
    "/nodes/{node_id}/neighbors",
    response_model=NeighborResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get node neighbors",
    description="Returns the node, its edges, and all directly connected neighbor nodes.",
)
async def get_node_neighbors(
    node_id: str,
    model: Annotated[SystemModel, Depends(_get_model)],
) -> NeighborResponse:
    """Retrieve a node and its immediate graph neighborhood.

    Returns the node itself, all edges touching it, and the nodes at the
    other end of those edges.

    Raises:
        HTTPException: 404 if the node does not exist.
    """
    node = model.get_node(node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found",
        )

    edges = model.get_edges_for_node(node_id)
    neighbor_ids: set[str] = set()
    for edge in edges:
        if edge.source_id == node_id:
            neighbor_ids.add(edge.target_id)
        else:
            neighbor_ids.add(edge.source_id)

    neighbors: list[NodeResponse] = []
    for nid in neighbor_ids:
        neighbor_node = model.get_node(nid)
        if neighbor_node is not None:
            neighbors.append(
                NodeResponse(
                    id=neighbor_node.id,
                    type=neighbor_node.node_type.value,
                    name=neighbor_node.name,
                    qualified_name=neighbor_node.qualified_name,
                    description=neighbor_node.description,
                    properties=neighbor_node.properties_dict(),
                    confidence=neighbor_node.confidence,
                    extraction_method=neighbor_node.extraction_method.value,
                    tags=neighbor_node.tags or [],
                )
            )

    edge_responses = [
        EdgeResponse(
            id=edge.id,
            source_id=edge.source_id,
            target_id=edge.target_id,
            type=edge.edge_type.value,
            properties=edge.properties,
            confidence=edge.confidence,
        )
        for edge in edges
    ]

    return NeighborResponse(
        node=NodeResponse(
            id=node.id,
            type=node.node_type.value,
            name=node.name,
            qualified_name=node.qualified_name,
            description=node.description,
            properties=node.properties_dict(),
            confidence=node.confidence,
            extraction_method=node.extraction_method.value,
            tags=node.tags or [],
        ),
        edges=edge_responses,
        neighbors=neighbors,
    )


@router.get(
    "/nodes/{node_id}/evidence",
    response_model=list[dict],
    responses={404: {"model": ErrorResponse}},
    summary="Get node evidence",
    description="Returns all provenance evidence records for a node.",
)
async def get_node_evidence(
    node_id: str,
    model: Annotated[SystemModel, Depends(_get_model)],
    tracker: Annotated[EvidenceTracker, Depends(_get_tracker)],
) -> list[dict]:
    """Retrieve provenance evidence for a specific node.

    Returns all evidence records that contributed to the creation or
    update of the given node.

    Raises:
        HTTPException: 404 if the node does not exist.
    """
    node = model.get_node(node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found",
        )

    evidence_list = tracker.get_evidence(node_id)
    return [
        {
            "id": ev.id,
            "node_id": ev.entity_id,
            "evidence_type": ev.source_type,
            "source_file": ev.source_uri,
            "start_line": ev.source_location,
            "end_line": ev.source_location,
            "content": ev.raw_excerpt,
            "extraction_method": ev.extraction_method,
            "confidence": ev.confidence,
            "run_id": ev.extracted_in_run,
            "timestamp": ev.extracted_in_run,
        }
        for ev in evidence_list
    ]


@router.get(
    "/edges",
    response_model=list[EdgeResponse],
    summary="List edges",
    description="Returns all edges in the model, optionally filtered by type.",
)
async def list_edges(
    model: Annotated[SystemModel, Depends(_get_model)],
    type: Annotated[str | None, Query(description="Filter by edge type")] = None,
    limit: Annotated[int, Query(ge=1, le=500, description="Max results")] = 100,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
) -> list[EdgeResponse]:
    """List system model edges with optional type filtering and pagination."""
    try:
        if type is not None:
            edges = model.get_edges_by_type(type)
        else:
            edges = model.get_all_edges()

        paginated = edges[offset : offset + limit]

        return [
            EdgeResponse(
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                type=edge.edge_type.value,
                properties=edge.properties,
                confidence=edge.confidence,
            )
            for edge in paginated
        ]
    except Exception as exc:
        logger.exception("Failed to list edges")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list edges: {exc}",
        ) from exc


@router.get(
    "/search",
    response_model=list[NodeResponse],
    summary="Search nodes",
    description="Full-text search across node names and descriptions.",
)
async def search_nodes(
    model: Annotated[SystemModel, Depends(_get_model)],
    q: Annotated[str, Query(min_length=1, description="Search query")],
    node_type: Annotated[str | None, Query(description="Filter by node type")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max results")] = 20,
) -> list[NodeResponse]:
    """Search for nodes using full-text search.

    Queries are matched against node names, qualified names, and descriptions.
    Results can be optionally filtered by node type.
    """
    try:
        results = model.search_nodes(query=q, node_type=node_type, limit=limit)

        return [
            NodeResponse(
                id=node.id,
                type=node.node_type.value,
                name=node.name,
                qualified_name=node.qualified_name,
                description=node.description,
                properties=node.properties_dict(),
                confidence=node.confidence,
                extraction_method=node.extraction_method.value,
                tags=node.tags or [],
            )
            for node in results
        ]
    except Exception as exc:
        logger.exception("Failed to search nodes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {exc}",
        ) from exc

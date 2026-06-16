"""
CodeLens Model Quality API Routes.

Provides an endpoint for running integrity checks against the system model
and returning quality metrics including confidence analysis, orphan detection,
and constraint violation reporting.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.models.schemas import QualityResponse
from backend.system_model.model import SystemModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/model", tags=["quality"])


def _get_model(request: Request) -> SystemModel:
    """Extract the SystemModel instance from application state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The shared SystemModel instance.
    """
    return request.app.state.model


@router.get(
    "/quality",
    response_model=QualityResponse,
    summary="Get model quality metrics",
    description="Runs integrity validation and returns quality metrics for the system model.",
)
async def get_model_quality(
    model: Annotated[SystemModel, Depends(_get_model)],
    request: Request,
) -> QualityResponse:
    """Compute and return quality metrics for the current system model.

    Performs the following analyses:
    - Counts nodes and edges by type
    - Identifies orphan nodes (nodes with no edges)
    - Computes average confidence scores
    - Counts low-confidence nodes (below 0.5 threshold)
    - Runs integrity validation if an IntegrityEngine is available
    - Calculates an overall integrity score

    Returns:
        QualityResponse with all computed metrics.
    """
    try:
        all_nodes = model.get_all_nodes()
        all_edges = model.get_all_edges()

        # --- Node and edge type counts ---
        nodes_by_type: dict[str, int] = {}
        for node in all_nodes:
            nodes_by_type[node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)] = nodes_by_type.get(node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type), 0) + 1

        edges_by_type: dict[str, int] = {}
        for edge in all_edges:
            edges_by_type[edge.edge_type.value if hasattr(edge.edge_type, 'value') else str(edge.edge_type)] = edges_by_type.get(edge.edge_type.value if hasattr(edge.edge_type, 'value') else str(edge.edge_type), 0) + 1

        total_nodes = len(all_nodes)
        total_edges = len(all_edges)

        # --- Orphan detection ---
        connected_node_ids: set[str] = set()
        for edge in all_edges:
            connected_node_ids.add(edge.source_id)
            connected_node_ids.add(edge.target_id)

        orphan_nodes = sum(
            1 for node in all_nodes if node.id not in connected_node_ids
        )

        # --- Confidence analysis ---
        confidence_threshold = 0.5
        if total_nodes > 0:
            total_confidence = sum(node.confidence for node in all_nodes)
            avg_confidence = total_confidence / total_nodes
            low_confidence_count = sum(
                1 for node in all_nodes if node.confidence < confidence_threshold
            )
        else:
            avg_confidence = 1.0
            low_confidence_count = 0

        # --- Integrity validation ---
        violations: list[dict] = []
        integrity_score = 1.0

        integrity_engine = getattr(request.app.state, "integrity_engine", None)
        if integrity_engine is not None:
            try:
                validation_result = integrity_engine.validate()
                violations = [
                    {
                        "type": v.type,
                        "severity": v.severity,
                        "message": v.message,
                        "node_id": getattr(v, "node_id", None),
                        "edge_id": getattr(v, "edge_id", None),
                    }
                    for v in validation_result.violations
                ]
                integrity_score = validation_result.score
            except Exception as validation_exc:
                logger.warning("Integrity validation failed: %s", validation_exc)
                violations.append(
                    {
                        "type": "validation_error",
                        "severity": "warning",
                        "message": f"Integrity validation failed: {validation_exc}",
                        "node_id": None,
                        "edge_id": None,
                    }
                )
        else:
            # Compute a simple heuristic score when no integrity engine is available
            if total_nodes > 0:
                orphan_penalty = orphan_nodes / total_nodes * 0.3
                confidence_penalty = (1.0 - avg_confidence) * 0.4
                low_conf_penalty = (
                    (low_confidence_count / total_nodes) * 0.3
                    if total_nodes > 0
                    else 0.0
                )
                integrity_score = max(
                    0.0, 1.0 - orphan_penalty - confidence_penalty - low_conf_penalty
                )
            else:
                integrity_score = 1.0

        return QualityResponse(
            integrity_score=round(integrity_score, 4),
            total_nodes=total_nodes,
            total_edges=total_edges,
            orphan_nodes=orphan_nodes,
            avg_confidence=round(avg_confidence, 4),
            low_confidence_count=low_confidence_count,
            nodes_by_type=nodes_by_type,
            edges_by_type=edges_by_type,
            violations=violations,
        )

    except Exception as exc:
        logger.exception("Failed to compute model quality")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute model quality: {exc}",
        ) from exc

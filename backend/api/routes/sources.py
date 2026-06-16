"""
CodeLens Source Management API Routes.

Provides endpoints for registering source repositories, triggering ingestion
pipelines, checking ingestion status, and removing sources from the system.
"""

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.config import Settings
from backend.models.schemas import (
    AddSourceRequest,
    ErrorResponse,
    IngestionStatusResponse,
    SourceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


# =============================================================================
# Source table management
# =============================================================================

# =============================================================================
# Dependencies
# =============================================================================


def _get_settings(request: Request) -> Settings:
    """Extract Settings from application state."""
    return request.app.state.settings


def _get_db_path(request: Request) -> str:
    """Extract the database path from application settings."""
    return request.app.state.settings.db_path


# =============================================================================
# Helper functions
# =============================================================================


def _row_to_source(row: tuple) -> SourceResponse:
    """Convert a database row to a SourceResponse.

    Args:
        row: Tuple of (id, type, uri, name, status, last_ingested, created_at, updated_at).

    Returns:
        SourceResponse populated from the database row.
    """
    return SourceResponse(
        id=row[0],
        type=row[1],
        uri=row[2],
        name=row[3],
        status=row[4],
        last_ingested=row[5],
    )


def _row_to_ingestion_status(row: tuple) -> IngestionStatusResponse:
    """Convert a database row to an IngestionStatusResponse.

    Args:
        row: Tuple of ingestion run columns.

    Returns:
        IngestionStatusResponse populated from the database row.
    """
    return IngestionStatusResponse(
        run_id=row[0],
        status=row[2],
        files_total=row[3],
        files_processed=row[4],
        files_failed=row[5],
        entities_extracted=row[6],
        relationships_extracted=row[7],
    )


# =============================================================================
# Routes
# =============================================================================


@router.post(
    "",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
    summary="Add a source",
    description="Register a new source repository for ingestion.",
)
async def add_source(
    body: AddSourceRequest,
    db_path: Annotated[str, Depends(_get_db_path)],
) -> SourceResponse:
    """Register a new source repository.

    Creates a source entry with 'registered' status. A name is derived from
    the URI if none is provided.

    Raises:
        HTTPException: 409 if a source with the same URI already exists.
    """
    source_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    name = body.name or body.uri.rstrip("/").split("/")[-1]

    conn = sqlite3.connect(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM sources WHERE uri = ?", (body.uri,)
        ).fetchone()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Source with URI '{body.uri}' already exists (id={existing[0]})",
            )

        conn.execute(
            "INSERT INTO sources (id, type, uri, name, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'registered', ?, ?)",
            (source_id, body.type, body.uri, name, now, now),
        )
        conn.commit()

        logger.info("Registered source '%s' (%s) with id %s", name, body.uri, source_id)

        return SourceResponse(
            id=source_id,
            type=body.type,
            uri=body.uri,
            name=name,
            status="registered",
            last_ingested=None,
        )
    finally:
        conn.close()


@router.get(
    "",
    response_model=list[SourceResponse],
    summary="List sources",
    description="Returns all registered sources.",
)
async def list_sources(
    db_path: Annotated[str, Depends(_get_db_path)],
) -> list[SourceResponse]:
    """List all registered source repositories."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, type, uri, name, status, last_ingested, created_at, updated_at "
            "FROM sources ORDER BY created_at DESC"
        ).fetchall()
        return [_row_to_source(row) for row in rows]
    finally:
        conn.close()


@router.post(
    "/{source_id}/ingest",
    response_model=IngestionStatusResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Trigger ingestion",
    description="Starts the ingestion pipeline for the given source.",
)
async def trigger_ingestion(
    source_id: str,
    request: Request,
    db_path: Annotated[str, Depends(_get_db_path)],
) -> IngestionStatusResponse:
    """Trigger the ingestion pipeline for a registered source.

    Runs the full pipeline synchronously: parse files, extract entities and
    relationships, build the system model. For MVP this is fast enough for
    small repositories.

    Raises:
        HTTPException: 404 if the source does not exist.
        HTTPException: 500 if ingestion fails.
    """
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, type, uri, name, status, last_ingested, created_at, updated_at "
            "FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found",
            )

        source = _row_to_source(row)

        # Create ingestion run record
        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO ingestion_runs "
            "(id, source_id, status, started_at) VALUES (?, ?, 'running', ?)",
            (run_id, source_id, now),
        )
        conn.execute(
            "UPDATE sources SET status = 'ingesting', updated_at = ? WHERE id = ?",
            (now, source_id),
        )
        conn.commit()
    finally:
        conn.close()

    # Run the ingestion pipeline
    try:
        from backend.ingestion.coordinator import PipelineCoordinator

        coordinator: PipelineCoordinator = request.app.state.coordinator
        ingestion_result = coordinator.ingest_repository(
            repo_path=source.uri,
            source_id=source_id,
        )

        # Update run record with results
        completed_at = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "UPDATE ingestion_runs SET "
                "status = 'completed', "
                "files_total = ?, files_processed = ?, files_failed = ?, "
                "entities_extracted = ?, relationships_extracted = ?, "
                "completed_at = ? "
                "WHERE id = ?",
                (
                    ingestion_result.stats.files_total,
                    ingestion_result.stats.files_processed,
                    ingestion_result.stats.files_failed,
                    ingestion_result.stats.entities_extracted,
                    ingestion_result.stats.relationships_extracted,
                    completed_at,
                    run_id,
                ),
            )
            conn.execute(
                "UPDATE sources SET status = 'ingested', last_ingested = ?, updated_at = ? "
                "WHERE id = ?",
                (completed_at, completed_at, source_id),
            )
            conn.commit()
        finally:
            conn.close()

        logger.info(
            "Ingestion completed for source '%s': %d files, %d entities, %d relationships",
            source.name,
            ingestion_result.stats.files_processed,
            ingestion_result.stats.entities_extracted,
            ingestion_result.stats.relationships_extracted,
        )

        return IngestionStatusResponse(
            run_id=run_id,
            status="completed",
            files_total=ingestion_result.stats.files_total,
            files_processed=ingestion_result.stats.files_processed,
            files_failed=ingestion_result.stats.files_failed,
            entities_extracted=ingestion_result.stats.entities_extracted,
            relationships_extracted=ingestion_result.stats.relationships_extracted,
        )

    except Exception as exc:
        # Mark the run and source as failed
        failed_at = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "UPDATE ingestion_runs SET status = 'failed', completed_at = ? WHERE id = ?",
                (failed_at, run_id),
            )
            conn.execute(
                "UPDATE sources SET status = 'error', updated_at = ? WHERE id = ?",
                (failed_at, source_id),
            )
            conn.commit()
        finally:
            conn.close()

        logger.exception("Ingestion failed for source '%s'", source_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        ) from exc


@router.get(
    "/{source_id}/status",
    response_model=IngestionStatusResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get ingestion status",
    description="Returns the status of the most recent ingestion run for a source.",
)
async def get_ingestion_status(
    source_id: str,
    db_path: Annotated[str, Depends(_get_db_path)],
) -> IngestionStatusResponse:
    """Get the status of the most recent ingestion run for a source.

    Raises:
        HTTPException: 404 if no ingestion run exists for this source.
    """
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT id as run_id, source_id, status, files_total, files_processed, "
            "files_failed, entities_extracted, relationships_extracted "
            "FROM ingestion_runs WHERE source_id = ? ORDER BY started_at DESC LIMIT 1",
            (source_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No ingestion runs found for source '{source_id}'",
            )
        return _row_to_ingestion_status(row)
    finally:
        conn.close()


@router.delete(
    "/{source_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}},
    summary="Delete a source",
    description="Removes a source and its ingestion history.",
)
async def delete_source(
    source_id: str,
    db_path: Annotated[str, Depends(_get_db_path)],
) -> dict:
    """Delete a registered source and all associated ingestion run records.

    Raises:
        HTTPException: 404 if the source does not exist.
    """
    conn = sqlite3.connect(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM sources WHERE id = ?", (source_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found",
            )

        conn.execute("DELETE FROM ingestion_runs WHERE source_id = ?", (source_id,))
        conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        conn.commit()

        logger.info("Deleted source %s and associated ingestion runs", source_id)
        return {"detail": "deleted"}
    finally:
        conn.close()

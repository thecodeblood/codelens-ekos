"""
CodeLens Model Builder Module.

The ModelBuilder is the bridge between the Understanding Layer and the System Model.
It converts ExtractedEntity and ExtractedRelationship instances produced by code
analysis into SystemNode and SystemEdge graph elements, resolving canonical identities
and recording provenance evidence for every created or updated element.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.evidence.models import Evidence
from backend.evidence.tracker import EvidenceTracker
from backend.system_model.canonical import CanonicalEntityRegistry
from backend.system_model.model import SystemModel
from backend.system_model.edges import SystemEdge
from backend.system_model.nodes import SystemNode, ExtractionMethod
from backend.understanding.models import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """Summary of a model-building pass."""

    nodes_created: int = 0
    nodes_updated: int = 0
    edges_created: int = 0
    edges_updated: int = 0
    conflicts: list[str] = field(default_factory=list)


class ModelBuilder:
    def __init__(
        self,
        model: SystemModel,
        registry: CanonicalEntityRegistry,
        tracker: EvidenceTracker,
    ) -> None:
        self.model = model
        self.registry = registry
        self.tracker = tracker

    def build_from_extraction(self, result: ExtractionResult, run_id: str) -> BuildResult:
        build_result = BuildResult()

        # --- Phase 1: Process entities → nodes ---
        qname_to_node_id: dict[str, str] = {}

        for entity in result.entities:
            try:
                node = self._entity_to_node(entity, run_id)
                existing_node = self.model.get_node(node.id)

                if existing_node is not None:
                    self.model.update_node(node)
                    build_result.nodes_updated += 1
                    logger.debug("Updated node %s (%s)", node.id, node.qualified_name)
                else:
                    self.model.add_node(node)
                    build_result.nodes_created += 1
                    logger.debug("Created node %s (%s)", node.id, node.qualified_name)

                qname_to_node_id[entity.qualified_name] = node.id

                evidence = self._create_evidence(entity, node.id, run_id, entity_type="node")
                self.tracker.record(evidence)

            except Exception as exc:
                conflict_msg = f"Failed to process entity '{entity.name}': {exc}"
                build_result.conflicts.append(conflict_msg)
                logger.warning(conflict_msg)

        # --- Phase 2: Process relationships → edges ---
        for rel in result.relationships:
            try:
                edge = self._relationship_to_edge(rel, run_id, qname_to_node_id)
                existing_edge = self.model.get_edge(edge.id)

                if existing_edge is not None:
                    # Added try block since update_edge might not exist yet
                    if hasattr(self.model, "update_edge"):
                        self.model.update_edge(edge)
                        build_result.edges_updated += 1
                        logger.debug("Updated edge %s (%s -> %s)", edge.id, edge.source_id, edge.target_id)
                    else:
                        # Fallback for now if update_edge is missing
                        self.model.remove_edge(edge.id)
                        self.model.add_edge(edge)
                        build_result.edges_updated += 1
                else:
                    self.model.add_edge(edge)
                    build_result.edges_created += 1
                    logger.debug("Created edge %s (%s -> %s)", edge.id, edge.source_id, edge.target_id)
                    
                evidence = self._create_evidence(rel, edge.id, run_id, entity_type="edge")
                self.tracker.record(evidence)

            except Exception as exc:
                conflict_msg = f"Failed to process relationship '{rel.source_qualified_name}' -> '{rel.target_qualified_name}': {exc}"
                build_result.conflicts.append(conflict_msg)
                logger.warning(conflict_msg)

        logger.info(
            "Build complete for run %s: %d nodes created, %d updated, %d edges created, %d updated, %d conflicts",
            run_id, build_result.nodes_created, build_result.nodes_updated,
            build_result.edges_created, build_result.edges_updated, len(build_result.conflicts),
        )

        return build_result

    def _entity_to_node(self, entity: ExtractedEntity, run_id: str) -> SystemNode:
        # resolve signature is (surface_form, node_type)
        canonical_id = self.registry.resolve(
            surface_form=entity.qualified_name,
            node_type=entity.entity_type,
        )
        # If the registry didn't return one (it doesn't auto-register currently), generate one
        if not canonical_id:
            # We'll just hash the qualified_name to create a stable canonical_id for Phase 1
            canonical_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entity.qualified_name))
            # Optional: self.registry.register(canonical_id, entity.name, entity.entity_type, ...)

        properties = dict(entity.properties) if entity.properties else {}
        properties["source_file"] = entity.source_file
        if entity.line_start is not None:
            properties["line_start"] = entity.line_start
        if entity.line_end is not None:
            properties["line_end"] = entity.line_end
        properties["run_id"] = run_id

        # Mapping extraction method string to Enum safely
        try:
            em = ExtractionMethod(entity.extraction_method)
        except ValueError:
            em = ExtractionMethod.MANUAL

        return SystemNode(
            id=canonical_id,
            node_type=entity.entity_type,
            name=entity.name,
            qualified_name=entity.qualified_name,
            description=properties.get("docstring"), # Use docstring if available
            properties=properties,
            confidence=entity.confidence,
            extraction_method=em,
            tags=[]
        )

    def _relationship_to_edge(
        self,
        rel: ExtractedRelationship,
        run_id: str,
        qname_to_node_id: dict[str, str],
    ) -> SystemEdge:
        source_node_id = qname_to_node_id.get(rel.source_qualified_name)
        if source_node_id is None:
            source_node_id = self.registry.resolve(surface_form=rel.source_qualified_name, node_type=None)
            if not source_node_id:
                source_node_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rel.source_qualified_name))

        target_node_id = qname_to_node_id.get(rel.target_qualified_name)
        if target_node_id is None:
            target_node_id = self.registry.resolve(surface_form=rel.target_qualified_name, node_type=None)
            if not target_node_id:
                target_node_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rel.target_qualified_name))

        properties = dict(rel.properties) if rel.properties else {}
        properties["run_id"] = run_id

        edge_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"{source_node_id}:{rel.relationship_type}:{target_node_id}",
            )
        )

        return SystemEdge(
            id=edge_id,
            source_id=source_node_id,
            target_id=target_node_id,
            edge_type=rel.relationship_type,
            properties=properties,
            confidence=rel.confidence,
        )

    def _create_evidence(
        self, extracted_item, element_id: str, run_id: str, entity_type: str
    ) -> Evidence:
        """Create an evidence record linking an element back to its source extraction."""
        
        # Check if it's an entity or relationship
        is_entity = hasattr(extracted_item, "line_start")
        
        loc_str = ""
        if is_entity and extracted_item.line_start is not None:
            loc_str = f"L{extracted_item.line_start}"
            if extracted_item.line_end is not None and extracted_item.line_end != extracted_item.line_start:
                loc_str += f"-L{extracted_item.line_end}"

        raw_excerpt = None
        if is_entity and "docstring" in extracted_item.properties and extracted_item.properties["docstring"]:
             raw_excerpt = extracted_item.properties["docstring"]

        return Evidence(
            id=str(uuid.uuid4()),
            entity_id=element_id,
            entity_type=entity_type,  # "node" or "edge"
            source_type="code",
            source_uri=extracted_item.source_file,
            source_location=loc_str if loc_str else None,
            extraction_method=extracted_item.extraction_method,
            confidence=extracted_item.confidence,
            extracted_in_run=run_id,
            raw_excerpt=raw_excerpt
        )

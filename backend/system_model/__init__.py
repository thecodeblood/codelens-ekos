"""System Model Core — Multi-graph knowledge representation for software systems.

This package provides the core data model, persistence, and graph operations
for the CodeLens Engineering Knowledge Operating System.
"""

from backend.system_model.nodes import NodeType, SystemNode, ExtractionMethod, NodeCategory
from backend.system_model.edges import EdgeType, SystemEdge
from backend.system_model.model import SystemModel
from backend.system_model.canonical import CanonicalEntityRegistry
from backend.system_model.entity_resolver import EntityResolver, ResolvedEntity
from backend.system_model.integrity import IntegrityEngine, IntegrityReport
from backend.system_model.snapshots import SnapshotManager

__all__ = [
    "NodeType",
    "SystemNode",
    "ExtractionMethod",
    "NodeCategory",
    "EdgeType",
    "SystemEdge",
    "SystemModel",
    "CanonicalEntityRegistry",
    "EntityResolver",
    "ResolvedEntity",
    "IntegrityEngine",
    "IntegrityReport",
    "SnapshotManager",
]

from pydantic import BaseModel
from typing import Optional
from .nodes import NodeType
from .model import SystemModel
from .canonical import CanonicalEntityRegistry

class ResolvedEntity(BaseModel):
    node_id: str
    name: str
    type: str
    confidence: float
    match_method: str

class EntityResolver:
    """Resolves natural language entities to System Model nodes."""
    
    def __init__(self, model: SystemModel, registry: CanonicalEntityRegistry):
        self.model = model
        self.registry = registry

    def resolve(self, query: str, node_type: Optional[NodeType] = None) -> list[ResolvedEntity]:
        """
        Resolution chain: exact name match → canonical alias match → FTS5 fuzzy search
        """
        results = []
        
        # We rely on CanonicalEntityRegistry for the first few steps
        nt_str = node_type.value if node_type else None
        
        import re
        clean_query = re.sub(r'[^\w\s]', '', query).strip()
        stop_words = {"how", "does", "work", "what", "is", "where", "show", "explain", "the", "a", "an", "for", "in", "of", "and", "or", "to", "workflow", "flow", "process", "dependencies", "depends", "on", "impact", "changing", "modifying", "removing", "breaks", "if", "why", "was", "introduced", "chosen", "selected", "used", "do", "we", "use", "rationale", "behind", "changed", "history", "evolution", "when", "added", "modified", "who", "owns", "maintains", "responsible", "team", "which", "code", "service", "function", "implementation", "implemented", "relies", "on"}
        core_query = " ".join([w for w in clean_query.split() if w.lower() not in stop_words])
        if not core_query:
            return results
            
        # 1. Try canonical registry
        canonical_id = self.registry.resolve(core_query, nt_str)
        if canonical_id:
            # Fetch node
            node = self.model.get_node(canonical_id)
            if node:
                results.append(ResolvedEntity(
                    node_id=node.id,
                    name=node.name,
                    type=node.node_type.value,
                    confidence=1.0,
                    match_method="exact_or_alias"
                ))
                return results
                
        # 2. If not found, use SystemModel FTS5 fuzzy search
        # Note: system model should expose search_nodes
        search_results = self.model.search_nodes(core_query) if core_query else []
        if node_type:
            search_results = [n for n in search_results if n.node_type.value == nt_str]
            
        for node in search_results:
            results.append(ResolvedEntity(
                node_id=node.id,
                name=node.name,
                type=node.node_type.value,
                confidence=0.8, # Lower confidence for fuzzy search
                match_method="fts5_fuzzy"
            ))
            
        return results

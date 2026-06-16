from backend.system_model.edges import EdgeType

class DependencyAnalyzer:
    """Analyzes dependencies and computes architectural impacts."""
    
    def __init__(self, model):
        self.model = model
        
    def execute(self, inputs: dict) -> dict:
        entity_id = inputs.get("entity_id")
        if not entity_id:
            return {"error": "Missing entity_id for dependency analysis"}
            
        # Fetch the connected subgraph for dependencies and imports
        nodes, edges = self.model.get_connected_subgraph(
            entity_id, 
            max_depth=5, 
            edge_types=[EdgeType.DEPENDS_ON, EdgeType.IMPORTS]
        )
        
        return {
            "entity_id": entity_id,
            "nodes": [n.model_dump() for n in nodes],
            "edges": [e.model_dump() for e in edges]
        }

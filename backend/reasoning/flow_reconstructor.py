class FlowReconstructor:
    """Reconstructs execution call chains for flow queries."""
    
    def __init__(self, model):
        self.model = model
        
    def execute(self, inputs: dict) -> dict:
        entity_id = inputs.get("entity_id")
        if not entity_id:
            return {"error": "Missing entity_id for flow reconstruction"}
            
        # Get all downstream call chains
        paths = self.model.get_call_chain(entity_id, max_depth=10)
        
        # Resolve nodes in paths
        resolved_paths = []
        for path in paths:
            resolved_path = []
            for nid in path:
                node = self.model.get_node(nid)
                if node:
                    resolved_path.append(node.model_dump())
            resolved_paths.append(resolved_path)
            
        return {
            "entity_id": entity_id,
            "call_chains": resolved_paths
        }

class KnowledgeTraverser:
    """Executes general graph exploration and entity resolution."""
    
    def __init__(self, model):
        self.model = model
        
    def execute(self, inputs: dict) -> dict:
        if "entity_id" in inputs:
            node_id = inputs["entity_id"]
            node = self.model.get_node(node_id)
            if not node:
                return {"error": "Node not found"}
                
            neighbors = self.model.get_neighbors(node_id)
            return {
                "entity_id": node.id,
                "node": node.model_dump(),
                "neighbors": [n.model_dump() for n in neighbors]
            }
        elif "query" in inputs:
            if inputs.get("operation") == "get_project_summary":
                # Fetch high level nodes to summarize the project
                from backend.system_model.nodes import NodeType
                services = self.model.get_nodes_by_type(NodeType.SERVICE)
                repositories = self.model.get_nodes_by_type(NodeType.REPOSITORY)
                domains = self.model.get_nodes_by_type(NodeType.DOMAIN)
                return {
                    "summary": True,
                    "services": [n.model_dump() for n in services],
                    "repositories": [n.model_dump() for n in repositories],
                    "domains": [n.model_dump() for n in domains],
                    "total_nodes": len(self.model.get_all_nodes())
                }
            
            nodes = self.model.search_nodes(inputs["query"])
            return {
                "nodes": [n.model_dump() for n in nodes]
            }
        return {}

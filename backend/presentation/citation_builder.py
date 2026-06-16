class CitationBuilder:
    """Builds provenance citations for generated responses."""
    
    def build_citations(self, nodes: list[dict]) -> list[dict]:
        citations = []
        for n in nodes:
            citations.append({
                "entity_id": n.get("id"),
                "name": n.get("name"),
                "type": n.get("node_type"),
                "confidence": n.get("confidence", 1.0),
                "extraction_method": n.get("extraction_method", "ast")
            })
        return citations

class DiagramGenerator:
    """Generates Mermaid diagrams from reasoning results."""
    
    def generate_flow_diagram(self, paths: list[list[dict]]) -> str:
        if not paths or (len(paths) == 1 and len(paths[0]) == 0):
            return "graph TD\n    A[No flow found]"
            
        lines = ["graph TD"]
        edges_added = set()
        
        for path in paths:
            for i in range(len(path) - 1):
                src = path[i]
                tgt = path[i+1]
                # Ensure we have IDs to make valid mermaid node identifiers
                src_node_id = src['id'].replace(':', '_').replace('-', '_').replace('.', '_')
                tgt_node_id = tgt['id'].replace(':', '_').replace('-', '_').replace('.', '_')
                edge_id = f"{src_node_id}->{tgt_node_id}"
                
                if edge_id not in edges_added:
                    src_name = src.get('name', src['id'])
                    tgt_name = tgt.get('name', tgt['id'])
                    src_label = src_name.replace('"', '').replace('(', '').replace(')', '')
                    tgt_label = tgt_name.replace('"', '').replace('(', '').replace(')', '')
                    
                    lines.append(f"    {src_node_id}[\"{src_label}\"] --> {tgt_node_id}[\"{tgt_label}\"]")
                    edges_added.add(edge_id)
                    
        return "\n".join(lines)
        
    def generate_dependency_diagram(self, nodes: list[dict], edges: list[dict]) -> str:
        if not nodes:
            return "graph TD\n    A[No dependencies found]"
            
        lines = ["graph TD"]
        node_map = {n['id']: n for n in nodes}
        
        for e in edges:
            src_id = e['source_id']
            tgt_id = e['target_id']
            if src_id in node_map and tgt_id in node_map:
                src_node_id = src_id.replace(':', '_').replace('-', '_').replace('.', '_')
                tgt_node_id = tgt_id.replace(':', '_').replace('-', '_').replace('.', '_')
                
                src_name = node_map[src_id].get('name', src_id).replace('"', '')
                tgt_name = node_map[tgt_id].get('name', tgt_id).replace('"', '')
                lines.append(f"    {src_node_id}[\"{src_name}\"] -->|{e.get('type', e.get('edge_type', ''))}| {tgt_node_id}[\"{tgt_name}\"]")
                
        return "\n".join(lines)

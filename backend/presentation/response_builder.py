from backend.reasoning.planner import QueryPlan, ReasonerType
from backend.presentation.diagram_generator import DiagramGenerator
from backend.presentation.citation_builder import CitationBuilder
import json

class ResponseBuilder:
    """Assembles final query response payload including diagram and citations."""
    
    def __init__(self, llm_client=None):
        self.diagram_generator = DiagramGenerator()
        self.citation_builder = CitationBuilder()
        self.llm = llm_client
        
    def build(self, plan: QueryPlan, results: dict) -> dict:
        markdown = f"### Query Plan Executed: {plan.intent.value}\n\n"
        diagram = ""
        all_nodes_referenced = []
        raw_context_for_llm = []
        
        for step in plan.steps:
            res = results.get(step.step_id, {})
            
            if step.reasoner == ReasonerType.KNOWLEDGE and "nodes" in res:
                nodes = res["nodes"]
                all_nodes_referenced.extend(nodes)
                if nodes:
                    raw_context_for_llm.append({"step": step.operation, "found_entities": [n.get('name') for n in nodes]})
                
            elif step.reasoner == ReasonerType.FLOW and "call_chains" in res:
                paths = res["call_chains"]
                for p in paths:
                    all_nodes_referenced.extend(p)
                raw_context_for_llm.append({"step": step.operation, "call_chains_count": len(paths)})
                diagram = self.diagram_generator.generate_flow_diagram(paths)
                
            elif step.reasoner == ReasonerType.DEPENDENCY and "nodes" in res:
                nodes = res["nodes"]
                edges = res["edges"]
                all_nodes_referenced.extend(nodes)
                raw_context_for_llm.append({"step": step.operation, "dependencies_count": len(nodes)})
                diagram = self.diagram_generator.generate_dependency_diagram(nodes, edges)

            elif step.reasoner == ReasonerType.KNOWLEDGE and res.get("summary"):
                raw_context_for_llm.append({
                    "step": "Project Summary", 
                    "total_nodes_in_db": res.get("total_nodes"),
                    "services": [n.get('name') for n in res.get("services", [])],
                    "repositories": [n.get('name') for n in res.get("repositories", [])],
                    "domains": [n.get('name') for n in res.get("domains", [])]
                })

            elif step.reasoner == ReasonerType.KNOWLEDGE and "neighbors" in res:
                all_nodes_referenced.append(res.get("node", {}))
                all_nodes_referenced.extend(res.get("neighbors", []))
                raw_context_for_llm.append({"step": step.operation, "neighbors_count": len(res.get("neighbors", []))})

        # Synthesize using LLM if available
        if self.llm and self.llm.is_enabled():
            system_prompt = \"\"\"You are a senior software architect responding to a query about a codebase.
Analyze the Graph Results and output a structured JSON response matching this schema exactly:
{
  "heading": "A short summary title (string)",
  "text": "Detailed explanation answering the query (string)",
  "bullets": [{"label": "short label", "body": "description"}],
  "codeBlock": {"language": "cypher", "title": "Query or File", "code": "code content"} (optional),
  "relatedServices": ["ServiceA", "ServiceB"] (optional)
}
\"\"\"
            user_prompt = f"User Query: {plan.query}\nGraph Results: {json.dumps(raw_context_for_llm)}"
            narrative = self.llm.generate_json(system_prompt, user_prompt)
            
            heading = narrative.get("heading", "Query Results")
            text = narrative.get("text", "No detailed information found.")
            bullets = narrative.get("bullets", [])
            codeBlock = narrative.get("codeBlock")
            relatedServices = narrative.get("relatedServices", [])
        else:
            # Fallback
            heading = f"Query Plan Executed: {plan.intent.value}"
            text = "The LLM is currently disabled. Raw execution plan context follows:"
            bullets = [{"label": item.get("step", "Step"), "body": str(item)} for item in raw_context_for_llm]
            codeBlock = None
            relatedServices = []

        seen_ids = set()
        unique_nodes = []
        for n in all_nodes_referenced:
            if n and isinstance(n, dict) and "id" in n and n["id"] not in seen_ids:
                seen_ids.add(n["id"])
                unique_nodes.append(n)
                
        citations = self.citation_builder.build_citations(unique_nodes)
        
        # We can still pass the diagram as a code block if the LLM didn't provide one
        if diagram and not codeBlock:
            codeBlock = {"language": "mermaid", "title": "Architecture Flow", "code": diagram}
            
        return {
            "heading": heading,
            "text": text,
            "bullets": bullets,
            "codeBlock": codeBlock,
            "relatedServices": relatedServices
        }

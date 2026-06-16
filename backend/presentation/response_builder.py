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

        # Synthesize markdown using LLM if available
        if self.llm and self.llm.is_enabled():
            system_prompt = "You are a senior software architect. Summarize the graph traversal results into a beautiful, concise markdown narrative answering the user's query. The context provided is a summary of the operations performed on the graph database."
            user_prompt = f"User Query: {plan.query}\nGraph Results: {json.dumps(raw_context_for_llm)}\n\nPlease provide a short markdown response."
            narrative = self.llm.generate(system_prompt, user_prompt)
            if narrative:
                markdown = narrative
        else:
            # Fallback
            for item in raw_context_for_llm:
                markdown += f"- **{item['step']}**: {item}\n"

        seen_ids = set()
        unique_nodes = []
        for n in all_nodes_referenced:
            if n and isinstance(n, dict) and "id" in n and n["id"] not in seen_ids:
                seen_ids.add(n["id"])
                unique_nodes.append(n)
                
        citations = self.citation_builder.build_citations(unique_nodes)
        
        return {
            "query": plan.query,
            "intent": plan.intent.value,
            "markdown": markdown,
            "diagram": diagram,
            "citations": citations,
            "plan_steps": [s.model_dump() for s in plan.steps]
        }

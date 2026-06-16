import re
from backend.reasoning.planner import QueryIntent

class LLMIntentClassifier:
    """Classifies user query into a QueryIntent and extracts primary entities using an LLM."""
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.system_prompt = f"""
You are the query understanding module for CodeLens EKOS. 
Given a natural language software architecture question, classify it into one of these intents:
{[e.value for e in QueryIntent]}

Also, extract the primary 'entity' (the core class, service, or concept) the user is asking about.

Return a JSON object with this exact schema:
{{
    "intent": "...",
    "primary_entity": "..."
}}
If the intent doesn't clearly match, default to "explore".
If no specific entity is found, set "primary_entity" to null.
        """
        
    def classify_and_extract(self, query: str) -> dict:
        if not self.llm.is_enabled():
            # Fallback to general exploration if LLM is not configured
            return {"intent": QueryIntent.EXPLORE, "primary_entity": query}
            
        result = self.llm.generate_json(
            system_prompt=self.system_prompt,
            user_prompt=f"Question: {query}"
        )
        
        intent_str = result.get("intent", "explore")
        try:
            intent = QueryIntent(intent_str)
        except ValueError:
            intent = QueryIntent.EXPLORE
            
        return {
            "intent": intent,
            "primary_entity": result.get("primary_entity")
        }

class QueryEngine:
    """High-level orchestrator for Reasoning."""
    
    def __init__(self, model, entity_resolver, llm_client=None):
        from backend.reasoning.planner import QueryPlanner, ReasonerType
        from backend.reasoning.knowledge_traverser import KnowledgeTraverser
        from backend.reasoning.flow_reconstructor import FlowReconstructor
        from backend.reasoning.dependency_analyzer import DependencyAnalyzer
        from backend.presentation.response_builder import ResponseBuilder
        
        self.model = model
        self.entity_resolver = entity_resolver
        self.llm = llm_client
        self.classifier = LLMIntentClassifier(llm_client)
        self.planner = QueryPlanner()
        self.executors = {
            ReasonerType.KNOWLEDGE: KnowledgeTraverser(model),
            ReasonerType.FLOW: FlowReconstructor(model),
            ReasonerType.DEPENDENCY: DependencyAnalyzer(model),
        }
        self.response_builder = ResponseBuilder(llm_client)
        
    def execute_query(self, query: str):
        # 1. LLM Classify intent & extract primary entity
        classification = self.classifier.classify_and_extract(query)
        intent = classification["intent"]
        extracted_entity = classification["primary_entity"]
        
        # 2. Resolve entities against our Canonical Registry
        # Use the extracted entity if available, otherwise fallback to the raw query
        search_term = extracted_entity if extracted_entity else query
        entities = self.entity_resolver.resolve(search_term)
        
        # 3. Create plan
        plan = self.planner.plan(query, intent, entities)
        
        # 4. Execute plan
        results = {}
        for step in plan.steps:
            executor = self.executors.get(step.reasoner)
            if executor:
                step_inputs = dict(step.inputs)
                if "from_step" in step_inputs:
                    prev_step = step_inputs["from_step"]
                    if prev_step in results:
                        step_inputs["entity_id"] = results[prev_step].get("entity_id")
                        
                result = executor.execute(step_inputs)
                results[step.step_id] = result
        
        # 5. Build response
        return self.response_builder.build(plan, results)

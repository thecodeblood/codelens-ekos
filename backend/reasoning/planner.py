from enum import Enum
from pydantic import BaseModel

class ReasonerType(str, Enum):
    FLOW = "flow"
    DEPENDENCY = "dependency"
    IMPACT = "impact"
    KNOWLEDGE = "knowledge"
    ARCHITECTURE = "architecture"
    DECISION = "decision"

class QueryIntent(str, Enum):
    EXPLAIN_FLOW = "explain_flow"
    FIND_IMPL = "find_implementation"
    SHOW_DEPS = "show_dependencies"
    ASSESS_IMPACT = "assess_impact"
    SHOW_WORKFLOW = "show_workflow"
    EXPLAIN_DECISION = "explain_decision"
    SHOW_HISTORY = "show_history"
    SHOW_OWNERSHIP = "show_ownership"
    EXPLORE = "explore"
    UNKNOWN = "unknown"

class PlanStep(BaseModel):
    step_id: str
    reasoner: ReasonerType
    operation: str
    inputs: dict
    depends_on: list[str] = []

class QueryPlan(BaseModel):
    query: str
    intent: QueryIntent
    steps: list[PlanStep]

class QueryPlanner:
    """Creates a structured execution plan from a classified query intent and resolved entities."""
    
    def plan(self, query: str, intent: QueryIntent, entities: list) -> QueryPlan:
        steps = []
        
        if not entities:
            # If no entities resolved, perform a general project summary
            steps.append(PlanStep(
                step_id="s1",
                reasoner=ReasonerType.KNOWLEDGE,
                operation="explore",
                inputs={"query": query, "operation": "get_project_summary"}
            ))
            return QueryPlan(query=query, intent=QueryIntent.EXPLORE, steps=steps)
            
        primary_entity = entities[0]
        
        # Step 1: Always resolve the primary entity first in the plan
        steps.append(PlanStep(
            step_id="s1",
            reasoner=ReasonerType.KNOWLEDGE,
            operation="resolve_concept",
            inputs={"entity_id": primary_entity.node_id}
        ))
        
        if intent == QueryIntent.EXPLAIN_FLOW:
            steps.append(PlanStep(
                step_id="s2",
                reasoner=ReasonerType.FLOW,
                operation="get_call_chain",
                inputs={"from_step": "s1", "direction": "downstream"},
                depends_on=["s1"]
            ))
        elif intent == QueryIntent.SHOW_DEPS:
            steps.append(PlanStep(
                step_id="s2",
                reasoner=ReasonerType.DEPENDENCY,
                operation="get_dependencies",
                inputs={"from_step": "s1", "direction": "both"},
                depends_on=["s1"]
            ))
        elif intent == QueryIntent.ASSESS_IMPACT:
            steps.append(PlanStep(
                step_id="s2",
                reasoner=ReasonerType.IMPACT,
                operation="assess_impact",
                inputs={"from_step": "s1"},
                depends_on=["s1"]
            ))
        else:
            steps.append(PlanStep(
                step_id="s2",
                reasoner=ReasonerType.KNOWLEDGE,
                operation="explore",
                inputs={"from_step": "s1"},
                depends_on=["s1"]
            ))
            
        return QueryPlan(query=query, intent=intent, steps=steps)

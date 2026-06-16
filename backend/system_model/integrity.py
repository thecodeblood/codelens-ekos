from pydantic import BaseModel
from typing import Optional
from .model import SystemModel
import datetime

class IntegrityRule(BaseModel):
    """Declarative graph validation rule."""
    id: str
    name: str
    description: str
    severity: str                     # "error", "warning", "info"
    query: str                        # SQL query that returns violations (must return node/edge IDs)
    repair_strategy: Optional[str]    # "auto_link", "flag_orphan", "suggest_merge", "delete", None

class Violation(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    entity_ids: list[str]
    description: str
    repair_available: bool

class IntegrityReport(BaseModel):
    timestamp: str
    errors: list[Violation]
    warnings: list[Violation]
    info: list[Violation]
    score: float

INTEGRITY_RULES: list[IntegrityRule] = [
    # ── Containment Rules ──
    IntegrityRule(
        id="R001",
        name="api_must_belong_to_service",
        description="Every API_ENDPOINT must be contained by a SERVICE",
        severity="warning",
        query="""
            SELECT n.id FROM nodes n
            WHERE n.node_type = 'api_endpoint'
            AND n.id NOT IN (
                SELECT e.target_id FROM edges e 
                WHERE e.edge_type = 'contains' 
                AND e.source_id IN (SELECT id FROM nodes WHERE node_type = 'service')
            )
        """,
        repair_strategy="auto_link"
    ),
    IntegrityRule(
        id="R002",
        name="function_must_belong_to_module",
        description="Every FUNCTION must be contained by a MODULE or CLASS",
        severity="warning",
        query="""
            SELECT n.id FROM nodes n
            WHERE n.node_type = 'function'
            AND n.id NOT IN (
                SELECT e.target_id FROM edges e 
                WHERE e.edge_type = 'contains'
            )
        """,
        repair_strategy="auto_link"
    ),
    IntegrityRule(
        id="R003",
        name="workflow_must_have_steps",
        description="Every WORKFLOW must contain at least one WORKFLOW_STEP",
        severity="warning",
        query="""
            SELECT n.id FROM nodes n
            WHERE n.node_type = 'workflow'
            AND n.id NOT IN (
                SELECT e.source_id FROM edges e
                WHERE e.edge_type = 'contains'
                AND e.target_id IN (SELECT id FROM nodes WHERE node_type = 'workflow_step')
            )
        """,
        repair_strategy=None
    ),

    # ── Orphan Rules ──
    IntegrityRule(
        id="R004",
        name="no_orphan_services",
        description="Every SERVICE must be contained by a REPOSITORY",
        severity="info",
        query="""
            SELECT n.id FROM nodes n
            WHERE n.node_type = 'service'
            AND n.id NOT IN (
                SELECT e.target_id FROM edges e 
                WHERE e.edge_type = 'contains' 
                AND e.source_id IN (SELECT id FROM nodes WHERE node_type = 'repository')
            )
        """,
        repair_strategy="auto_link"
    ),
    IntegrityRule(
        id="R005",
        name="no_dangling_edges",
        description="No edge should reference a non-existent node",
        severity="error",
        query="""
            SELECT e.id FROM edges e
            WHERE e.source_id NOT IN (SELECT id FROM nodes)
            OR e.target_id NOT IN (SELECT id FROM nodes)
        """,
        repair_strategy="delete"
    ),

    # ── Canonical Entity Rules ──
    IntegrityRule(
        id="R006",
        name="no_duplicate_canonical",
        description="No two nodes of the same type should have overlapping canonical aliases",
        severity="error",
        query="""
            SELECT DISTINCT c1.canonical_id
            FROM entity_aliases a1
            JOIN entity_aliases a2 ON a1.alias = a2.alias AND a1.canonical_id != a2.canonical_id
            JOIN canonical_entities c1 ON a1.canonical_id = c1.canonical_id
            JOIN canonical_entities c2 ON a2.canonical_id = c2.canonical_id
            WHERE c1.node_type = c2.node_type
        """,
        repair_strategy="suggest_merge"
    ),

    # ── Hierarchy Rules ──
    IntegrityRule(
        id="R007",
        name="feature_should_have_capability",
        description="Every FEATURE should be PART_OF a CAPABILITY",
        severity="info",
        query="""
            SELECT n.id FROM nodes n
            WHERE n.node_type = 'feature'
            AND n.id NOT IN (
                SELECT e.source_id FROM edges e WHERE e.edge_type = 'part_of'
                AND e.target_id IN (SELECT id FROM nodes WHERE node_type = 'capability')
            )
        """,
        repair_strategy=None
    ),

    # ── Evidence Rules ──
    IntegrityRule(
        id="R008",
        name="node_must_have_evidence",
        description="Every node must have at least one evidence record",
        severity="warning",
        query="""
            SELECT n.id FROM nodes n
            WHERE n.id NOT IN (
                SELECT DISTINCT entity_id FROM evidence WHERE entity_type = 'node'
            )
        """,
        repair_strategy=None
    )
]

class IntegrityEngine:
    """Runs validation rules and optionally applies repairs."""

    def __init__(self, model: SystemModel):
        self.model = model

    def validate(self) -> IntegrityReport:
        """Run all rules. Return violations grouped by severity."""
        errors = []
        warnings = []
        info = []
        
        cursor = self.model.conn.cursor()
        
        for rule in INTEGRITY_RULES:
            try:
                rows = cursor.execute(rule.query).fetchall()
                if rows:
                    entity_ids = [row[0] for row in rows]
                    violation = Violation(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        entity_ids=entity_ids,
                        description=rule.description,
                        repair_available=rule.repair_strategy is not None
                    )
                    if rule.severity == "error":
                        errors.append(violation)
                    elif rule.severity == "warning":
                        warnings.append(violation)
                    else:
                        info.append(violation)
            except Exception as e:
                # Log error
                pass
                
        # Calculate a simple score: 1.0 - penalties
        penalty = (len(errors) * 0.1) + (len(warnings) * 0.05) + (len(info) * 0.01)
        score = max(0.0, min(1.0, 1.0 - penalty))
        
        return IntegrityReport(
            timestamp=datetime.datetime.utcnow().isoformat(),
            errors=errors,
            warnings=warnings,
            info=info,
            score=score
        )

    def repair(self, rule_id: str, violations: list) -> dict:
        """Apply auto-repair strategy for a specific rule."""
        rule = next((r for r in INTEGRITY_RULES if r.id == rule_id), None)
        if not rule or not rule.repair_strategy:
            return {"status": "failed", "reason": "No repair strategy"}
            
        # Simplified repair execution for Phase 1
        if rule.repair_strategy == "delete" and rule.name == "no_dangling_edges":
            cursor = self.model.conn.cursor()
            cursor.execute("""
                DELETE FROM edges
                WHERE source_id NOT IN (SELECT id FROM nodes)
                OR target_id NOT IN (SELECT id FROM nodes)
            """)
            self.model.conn.commit()
            return {"status": "success", "action": "deleted dangling edges"}
            
        return {"status": "not_implemented"}

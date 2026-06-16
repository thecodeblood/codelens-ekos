from pydantic import BaseModel
from typing import Optional, List
from ..system_model.nodes import NodeType
from ..system_model.edges import EdgeType

class ExtractedEntity(BaseModel):
    name: str
    qualified_name: str
    entity_type: NodeType
    properties: dict
    source_file: str
    line_start: Optional[int]
    line_end: Optional[int]
    confidence: float
    extraction_method: str

class ExtractedRelationship(BaseModel):
    source_qualified_name: str
    target_qualified_name: str
    relationship_type: EdgeType
    properties: dict
    confidence: float
    extraction_method: str
    source_file: str

class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]
    source_file: str
    extraction_method: str

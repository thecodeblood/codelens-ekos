import logging
import json
from typing import List, Dict, Any
from ..models import ExtractedEntity, ExtractedRelationship, ExtractionResult
from ...system_model.nodes import NodeType
from ...system_model.edges import EdgeType
from ..llm import LLMClient
from ...config import Settings

logger = logging.getLogger(__name__)

class DocExtractor:
    """Uses an LLM to extract architectural entities and relationships from raw text/documentation."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def extract(self, text: str, source_uri: str) -> ExtractionResult:
        if not self.llm.is_enabled():
            logger.warning("LLM not enabled. DocExtractor will return empty results.")
            return ExtractionResult(entities=[], relationships=[], source_file=source_uri, extraction_method="llm")

        system_prompt = """
You are an expert software architect. Analyze the following project documentation and extract the core architectural entities and their relationships.
You must extract high-level entities such as:
- domain
- capability
- feature
- service
- workflow

For each entity, provide:
- name: (e.g. "Payment Gateway")
- type: (must be one of: domain, capability, feature, service, workflow, repository)
- description: A short description of its purpose.

For each relationship, provide:
- source: name of the entity
- target: name of the entity
- type: (must be one of: contains, part_of, calls, exposes, depends_on, implements, describes)

Respond ONLY with valid JSON in this format:
{
  "entities": [
    {"name": "...", "type": "...", "description": "..."}
  ],
  "relationships": [
    {"source": "...", "target": "...", "type": "..."}
  ]
}
"""
        
        # Limit text length to avoid token limits. For MVP, we take first ~15,000 characters
        truncated_text = text[:15000]
        
        try:
            logger.info(f"Extracting knowledge from document: {source_uri}")
            llm_result = self.llm.generate_json(system_prompt, f"Extract architecture from this document:\n\n{truncated_text}")
        except Exception as e:
            logger.error(f"Failed to extract from document using LLM: {e}")
            llm_result = {"entities": [], "relationships": []}

        extracted_entities = []
        extracted_relationships = []

        raw_entities = llm_result.get("entities", [])
        raw_rels = llm_result.get("relationships", [])

        # Create a mapping of name to qualified name (which we'll just normalize)
        name_map = {}
        for ent in raw_entities:
            name = ent.get("name", "")
            if not name:
                continue
            
            ent_type_str = ent.get("type", "").lower()
            try:
                node_type = NodeType(ent_type_str)
            except ValueError:
                # Fallback
                node_type = NodeType.FEATURE

            q_name = name.lower().replace(" ", "_").replace("-", "_")
            name_map[name] = q_name
            
            extracted_entities.append(ExtractedEntity(
                name=name,
                qualified_name=q_name,
                entity_type=node_type,
                properties={"description": ent.get("description", "")},
                source_file=source_uri,
                line_start=None,
                line_end=None,
                confidence=0.8,
                extraction_method="llm"
            ))

        for rel in raw_rels:
            src = rel.get("source", "")
            tgt = rel.get("target", "")
            rel_type_str = rel.get("type", "").lower()
            
            if src not in name_map or tgt not in name_map:
                continue
                
            try:
                edge_type = EdgeType(rel_type_str)
            except ValueError:
                edge_type = EdgeType.DEPENDS_ON
                
            extracted_relationships.append(ExtractedRelationship(
                source_qualified_name=name_map[src],
                target_qualified_name=name_map[tgt],
                relationship_type=edge_type,
                properties={},
                confidence=0.8,
                extraction_method="llm",
                source_file=source_uri
            ))

        return ExtractionResult(
            entities=extracted_entities,
            relationships=extracted_relationships,
            source_file=source_uri,
            extraction_method="llm"
        )

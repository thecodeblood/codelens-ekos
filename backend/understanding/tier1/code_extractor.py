from typing import List
from ...parsing.ast_queries.python import PythonExtractionResult
from ..models import ExtractionResult, ExtractedEntity, ExtractedRelationship
from ...system_model.nodes import NodeType
from ...system_model.edges import EdgeType

class CodeEntityExtractor:
    """Extracts System Model entities and relationships from parsed AST results."""
    
    def extract(self, ast_result: PythonExtractionResult) -> ExtractionResult:
        entities = []
        relationships = []
        source = ast_result.file_path
        
        # 1. Module
        module_name = ast_result.module_name
        entities.append(ExtractedEntity(
            name=module_name.split('.')[-1],
            qualified_name=module_name,
            entity_type=NodeType.MODULE,
            properties={"docstring": ast_result.module_docstring},
            source_file=source,
            line_start=1,
            line_end=None,
            confidence=1.0,
            extraction_method="ast"
        ))
        
        # 2. Classes
        for cls in ast_result.classes:
            entities.append(ExtractedEntity(
                name=cls.name,
                qualified_name=cls.qualified_name,
                entity_type=NodeType.CLASS,
                properties={
                    "is_dataclass": cls.is_dataclass,
                    "decorators": cls.decorators,
                    "docstring": cls.docstring,
                    "bases": cls.bases
                },
                source_file=source,
                line_start=cls.line_start,
                line_end=cls.line_end,
                confidence=1.0,
                extraction_method="ast"
            ))
            # Module contains Class
            relationships.append(ExtractedRelationship(
                source_qualified_name=module_name,
                target_qualified_name=cls.qualified_name,
                relationship_type=EdgeType.CONTAINS,
                properties={},
                confidence=1.0,
                extraction_method="ast",
                source_file=source
            ))
            
            # 3. Methods inside classes
            for method in cls.methods:
                entities.append(ExtractedEntity(
                    name=method.name,
                    qualified_name=method.qualified_name,
                    entity_type=NodeType.FUNCTION,
                    properties={
                        "is_async": method.is_async,
                        "is_method": True,
                        "is_static": method.is_static,
                        "is_classmethod": method.is_classmethod,
                        "is_property": method.is_property,
                        "decorators": method.decorators,
                        "docstring": method.docstring,
                        "return_type": method.return_type
                    },
                    source_file=source,
                    line_start=method.line_start,
                    line_end=method.line_end,
                    confidence=1.0,
                    extraction_method="ast"
                ))
                # Class contains Method
                relationships.append(ExtractedRelationship(
                    source_qualified_name=cls.qualified_name,
                    target_qualified_name=method.qualified_name,
                    relationship_type=EdgeType.CONTAINS,
                    properties={},
                    confidence=1.0,
                    extraction_method="ast",
                    source_file=source
                ))
                
                # Calls from methods
                for call in method.calls:
                    relationships.append(ExtractedRelationship(
                        source_qualified_name=method.qualified_name,
                        target_qualified_name=call.function_name, # Note: this might be unresolvable if external or dynamic
                        relationship_type=EdgeType.CALLS,
                        properties={"line": call.line},
                        confidence=0.8, # Lower confidence for dynamic calls
                        extraction_method="ast",
                        source_file=source
                    ))

        # 4. Top-level functions
        for func in ast_result.functions:
            entities.append(ExtractedEntity(
                name=func.name,
                qualified_name=func.qualified_name,
                entity_type=NodeType.FUNCTION,
                properties={
                    "is_async": func.is_async,
                    "is_method": False,
                    "is_static": False,
                    "is_classmethod": False,
                    "is_property": False,
                    "decorators": func.decorators,
                    "docstring": func.docstring,
                    "return_type": func.return_type
                },
                source_file=source,
                line_start=func.line_start,
                line_end=func.line_end,
                confidence=1.0,
                extraction_method="ast"
            ))
            # Module contains Function
            relationships.append(ExtractedRelationship(
                source_qualified_name=module_name,
                target_qualified_name=func.qualified_name,
                relationship_type=EdgeType.CONTAINS,
                properties={},
                confidence=1.0,
                extraction_method="ast",
                source_file=source
            ))
            
            # Calls from functions
            for call in func.calls:
                relationships.append(ExtractedRelationship(
                    source_qualified_name=func.qualified_name,
                    target_qualified_name=call.function_name,
                    relationship_type=EdgeType.CALLS,
                    properties={"line": call.line},
                    confidence=0.8,
                    extraction_method="ast",
                    source_file=source
                ))
                
        # 5. Imports
        for imp in ast_result.imports:
            # We don't necessarily create an entity for the imported module if it's not our code,
            # but we create an IMPORTS relationship.
            relationships.append(ExtractedRelationship(
                source_qualified_name=module_name,
                target_qualified_name=imp.module,
                relationship_type=EdgeType.IMPORTS,
                properties={"names": imp.names, "is_from": imp.is_from, "line": imp.line},
                confidence=1.0,
                extraction_method="ast",
                source_file=source
            ))

        # 6. API Endpoints
        for endpoint in ast_result.endpoints:
            endpoint_qn = f"{endpoint.method} {endpoint.path}"
            entities.append(ExtractedEntity(
                name=endpoint.path,
                qualified_name=endpoint_qn,
                entity_type=NodeType.API_ENDPOINT,
                properties={"method": endpoint.method, "path": endpoint.path},
                source_file=source,
                line_start=endpoint.line,
                line_end=endpoint.line,
                confidence=1.0,
                extraction_method="ast"
            ))
            # Function EXPOSES API_ENDPOINT
            relationships.append(ExtractedRelationship(
                source_qualified_name=endpoint.handler_function,
                target_qualified_name=endpoint_qn,
                relationship_type=EdgeType.EXPOSES,
                properties={},
                confidence=1.0,
                extraction_method="ast",
                source_file=source
            ))

        # 7. Data Models
        for dm in ast_result.data_models:
            # Extract DataModel entity
            entities.append(ExtractedEntity(
                name=dm.table_name or dm.class_name,
                qualified_name=f"table:{dm.table_name or dm.class_name}",
                entity_type=NodeType.DATA_MODEL,
                properties={"fields": dm.fields, "framework": dm.framework},
                source_file=source,
                line_start=dm.line_start,
                line_end=dm.line_end,
                confidence=1.0,
                extraction_method="ast"
            ))
            
            # Assuming dm is linked to the class
            class_qn = f"{module_name}.{dm.class_name}"
            # A data model class reads/writes or implements the DATA_MODEL.
            # In EKOS, we can say Class IMPLEMENTS DataModel or just store it.
            relationships.append(ExtractedRelationship(
                source_qualified_name=class_qn,
                target_qualified_name=f"table:{dm.table_name or dm.class_name}",
                relationship_type=EdgeType.IMPLEMENTS,
                properties={},
                confidence=1.0,
                extraction_method="ast",
                source_file=source
            ))

        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            source_file=source,
            extraction_method="ast"
        )

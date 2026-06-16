"""Node type ontology and property models for the System Model.

Defines the complete taxonomy of entity types that can exist in the knowledge
graph, along with their typed property schemas and extraction metadata.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core Enums
# ---------------------------------------------------------------------------


class NodeType(str, Enum):
    """Complete taxonomy of node types in the System Model.

    Organised into five conceptual layers that span from business-level
    concepts down to operational concerns.
    """

    # Concept Layer
    DOMAIN = "domain"
    CAPABILITY = "capability"
    FEATURE = "feature"

    # Architecture Layer
    WORKFLOW = "workflow"
    WORKFLOW_STEP = "workflow_step"
    ADR = "adr"
    RFC = "rfc"
    DECISION = "decision"
    TECHNOLOGY = "technology"

    # Code Layer
    REPOSITORY = "repository"
    SERVICE = "service"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    API_ENDPOINT = "api_endpoint"
    DATA_MODEL = "data_model"
    EVENT = "event"
    EXTERNAL_DEP = "external_dep"

    # Document Layer
    DOCUMENT = "document"
    SECTION = "section"

    # Operational Layer
    AUTHOR = "author"
    TEAM = "team"


class ExtractionMethod(str, Enum):
    """How an entity or relationship was discovered."""

    AST = "ast"
    REGEX = "regex"
    NER = "ner"
    HEURISTIC = "heuristic"
    GIT = "git"
    LLM = "llm"
    MANUAL = "manual"


class NodeCategory(str, Enum):
    """High-level categorisation used for filtering and display."""

    CODE = "code"
    KNOWLEDGE = "knowledge"
    OPERATIONAL = "operational"


# Mapping from NodeType → NodeCategory for quick look-ups.
NODE_CATEGORY_MAP: dict[NodeType, NodeCategory] = {
    # Concept Layer → KNOWLEDGE
    NodeType.DOMAIN: NodeCategory.KNOWLEDGE,
    NodeType.CAPABILITY: NodeCategory.KNOWLEDGE,
    NodeType.FEATURE: NodeCategory.KNOWLEDGE,
    # Architecture Layer → KNOWLEDGE
    NodeType.WORKFLOW: NodeCategory.KNOWLEDGE,
    NodeType.WORKFLOW_STEP: NodeCategory.KNOWLEDGE,
    NodeType.ADR: NodeCategory.KNOWLEDGE,
    NodeType.RFC: NodeCategory.KNOWLEDGE,
    NodeType.DECISION: NodeCategory.KNOWLEDGE,
    NodeType.TECHNOLOGY: NodeCategory.KNOWLEDGE,
    # Code Layer → CODE
    NodeType.REPOSITORY: NodeCategory.CODE,
    NodeType.SERVICE: NodeCategory.CODE,
    NodeType.MODULE: NodeCategory.CODE,
    NodeType.CLASS: NodeCategory.CODE,
    NodeType.FUNCTION: NodeCategory.CODE,
    NodeType.API_ENDPOINT: NodeCategory.CODE,
    NodeType.DATA_MODEL: NodeCategory.CODE,
    NodeType.EVENT: NodeCategory.CODE,
    NodeType.EXTERNAL_DEP: NodeCategory.CODE,
    # Document Layer → KNOWLEDGE
    NodeType.DOCUMENT: NodeCategory.KNOWLEDGE,
    NodeType.SECTION: NodeCategory.KNOWLEDGE,
    # Operational Layer → OPERATIONAL
    NodeType.AUTHOR: NodeCategory.OPERATIONAL,
    NodeType.TEAM: NodeCategory.OPERATIONAL,
}


# ---------------------------------------------------------------------------
# Typed Property Models
# ---------------------------------------------------------------------------


class FunctionProperties(BaseModel):
    """Properties specific to FUNCTION nodes."""

    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    signature: Optional[str] = None
    return_type: Optional[str] = None
    parameters: list[dict[str, str]] = Field(default_factory=list)
    is_async: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    complexity: Optional[int] = None
    decorators: list[str] = Field(default_factory=list)
    docstring: Optional[str] = None
    language: Optional[str] = None


class ClassProperties(BaseModel):
    """Properties specific to CLASS nodes."""

    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    bases: list[str] = Field(default_factory=list)
    is_abstract: bool = False
    is_dataclass: bool = False
    is_pydantic: bool = False
    decorators: list[str] = Field(default_factory=list)
    docstring: Optional[str] = None
    method_count: Optional[int] = None
    language: Optional[str] = None


class ModuleProperties(BaseModel):
    """Properties specific to MODULE nodes."""

    file_path: Optional[str] = None
    language: Optional[str] = None
    line_count: Optional[int] = None
    import_count: Optional[int] = None
    class_count: Optional[int] = None
    function_count: Optional[int] = None
    docstring: Optional[str] = None


class ServiceProperties(BaseModel):
    """Properties specific to SERVICE nodes."""

    language: Optional[str] = None
    framework: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    repository: Optional[str] = None
    health_check_url: Optional[str] = None
    api_prefix: Optional[str] = None
    version: Optional[str] = None


class ConceptProperties(BaseModel):
    """Properties for DOMAIN, CAPABILITY, and FEATURE nodes."""

    definition: Optional[str] = None
    examples: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    status: Optional[str] = None
    priority: Optional[str] = None
    source_document: Optional[str] = None


class DecisionProperties(BaseModel):
    """Properties for ADR, RFC, and DECISION nodes."""

    status: Optional[str] = None  # proposed, accepted, deprecated, superseded
    date: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    context: Optional[str] = None
    decision_text: Optional[str] = None
    consequences: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    source_uri: Optional[str] = None


class WorkflowProperties(BaseModel):
    """Properties for WORKFLOW and WORKFLOW_STEP nodes."""

    trigger: Optional[str] = None
    step_order: Optional[int] = None
    is_conditional: bool = False
    condition: Optional[str] = None
    timeout: Optional[str] = None
    retry_policy: Optional[str] = None
    actors: list[str] = Field(default_factory=list)


class DocumentProperties(BaseModel):
    """Properties for DOCUMENT and SECTION nodes."""

    file_path: Optional[str] = None
    format: Optional[str] = None  # markdown, rst, html, pdf
    title: Optional[str] = None
    section_level: Optional[int] = None
    word_count: Optional[int] = None
    last_modified: Optional[str] = None
    authors: list[str] = Field(default_factory=list)


class APIEndpointProperties(BaseModel):
    """Properties specific to API_ENDPOINT nodes."""

    http_method: Optional[str] = None
    path: Optional[str] = None
    request_body_schema: Optional[str] = None
    response_schema: Optional[str] = None
    status_codes: list[int] = Field(default_factory=list)
    auth_required: bool = False
    rate_limited: bool = False
    version: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class DataModelProperties(BaseModel):
    """Properties specific to DATA_MODEL nodes."""

    file_path: Optional[str] = None
    fields: list[dict[str, str]] = Field(default_factory=list)
    primary_key: Optional[str] = None
    table_name: Optional[str] = None
    orm_type: Optional[str] = None  # sqlalchemy, django, pydantic
    is_abstract: bool = False
    language: Optional[str] = None


class EventProperties(BaseModel):
    """Properties specific to EVENT nodes."""

    topic: Optional[str] = None
    payload_schema: Optional[str] = None
    broker: Optional[str] = None  # kafka, rabbitmq, sqs, etc.
    is_async: bool = True
    retention: Optional[str] = None


class AuthorProperties(BaseModel):
    """Properties for AUTHOR and TEAM nodes."""

    email: Optional[str] = None
    git_handle: Optional[str] = None
    github_username: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    active: bool = True


class TechnologyProperties(BaseModel):
    """Properties specific to TECHNOLOGY nodes."""

    version: Optional[str] = None
    category: Optional[str] = None  # language, framework, database, tool
    website: Optional[str] = None
    license: Optional[str] = None


class RepositoryProperties(BaseModel):
    """Properties specific to REPOSITORY nodes."""

    url: Optional[str] = None
    default_branch: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    last_commit: Optional[str] = None


class ExternalDepProperties(BaseModel):
    """Properties specific to EXTERNAL_DEP nodes."""

    package_name: Optional[str] = None
    version_constraint: Optional[str] = None
    registry: Optional[str] = None  # pypi, npm, maven, etc.
    is_dev_dependency: bool = False


# ---------------------------------------------------------------------------
# Property Registry
# ---------------------------------------------------------------------------

# Maps each NodeType to its specialised properties model. Types without a
# dedicated model fall back to a plain dict.
PropertiesType = Union[
    FunctionProperties,
    ClassProperties,
    ModuleProperties,
    ServiceProperties,
    ConceptProperties,
    DecisionProperties,
    WorkflowProperties,
    DocumentProperties,
    APIEndpointProperties,
    DataModelProperties,
    EventProperties,
    AuthorProperties,
    TechnologyProperties,
    RepositoryProperties,
    ExternalDepProperties,
    dict[str, Any],
]

NODE_PROPERTIES_REGISTRY: dict[NodeType, type[BaseModel]] = {
    NodeType.FUNCTION: FunctionProperties,
    NodeType.CLASS: ClassProperties,
    NodeType.MODULE: ModuleProperties,
    NodeType.SERVICE: ServiceProperties,
    NodeType.DOMAIN: ConceptProperties,
    NodeType.CAPABILITY: ConceptProperties,
    NodeType.FEATURE: ConceptProperties,
    NodeType.ADR: DecisionProperties,
    NodeType.RFC: DecisionProperties,
    NodeType.DECISION: DecisionProperties,
    NodeType.WORKFLOW: WorkflowProperties,
    NodeType.WORKFLOW_STEP: WorkflowProperties,
    NodeType.DOCUMENT: DocumentProperties,
    NodeType.SECTION: DocumentProperties,
    NodeType.API_ENDPOINT: APIEndpointProperties,
    NodeType.DATA_MODEL: DataModelProperties,
    NodeType.EVENT: EventProperties,
    NodeType.AUTHOR: AuthorProperties,
    NodeType.TEAM: AuthorProperties,
    NodeType.TECHNOLOGY: TechnologyProperties,
    NodeType.REPOSITORY: RepositoryProperties,
    NodeType.EXTERNAL_DEP: ExternalDepProperties,
}


# ---------------------------------------------------------------------------
# SystemNode — the core node model
# ---------------------------------------------------------------------------


class SystemNode(BaseModel):
    """A single node in the System Model knowledge graph.

    Every entity discovered during ingestion is represented as a SystemNode.
    The ``properties`` field is typed according to the ``NODE_PROPERTIES_REGISTRY``
    for the given ``node_type``, but falls back to a plain dict for unknown types.
    """

    id: str = Field(..., description="Unique identifier (typically a UUID or qualified name hash).")
    node_type: NodeType = Field(..., description="Ontology type of this node.")
    name: str = Field(..., description="Human-readable short name.")
    qualified_name: Optional[str] = Field(
        default=None,
        description="Fully qualified name (e.g. 'backend.system_model.nodes.SystemNode').",
    )
    description: Optional[str] = Field(default=None, description="Free-text description.")
    properties: PropertiesType = Field(
        default_factory=dict,
        description="Type-specific properties; see NODE_PROPERTIES_REGISTRY.",
    )
    tags: list[str] = Field(default_factory=list, description="User-supplied or inferred labels.")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score [0..1].",
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.MANUAL,
        description="How this node was extracted.",
    )
    first_seen_run: Optional[str] = Field(
        default=None,
        description="Ingestion run ID that first created this node.",
    )
    last_updated_run: Optional[str] = Field(
        default=None,
        description="Ingestion run ID that last modified this node.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def properties_dict(self) -> dict[str, Any]:
        """Return properties as a plain dict regardless of underlying type."""
        if isinstance(self.properties, BaseModel):
            return self.properties.model_dump()
        return dict(self.properties)

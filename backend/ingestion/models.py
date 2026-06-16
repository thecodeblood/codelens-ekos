from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Dict

class SourceType(str, Enum):
    GIT = "git"
    PDF = "pdf"
    MARKDOWN = "markdown"
    WEB = "web"
    DOCX = "docx"

class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    UNKNOWN = "unknown"

class ParsedCodeFile(BaseModel):
    id: str
    path: str
    repository: str
    language: Language
    content_hash: str
    raw_source: str
    # Store extraction results here temporarily before sending to code_extractor
    tree_sitter_ast: Optional[str] = None # Or bytes, depending on wrapper

class ParsedSection(BaseModel):
    id: str
    title: str
    level: int
    content: str
    parent_id: Optional[str]
    order: int

class DocumentMetadata(BaseModel):
    author: Optional[str]
    version: Optional[str]
    created_at: Optional[str]
    last_modified: Optional[str]
    tags: List[str] = []

class ParsedDocument(BaseModel):
    id: str
    title: str
    source_type: SourceType
    source_uri: str
    sections: List[ParsedSection]
    metadata: DocumentMetadata
    content_hash: str
    raw_text: str

class GitMetadata(BaseModel):
    repository: str
    branch: str
    last_commit_sha: str
    file_authors: Dict[str, str]
    file_change_counts: Dict[str, int]

class RunStats(BaseModel):
    files_total: int = 0
    files_processed: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    entities_extracted: int = 0
    relationships_extracted: int = 0

class IngestionRun(BaseModel):
    id: str
    source_id: str
    source_type: str
    source_uri: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    stats: RunStats = RunStats()

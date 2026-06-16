import hashlib
import os
from .base import BaseParser
from ..models import ParsedCodeFile, Language
from ...parsing.tree_sitter_wrapper import TreeSitterWrapper
from ...parsing.ast_queries.python import PythonASTExtractor

class CodeParser(BaseParser):
    def __init__(self):
        self.ts_wrapper = TreeSitterWrapper()
        self.python_extractor = PythonASTExtractor()

    def can_parse(self, file_path: str) -> bool:
        return file_path.endswith('.py')

    def parse(self, file_path: str, repository: str = None) -> ParsedCodeFile:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Determine language
        language = Language.UNKNOWN
        if file_path.endswith('.py'):
            language = Language.PYTHON
            
        # We don't parse the tree here, we just store the raw source.
        # Tree parsing will happen in the extraction phase, or we can do it here and store it.
        # For simplicity, we just return the ParsedCodeFile.
        return ParsedCodeFile(
            id=file_path,
            path=file_path,
            repository=repository or "unknown",
            language=language,
            content_hash=content_hash,
            raw_source=content
        )

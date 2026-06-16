from abc import ABC, abstractmethod
from typing import Union
from ..models import ParsedCodeFile, ParsedDocument

class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        pass
        
    @abstractmethod  
    def parse(self, file_path: str, repository: str = None) -> Union[ParsedCodeFile, ParsedDocument]:
        pass

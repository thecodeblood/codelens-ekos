from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from backend.api.routes.model import _get_model
from backend.system_model.canonical import CanonicalEntityRegistry
from backend.system_model.entity_resolver import EntityResolver
from backend.reasoning.engine import QueryEngine
from backend.understanding.llm import LLMClient

router = APIRouter(prefix="/api/v1/query", tags=["Query & Reasoning"])

class QueryRequest(BaseModel):
    query: str

class Bullet(BaseModel):
    label: str
    body: str

class CodeBlock(BaseModel):
    language: str
    title: str
    code: str

class QueryResponse(BaseModel):
    heading: str
    text: str
    bullets: list[Bullet] | None = None
    codeBlock: CodeBlock | None = None
    relatedServices: list[str] | None = None

def get_query_engine(request: Request, model=Depends(_get_model)):
    registry = CanonicalEntityRegistry(model.conn)
    resolver = EntityResolver(model, registry)
    
    settings = request.app.state.settings
    llm_client = LLMClient(settings)
    
    return QueryEngine(model, resolver, llm_client)

@router.post("", response_model=QueryResponse)
def execute_query(req: QueryRequest, engine: QueryEngine = Depends(get_query_engine)):
    result = engine.execute_query(req.query)
    return QueryResponse(**result)

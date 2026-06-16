from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sqlite3

from .config import Settings
from .system_model.model import SystemModel
from .system_model.canonical import CanonicalEntityRegistry
from .evidence.tracker import EvidenceTracker
from .system_model.schema import create_schema
from .ingestion.coordinator import PipelineCoordinator
from .ingestion.change_detector import ChangeDetector
from .system_model.builder import ModelBuilder

from .api.routes import model, sources, quality, query

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = Settings()
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    
    # Initialize Core Components
    system_model = SystemModel(settings.db_path)
    registry = CanonicalEntityRegistry(system_model.conn)
    evidence_tracker = EvidenceTracker(system_model.conn)
    
    # Initialize LLM Client
    from .understanding.llm import LLMClient
    llm_client = LLMClient(settings)
    
    # Initialize Ingestion Components
    model_builder = ModelBuilder(system_model, registry, evidence_tracker)
    change_detector = ChangeDetector(system_model.conn)
    coordinator = PipelineCoordinator(system_model, model_builder, change_detector, llm_client)
    
    # Add to app state
    app.state.settings = settings
    app.state.model = system_model
    app.state.registry = registry
    app.state.tracker = evidence_tracker
    app.state.coordinator = coordinator
    
    yield
    
    # Shutdown
    system_model.close()

app = FastAPI(
    title="CodeLens EKOS",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefix is already defined in the routers themselves, so we do not pass it here
app.include_router(model.router)
app.include_router(sources.router)
app.include_router(quality.router)
app.include_router(query.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to CodeLens EKOS API"}

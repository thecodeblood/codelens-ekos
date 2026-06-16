import os
import uuid
import datetime
import traceback
from typing import Optional
from .parsers.code_parser import CodeParser
from .parsers.git_metadata import GitMetadataParser
from .change_detector import ChangeDetector
from ..understanding.tier1.code_extractor import CodeEntityExtractor
from ..system_model.model import SystemModel
from ..system_model.builder import ModelBuilder
from .models import IngestionRun, RunStats

class PipelineCoordinator:
    """Manages ingestion runs with tracking, resume, and idempotency."""
    
    def __init__(self, model: SystemModel, builder: ModelBuilder, change_detector: ChangeDetector):
        self.model = model
        self.builder = builder
        self.change_detector = change_detector
        self.code_parser = CodeParser()
        self.git_parser = GitMetadataParser()
        self.code_extractor = CodeEntityExtractor()

    def ingest_repository(self, repo_path: str, source_id: str) -> IngestionRun:
        run_id = str(uuid.uuid4())
        started_at = datetime.datetime.utcnow().isoformat()
        
        run = IngestionRun(
            id=run_id,
            source_id=source_id,
            source_type="git",
            source_uri=repo_path,
            status="running",
            started_at=started_at
        )
        
        stats = RunStats()
        
        # 1. Record Run start in DB
        cursor = self.model._conn.cursor()
        cursor.execute('''
            INSERT INTO ingestion_runs (id, source_id, status, started_at)
            VALUES (?, ?, ?, ?)
        ''', (run.id, run.source_id, run.status, run.started_at))
        self.model._conn.commit()
        
        try:
            # Git extraction (optional for now, but useful to have)
            git_meta = self.git_parser.parse(repo_path)
            
            # Walk files
            for root, _, files in os.walk(repo_path):
                # Simple ignore strategy for MVP
                if '.git' in root or 'venv' in root or '__pycache__' in root:
                    continue
                    
                for file in files:
                    if not file.endswith('.py'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    stats.files_total += 1
                    
                    try:
                        # 2. Check changes
                        content_hash = self.change_detector.compute_hash(file_path)
                        if not self.change_detector.has_changed(source_id, file_path, content_hash):
                            stats.files_skipped += 1
                            continue
                            
                        # 3. Parse Code
                        parsed_file = self.code_parser.parse(file_path, git_meta.repository)
                        
                        # We need the AST. CodeParser gives raw_source, we need to parse it for extractor
                        tree = self.code_parser.ts_wrapper.parse(parsed_file.raw_source)
                        
                        # 4. Extract Entities
                        ast_result = self.code_parser.python_extractor.extract_all(tree, parsed_file.raw_source, file_path)
                        extraction_result = self.code_extractor.extract(ast_result)
                        
                        # 5. Build Model
                        build_result = self.builder.build_from_extraction(extraction_result, run_id)
                        
                        # Update stats
                        stats.entities_extracted += build_result.nodes_created + build_result.nodes_updated
                        stats.relationships_extracted += build_result.edges_created + build_result.edges_updated
                        stats.files_processed += 1
                        
                        # Store hash to mark as processed
                        self.change_detector.store_hash(source_id, file_path, content_hash, datetime.datetime.utcnow().isoformat())
                        
                    except Exception as e:
                        # Log error and continue
                        stats.files_failed += 1
                        print(f"Error processing {file_path}: {e}")
                        traceback.print_exc()

            # Mark Run complete
            run.status = "completed"
            run.completed_at = datetime.datetime.utcnow().isoformat()
            run.stats = stats
            
            cursor.execute('''
                UPDATE ingestion_runs 
                SET status = ?, completed_at = ?, files_total = ?, files_processed = ?, 
                    files_failed = ?, entities_extracted = ?, relationships_extracted = ?
                WHERE id = ?
            ''', (
                run.status, run.completed_at, stats.files_total, stats.files_processed, 
                stats.files_failed, stats.entities_extracted, stats.relationships_extracted, run.id
            ))
            self.model._conn.commit()
            
            return run
            
        except Exception as e:
            run.status = "failed"
            cursor.execute('UPDATE ingestion_runs SET status = ?, error_log = ? WHERE id = ?', ("failed", str(e), run.id))
            self.model._conn.commit()
            raise

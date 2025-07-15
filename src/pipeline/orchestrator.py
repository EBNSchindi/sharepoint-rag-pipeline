import autogen
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import yaml
import logging
from datetime import datetime
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.pdf_extractor import PDFExtractorAgent
from agents.context_enricher import ContextEnricherAgent
from agents.metadata_extractor import MetadataExtractorAgent
from agents.chunk_creator import ChunkCreatorAgent
from agents.quality_validator import QualityValidatorAgent

from pipeline.incremental_processor import IncrementalProcessor
from models.contextual_chunk import ContextualChunk

from storage.vector_store import ContextualVectorStore
from storage.metadata_store import MetadataStore

class ContextualRAGOrchestrator:
    def __init__(self, config_path: str):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback config
            self.config = self._get_default_config()
        
        self.logger = self._setup_logging()
        
        # Initialize components
        self.incremental_processor = IncrementalProcessor(self.config)
        
        # Initialize storage
        self.vector_store = ContextualVectorStore(self.config)
        self.metadata_store = MetadataStore(self.config)
        
        # Initialize agents
        self._init_agents()
        
        # AutoGen configuration
        self.user_proxy = autogen.UserProxyAgent(
            name="orchestrator",
            system_message="Pipeline orchestrator managing document processing.",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
    
    def _get_default_config(self) -> Dict:
        """Standard-Konfiguration falls keine Datei vorhanden"""
        return {
            'version': '1.0.0',
            'processing': {
                'batch_size': 10,
                'max_workers': 4,
                'timeout_per_document': 300
            },
            'quality_validation': {
                'min_quality_score': 70
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'state_directory': './data/state',
            'report_directory': './data/reports'
        }
    
    def _init_agents(self):
        """Initialisiere alle Agenten"""
        # Initialize all agents
        self.agents = {
            'pdf_extractor': PDFExtractorAgent(self.config),
            'context_enricher': ContextEnricherAgent(self.config),
            'metadata_extractor': MetadataExtractorAgent(self.config),
            'chunk_creator': ChunkCreatorAgent(self.config),
            'quality_validator': QualityValidatorAgent(self.config)
        }
        
        # Create AutoGen agent group
        autogen_agents = [agent.agent for agent in self.agents.values() if hasattr(agent, 'agent')]
        
        if autogen_agents and self.user_proxy:
            autogen_agents.append(self.user_proxy)
            
            self.groupchat = autogen.GroupChat(
                agents=autogen_agents,
                messages=[],
                max_round=10
            )
            
            self.manager = autogen.GroupChatManager(
                groupchat=self.groupchat,
                llm_config={"temperature": 0}
            )
    
    def process_documents(self, 
                         input_dir: str, 
                         force_all: bool = False,
                         max_workers: int = 4):
        """Hauptmethode für Dokumentverarbeitung"""
        start_time = time.time()
        input_path = Path(input_dir)
        
        self.logger.info(f"Starting contextual RAG pipeline for {input_path}")
        
        # Validiere Input Directory
        if not input_path.exists() or not input_path.is_dir():
            raise ValueError(f"Input directory does not exist: {input_path}")
        
        # Identifiziere zu verarbeitende Dateien
        if force_all:
            files_to_process = list(input_path.glob('*.pdf'))
            self.logger.info(f"Force processing all {len(files_to_process)} files")
        else:
            files_to_process = self.incremental_processor.get_files_to_process(input_path)
            self.logger.info(f"Found {len(files_to_process)} new/modified files")
        
        if not files_to_process:
            self.logger.info("No files to process")
            return self._generate_empty_report()
        
        # Verarbeite Dateien
        results = []
        failed_files = []
        
        # Verwende ThreadPoolExecutor für Parallelverarbeitung
        actual_workers = min(max_workers, len(files_to_process))
        
        with ThreadPoolExecutor(max_workers=actual_workers) as executor:
            future_to_file = {
                executor.submit(self._process_single_document, file_path): file_path
                for file_path in files_to_process
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"Successfully processed: {file_path.name}")
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path.name}: {str(e)}")
                    failed_files.append((file_path, str(e)))
        
        # Cleanup orphaned chunks
        if not force_all and self.vector_store:
            self.incremental_processor.cleanup_orphaned_chunks(self.vector_store)
        
        # Update pipeline state
        processing_time = time.time() - start_time
        self.incremental_processor.update_state('last_run', {
            'timestamp': datetime.now().isoformat(),
            'files_processed': len(results),
            'files_failed': len(failed_files),
            'processing_time': processing_time
        })
        
        # Generate report
        report = self._generate_pipeline_report(results, failed_files, processing_time)
        self._save_report(report)
        
        self.logger.info(f"Pipeline completed in {processing_time:.2f} seconds")
        
        return report
    
    def _process_single_document(self, file_path: Path) -> Dict:
        """Verarbeite einzelnes Dokument mit Kontext"""
        doc_start_time = time.time()
        doc_id = f"doc_{file_path.stem}_{int(time.time())}"
        
        try:
            # Step 1: Extract PDF
            self.logger.info(f"Extracting PDF: {file_path.name}")
            extraction_result = self.agents['pdf_extractor'].process_pdf(file_path)
            
            # Step 2: Extract metadata
            self.logger.info(f"Extracting metadata: {file_path.name}")
            metadata = self.agents['metadata_extractor'].extract_metadata(extraction_result)
            
            # Prepare document data
            document_data = {
                'doc_id': doc_id,
                'title': metadata.get('title', file_path.stem),
                'doc_type': metadata.get('doc_type', 'unknown'),
                'total_pages': extraction_result.get('total_pages', 1),
                'chunks': [],
                **metadata
            }
            
            # Step 3: Create initial chunks
            self.logger.info(f"Creating chunks: {file_path.name}")
            initial_chunks = self.agents['chunk_creator'].create_chunks(
                extraction_result.get('pages', []),
                document_data
            )
            
            # Step 4: Enrich chunks with context
            self.logger.info(f"Enriching chunks with context: {file_path.name}")
            contextual_chunks = self.agents['context_enricher'].enrich_chunks(
                initial_chunks,
                document_data
            )
            
            # Step 5: Validate quality
            self.logger.info(f"Validating quality: {file_path.name}")
            quality_report = self.agents['quality_validator'].validate_chunks(
                contextual_chunks,
                document_data
            )
            
            min_quality_score = self.config.get('quality_validation', {}).get('min_quality_score', 50)
            if quality_report['overall_score'] < min_quality_score:
                raise ValueError(f"Quality score too low: {quality_report['overall_score']}")
            
            # Step 6: Store in vector database
            self.logger.info(f"Storing in vector database: {file_path.name}")
            if self.vector_store:
                self.vector_store.store_contextual_chunks(contextual_chunks)
            
            # Step 7: Store metadata
            if self.metadata_store:
                self.metadata_store.store_document_metadata(doc_id, {
                    'file_path': str(file_path),
                    'processed_at': datetime.now().isoformat(),
                    'chunks_created': len(contextual_chunks),
                    'quality_report': quality_report,
                    **document_data
                })
            
            # Mark as processed
            processing_time = time.time() - doc_start_time
            self.incremental_processor.mark_as_processed(
                file_path, 
                doc_id,
                {
                    'chunks_created': len(contextual_chunks),
                    'processing_time': processing_time,
                    'quality_score': quality_report['overall_score']
                }
            )
            
            return {
                'doc_id': doc_id,
                'file_path': str(file_path),
                'chunks_created': len(contextual_chunks),
                'quality_score': quality_report['overall_score'],
                'processing_time': processing_time,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}", exc_info=True)
            return {
                'doc_id': doc_id,
                'file_path': str(file_path),
                'error': str(e),
                'processing_time': time.time() - doc_start_time,
                'status': 'failed'
            }
    
    
    def _generate_empty_report(self) -> Dict:
        """Generiere leeren Bericht wenn keine Dateien verarbeitet wurden"""
        return {
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': self.config.get('version', '1.0.0'),
            'summary': {
                'total_files_processed': 0,
                'successful': 0,
                'failed': 0,
                'total_processing_time': 0,
                'average_processing_time': 0
            },
            'chunks': {
                'total_created': 0,
                'average_per_document': 0
            },
            'quality': {
                'average_score': 0,
                'min_score': 0,
                'max_score': 0
            },
            'failures': [],
            'incremental_processing': self.incremental_processor.generate_processing_report()
        }
    
    def _generate_pipeline_report(self, 
                                 results: List[Dict], 
                                 failed_files: List[Tuple],
                                 total_time: float) -> Dict:
        """Erstelle detaillierten Pipeline-Bericht"""
        successful = [r for r in results if r['status'] == 'success']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': self.config.get('version', '1.0.0'),
            'summary': {
                'total_files_processed': len(results),
                'successful': len(successful),
                'failed': len(failed_files),
                'total_processing_time': total_time,
                'average_processing_time': total_time / len(results) if results else 0
            },
            'chunks': {
                'total_created': sum(r.get('chunks_created', 0) for r in successful),
                'average_per_document': sum(r.get('chunks_created', 0) for r in successful) / len(successful) if successful else 0
            },
            'quality': {
                'average_score': sum(r.get('quality_score', 0) for r in successful) / len(successful) if successful else 0,
                'min_score': min((r.get('quality_score', 100) for r in successful), default=0),
                'max_score': max((r.get('quality_score', 0) for r in successful), default=0)
            },
            'failures': [
                {
                    'file': str(file_path),
                    'error': error
                } for file_path, error in failed_files
            ],
            'incremental_processing': self.incremental_processor.generate_processing_report()
        }
        
        return report
    
    def _save_report(self, report: Dict):
        """Speichere Pipeline-Bericht"""
        report_dir = Path(self.config.get('report_directory', './data/reports'))
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'pipeline_report_{timestamp}.json'
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # Speichere auch als latest
            latest_file = report_dir / 'latest_report.json'
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Report saved to {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        
        # Erstelle logs directory
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_dir / 'contextual_pipeline.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(__name__)
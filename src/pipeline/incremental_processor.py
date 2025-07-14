import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple, Any
import logging

class IncrementalProcessor:
    """Verarbeitet nur neue oder geänderte Dokumente"""
    
    def __init__(self, config: dict):
        self.config = config
        self.state_dir = Path(config.get('state_directory', './data/state'))
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / 'pipeline_state.json'
        self.processed_files = self.state_dir / 'processed_files.json'
        
        self.logger = logging.getLogger(__name__)
        
        # Lade vorherigen State
        self.state = self._load_state()
        self.processed = self._load_processed_files()
    
    def get_files_to_process(self, input_dir: Path) -> List[Path]:
        """Identifiziere neue oder geänderte Dateien"""
        all_files = list(input_dir.glob('*.pdf'))
        files_to_process = []
        
        for file_path in all_files:
            file_hash = self._calculate_file_hash(file_path)
            file_key = str(file_path.relative_to(input_dir))
            
            # Prüfe ob Datei neu oder geändert ist
            if file_key not in self.processed:
                self.logger.info(f"New file detected: {file_key}")
                files_to_process.append(file_path)
            elif self.processed[file_key]['hash'] != file_hash:
                self.logger.info(f"Modified file detected: {file_key}")
                files_to_process.append(file_path)
            else:
                self.logger.debug(f"File unchanged, skipping: {file_key}")
        
        # Prüfe auf gelöschte Dateien
        existing_files = {str(f.relative_to(input_dir)) for f in all_files}
        deleted_files = set(self.processed.keys()) - existing_files
        
        if deleted_files:
            self.logger.info(f"Deleted files detected: {deleted_files}")
            # Diese müssen aus dem Vector Store entfernt werden
            self._mark_files_for_deletion(deleted_files)
        
        return files_to_process
    
    def mark_as_processed(self, file_path: Path, doc_id: str, metadata: Dict):
        """Markiere Datei als verarbeitet"""
        file_key = file_path.name
        
        self.processed[file_key] = {
            'hash': self._calculate_file_hash(file_path),
            'doc_id': doc_id,
            'processed_at': datetime.now().isoformat(),
            'chunks_created': metadata.get('chunks_created', 0),
            'processing_time': metadata.get('processing_time', 0),
            'quality_score': metadata.get('quality_score', 0),
            'file_size': file_path.stat().st_size,
            'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        self._save_processed_files()
    
    def update_state(self, key: str, value: Any):
        """Aktualisiere Pipeline State"""
        self.state[key] = value
        self.state['last_updated'] = datetime.now().isoformat()
        self._save_state()
    
    def get_state(self, key: str, default=None):
        """Hole Wert aus Pipeline State"""
        return self.state.get(key, default)
    
    def get_deleted_files(self) -> Set[str]:
        """Hole Liste der zu löschenden Dateien"""
        return set(self.state.get('deleted_files', []))
    
    def cleanup_orphaned_chunks(self, vector_store):
        """Entferne Chunks von gelöschten Dokumenten"""
        deleted_files = self.get_deleted_files()
        
        for file_key in deleted_files:
            if file_key in self.processed:
                doc_id = self.processed[file_key]['doc_id']
                
                try:
                    # Entferne aus Vector Store
                    vector_store.delete_document_chunks(doc_id)
                    
                    # Entferne aus processed files
                    del self.processed[file_key]
                    
                    self.logger.info(f"Cleaned up chunks for deleted file: {file_key}")
                    
                except Exception as e:
                    self.logger.error(f"Error cleaning up chunks for {file_key}: {str(e)}")
        
        # Leere deleted_files Liste
        self.state['deleted_files'] = []
        self._save_state()
        self._save_processed_files()
    
    def get_processing_statistics(self) -> Dict:
        """Hole Verarbeitungsstatistiken"""
        if not self.processed:
            return {
                'total_files': 0,
                'total_chunks': 0,
                'average_quality': 0,
                'average_processing_time': 0,
                'total_file_size': 0
            }
        
        total_files = len(self.processed)
        total_chunks = sum(f.get('chunks_created', 0) for f in self.processed.values())
        total_quality = sum(f.get('quality_score', 0) for f in self.processed.values())
        total_processing_time = sum(f.get('processing_time', 0) for f in self.processed.values())
        total_file_size = sum(f.get('file_size', 0) for f in self.processed.values())
        
        return {
            'total_files': total_files,
            'total_chunks': total_chunks,
            'average_quality': total_quality / total_files if total_files > 0 else 0,
            'average_processing_time': total_processing_time / total_files if total_files > 0 else 0,
            'total_file_size': total_file_size,
            'chunks_per_file': total_chunks / total_files if total_files > 0 else 0
        }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Berechne SHA-256 Hash einer Datei"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
    def _load_state(self) -> Dict:
        """Lade Pipeline State"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading state: {str(e)}")
        
        return {
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'deleted_files': []
        }
    
    def _save_state(self):
        """Speichere Pipeline State"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving state: {str(e)}")
    
    def _load_processed_files(self) -> Dict:
        """Lade Liste verarbeiteter Dateien"""
        try:
            if self.processed_files.exists():
                with open(self.processed_files, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading processed files: {str(e)}")
        
        return {}
    
    def _save_processed_files(self):
        """Speichere Liste verarbeiteter Dateien"""
        try:
            with open(self.processed_files, 'w', encoding='utf-8') as f:
                json.dump(self.processed, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving processed files: {str(e)}")
    
    def _mark_files_for_deletion(self, deleted_files: Set[str]):
        """Markiere Dateien für Löschung"""
        current_deleted = set(self.state.get('deleted_files', []))
        current_deleted.update(deleted_files)
        self.state['deleted_files'] = list(current_deleted)
        self._save_state()
    
    def generate_processing_report(self) -> Dict:
        """Erstelle Verarbeitungsbericht"""
        stats = self.get_processing_statistics()
        
        # Finde letzte Verarbeitung
        last_processing = None
        for file_info in self.processed.values():
            try:
                processed_at = datetime.fromisoformat(file_info['processed_at'])
                if last_processing is None or processed_at > last_processing:
                    last_processing = processed_at
            except:
                continue
        
        # Finde Dateien mit niedrigster Qualität
        low_quality_files = []
        for file_name, file_info in self.processed.items():
            quality = file_info.get('quality_score', 0)
            if quality < 70:  # Threshold für niedrige Qualität
                low_quality_files.append({
                    'file': file_name,
                    'quality_score': quality,
                    'chunks_created': file_info.get('chunks_created', 0)
                })
        
        low_quality_files.sort(key=lambda x: x['quality_score'])
        
        return {
            'statistics': stats,
            'last_processing': last_processing.isoformat() if last_processing else None,
            'pipeline_version': self.state.get('version', 'unknown'),
            'low_quality_files': low_quality_files[:10],  # Top 10 niedrigste Qualität
            'deleted_files_pending': len(self.get_deleted_files()),
            'state_file_size': self.state_file.stat().st_size if self.state_file.exists() else 0,
            'processed_files_count': len(self.processed)
        }
    
    def reset_processing_state(self, confirm: bool = False):
        """Lösche alle Verarbeitungsstatistiken (nur bei Bestätigung)"""
        if not confirm:
            raise ValueError("Reset requires explicit confirmation")
        
        self.processed = {}
        self.state = {
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'deleted_files': [],
            'reset_at': datetime.now().isoformat()
        }
        
        self._save_state()
        self._save_processed_files()
        
        self.logger.info("Processing state has been reset")
    
    def export_processing_history(self, output_path: Path):
        """Exportiere Verarbeitungshistorie"""
        history = {
            'export_timestamp': datetime.now().isoformat(),
            'pipeline_state': self.state,
            'processed_files': self.processed,
            'statistics': self.get_processing_statistics()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Processing history exported to {output_path}")
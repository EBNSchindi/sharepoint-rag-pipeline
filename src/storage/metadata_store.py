import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class MetadataStore:
    """Metadata Store für zusätzliche Dokumentmetadaten"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        self.db_path = Path(config.get('metadata_db_path', './data/metadata.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents (
                        doc_id TEXT PRIMARY KEY,
                        title TEXT,
                        doc_type TEXT,
                        file_path TEXT,
                        file_size INTEGER,
                        total_pages INTEGER,
                        total_chunks INTEGER,
                        creation_date TEXT,
                        last_modified TEXT,
                        processed_at TEXT,
                        extraction_method TEXT,
                        language TEXT,
                        version TEXT,
                        metadata_json TEXT,
                        quality_score REAL,
                        processing_time REAL
                    )
                ''')
                
                # Authors table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS authors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id TEXT,
                        author_name TEXT,
                        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
                    )
                ''')
                
                # Tags table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id TEXT,
                        tag_name TEXT,
                        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
                    )
                ''')
                
                # Processing history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processing_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id TEXT,
                        processed_at TEXT,
                        processing_version TEXT,
                        chunks_created INTEGER,
                        quality_score REAL,
                        processing_time REAL,
                        notes TEXT,
                        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
                    )
                ''')
                
                # Quality metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id TEXT,
                        metric_name TEXT,
                        metric_value REAL,
                        measured_at TEXT,
                        FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_authors_doc ON authors(doc_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_doc ON tags(doc_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_processing_doc ON processing_history(doc_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_doc ON quality_metrics(doc_id)')
                
                conn.commit()
                self.logger.info("Metadata database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing metadata database: {str(e)}")
            raise
    
    def store_document_metadata(self, doc_id: str, metadata: Dict) -> bool:
        """Store document metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store main document metadata
                cursor.execute('''
                    INSERT OR REPLACE INTO documents (
                        doc_id, title, doc_type, file_path, file_size, total_pages,
                        total_chunks, creation_date, last_modified, processed_at,
                        extraction_method, language, version, metadata_json,
                        quality_score, processing_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doc_id,
                    metadata.get('title', ''),
                    metadata.get('doc_type', ''),
                    metadata.get('file_path', ''),
                    metadata.get('file_size', 0),
                    metadata.get('total_pages', 0),
                    metadata.get('chunks_created', 0),
                    metadata.get('creation_date', ''),
                    metadata.get('last_modified', ''),
                    metadata.get('processed_at', datetime.now().isoformat()),
                    metadata.get('extraction_method', ''),
                    metadata.get('language', ''),
                    metadata.get('version', ''),
                    json.dumps(metadata, ensure_ascii=False),
                    metadata.get('quality_report', {}).get('overall_score', 0),
                    metadata.get('processing_time', 0)
                ))
                
                # Store authors
                cursor.execute('DELETE FROM authors WHERE doc_id = ?', (doc_id,))
                for author in metadata.get('authors', []):
                    cursor.execute(
                        'INSERT INTO authors (doc_id, author_name) VALUES (?, ?)',
                        (doc_id, author)
                    )
                
                # Store tags
                cursor.execute('DELETE FROM tags WHERE doc_id = ?', (doc_id,))
                for tag in metadata.get('tags', []):
                    cursor.execute(
                        'INSERT INTO tags (doc_id, tag_name) VALUES (?, ?)',
                        (doc_id, tag)
                    )
                
                # Store processing history
                cursor.execute('''
                    INSERT INTO processing_history (
                        doc_id, processed_at, processing_version, chunks_created,
                        quality_score, processing_time, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    doc_id,
                    metadata.get('processed_at', datetime.now().isoformat()),
                    metadata.get('processing_version', ''),
                    metadata.get('chunks_created', 0),
                    metadata.get('quality_report', {}).get('overall_score', 0),
                    metadata.get('processing_time', 0),
                    json.dumps(metadata.get('quality_report', {}), ensure_ascii=False)
                ))
                
                # Store quality metrics
                quality_report = metadata.get('quality_report', {})
                if quality_report and 'chunk_scores' in quality_report:
                    cursor.execute('DELETE FROM quality_metrics WHERE doc_id = ?', (doc_id,))
                    
                    # Overall metrics
                    cursor.execute('''
                        INSERT INTO quality_metrics (doc_id, metric_name, metric_value, measured_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        doc_id,
                        'overall_score',
                        quality_report.get('overall_score', 0),
                        datetime.now().isoformat()
                    ))
                    
                    # Individual chunk metrics
                    for i, chunk_score in enumerate(quality_report.get('chunk_scores', [])):
                        if isinstance(chunk_score, dict) and 'score' in chunk_score:
                            cursor.execute('''
                                INSERT INTO quality_metrics (doc_id, metric_name, metric_value, measured_at)
                                VALUES (?, ?, ?, ?)
                            ''', (
                                doc_id,
                                f'chunk_{i}_score',
                                chunk_score['score'],
                                datetime.now().isoformat()
                            ))
                
                conn.commit()
                self.logger.info(f"Stored metadata for document: {doc_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing metadata for document {doc_id}: {str(e)}")
            return False
    
    def get_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """Get document metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get main document data
                cursor.execute('SELECT * FROM documents WHERE doc_id = ?', (doc_id,))
                doc_row = cursor.fetchone()
                
                if not doc_row:
                    return None
                
                # Convert to dict
                doc_data = dict(doc_row)
                
                # Parse JSON metadata
                if doc_data['metadata_json']:
                    try:
                        doc_data['full_metadata'] = json.loads(doc_data['metadata_json'])
                    except json.JSONDecodeError:
                        doc_data['full_metadata'] = {}
                
                # Get authors
                cursor.execute('SELECT author_name FROM authors WHERE doc_id = ?', (doc_id,))
                doc_data['authors'] = [row[0] for row in cursor.fetchall()]
                
                # Get tags
                cursor.execute('SELECT tag_name FROM tags WHERE doc_id = ?', (doc_id,))
                doc_data['tags'] = [row[0] for row in cursor.fetchall()]
                
                # Get processing history
                cursor.execute('''
                    SELECT processed_at, processing_version, chunks_created, 
                           quality_score, processing_time, notes
                    FROM processing_history 
                    WHERE doc_id = ? 
                    ORDER BY processed_at DESC
                ''', (doc_id,))
                
                history_rows = cursor.fetchall()
                doc_data['processing_history'] = []
                
                for row in history_rows:
                    history_entry = dict(row)
                    if history_entry['notes']:
                        try:
                            history_entry['quality_report'] = json.loads(history_entry['notes'])
                        except json.JSONDecodeError:
                            history_entry['quality_report'] = {}
                    doc_data['processing_history'].append(history_entry)
                
                return doc_data
                
        except Exception as e:
            self.logger.error(f"Error retrieving metadata for document {doc_id}: {str(e)}")
            return None
    
    def search_documents(self, 
                        filters: Optional[Dict] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Dict]:
        """Search documents with filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query
                query = 'SELECT * FROM documents'
                params = []
                where_clauses = []
                
                if filters:
                    if 'doc_type' in filters:
                        where_clauses.append('doc_type = ?')
                        params.append(filters['doc_type'])
                    
                    if 'title_contains' in filters:
                        where_clauses.append('title LIKE ?')
                        params.append(f"%{filters['title_contains']}%")
                    
                    if 'language' in filters:
                        where_clauses.append('language = ?')
                        params.append(filters['language'])
                    
                    if 'min_quality_score' in filters:
                        where_clauses.append('quality_score >= ?')
                        params.append(filters['min_quality_score'])
                    
                    if 'processed_after' in filters:
                        where_clauses.append('processed_at >= ?')
                        params.append(filters['processed_after'])
                    
                    if 'author' in filters:
                        where_clauses.append('''
                            doc_id IN (
                                SELECT doc_id FROM authors 
                                WHERE author_name LIKE ?
                            )
                        ''')
                        params.append(f"%{filters['author']}%")
                    
                    if 'tag' in filters:
                        where_clauses.append('''
                            doc_id IN (
                                SELECT doc_id FROM tags 
                                WHERE tag_name LIKE ?
                            )
                        ''')
                        params.append(f"%{filters['tag']}%")
                
                if where_clauses:
                    query += ' WHERE ' + ' AND '.join(where_clauses)
                
                query += ' ORDER BY processed_at DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                documents = []
                for row in rows:
                    doc_data = dict(row)
                    
                    # Parse JSON metadata
                    if doc_data['metadata_json']:
                        try:
                            doc_data['full_metadata'] = json.loads(doc_data['metadata_json'])
                        except json.JSONDecodeError:
                            doc_data['full_metadata'] = {}
                    
                    # Get authors and tags
                    cursor.execute('SELECT author_name FROM authors WHERE doc_id = ?', (doc_data['doc_id'],))
                    doc_data['authors'] = [author_row[0] for author_row in cursor.fetchall()]
                    
                    cursor.execute('SELECT tag_name FROM tags WHERE doc_id = ?', (doc_data['doc_id'],))
                    doc_data['tags'] = [tag_row[0] for tag_row in cursor.fetchall()]
                    
                    documents.append(doc_data)
                
                return documents
                
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def delete_document_metadata(self, doc_id: str) -> bool:
        """Delete all metadata for a document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete from all tables
                cursor.execute('DELETE FROM quality_metrics WHERE doc_id = ?', (doc_id,))
                cursor.execute('DELETE FROM processing_history WHERE doc_id = ?', (doc_id,))
                cursor.execute('DELETE FROM tags WHERE doc_id = ?', (doc_id,))
                cursor.execute('DELETE FROM authors WHERE doc_id = ?', (doc_id,))
                cursor.execute('DELETE FROM documents WHERE doc_id = ?', (doc_id,))
                
                conn.commit()
                self.logger.info(f"Deleted metadata for document: {doc_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting metadata for document {doc_id}: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Document counts
                cursor.execute('SELECT COUNT(*) FROM documents')
                stats['total_documents'] = cursor.fetchone()[0]
                
                # Document types
                cursor.execute('''
                    SELECT doc_type, COUNT(*) 
                    FROM documents 
                    GROUP BY doc_type
                ''')
                stats['document_types'] = dict(cursor.fetchall())
                
                # Languages
                cursor.execute('''
                    SELECT language, COUNT(*) 
                    FROM documents 
                    WHERE language IS NOT NULL AND language != ""
                    GROUP BY language
                ''')
                stats['languages'] = dict(cursor.fetchall())
                
                # Quality scores
                cursor.execute('''
                    SELECT AVG(quality_score), MIN(quality_score), MAX(quality_score)
                    FROM documents
                    WHERE quality_score > 0
                ''')
                quality_stats = cursor.fetchone()
                if quality_stats[0] is not None:
                    stats['quality_scores'] = {
                        'average': quality_stats[0],
                        'minimum': quality_stats[1],
                        'maximum': quality_stats[2]
                    }
                
                # Processing times
                cursor.execute('''
                    SELECT AVG(processing_time), MIN(processing_time), MAX(processing_time)
                    FROM documents
                    WHERE processing_time > 0
                ''')
                time_stats = cursor.fetchone()
                if time_stats[0] is not None:
                    stats['processing_times'] = {
                        'average': time_stats[0],
                        'minimum': time_stats[1],
                        'maximum': time_stats[2]
                    }
                
                # Recent activity
                cursor.execute('''
                    SELECT DATE(processed_at) as date, COUNT(*) as count
                    FROM documents
                    WHERE processed_at IS NOT NULL
                    GROUP BY DATE(processed_at)
                    ORDER BY date DESC
                    LIMIT 30
                ''')
                stats['recent_activity'] = dict(cursor.fetchall())
                
                # Most common authors
                cursor.execute('''
                    SELECT author_name, COUNT(*) as count
                    FROM authors
                    GROUP BY author_name
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                stats['top_authors'] = dict(cursor.fetchall())
                
                # Most common tags
                cursor.execute('''
                    SELECT tag_name, COUNT(*) as count
                    FROM tags
                    GROUP BY tag_name
                    ORDER BY count DESC
                    LIMIT 20
                ''')
                stats['top_tags'] = dict(cursor.fetchall())
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 365) -> bool:
        """Clean up old processing history and quality metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now().replace(year=datetime.now().year - days_old // 365)
                cutoff_str = cutoff_date.isoformat()
                
                # Delete old processing history
                cursor.execute('''
                    DELETE FROM processing_history 
                    WHERE processed_at < ?
                ''', (cutoff_str,))
                
                # Delete old quality metrics
                cursor.execute('''
                    DELETE FROM quality_metrics 
                    WHERE measured_at < ?
                ''', (cutoff_str,))
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {days_old} days")
                return True
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            return False
    
    def export_metadata(self, output_path: Path) -> bool:
        """Export all metadata to JSON file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Export all tables
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'tables': {}
                }
                
                tables = ['documents', 'authors', 'tags', 'processing_history', 'quality_metrics']
                
                for table in tables:
                    cursor.execute(f'SELECT * FROM {table}')
                    rows = cursor.fetchall()
                    export_data['tables'][table] = [dict(row) for row in rows]
                
                # Write to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Exported metadata to {output_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error exporting metadata: {str(e)}")
            return False
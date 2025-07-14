import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError:
    chromadb = None
    SentenceTransformer = None

from models.contextual_chunk import ContextualChunk

class ContextualVectorStore:
    """Vector Store für contextual RAG mit ChromaDB"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Vector store configuration
        self.store_config = config.get('vector_store', {})
        self.store_type = self.store_config.get('type', 'chromadb')
        self.persist_directory = Path(self.store_config.get('persist_directory', './data/vectors'))
        self.collection_name = self.store_config.get('collection_name', 'sharepoint_contextual_kb')
        self.embedding_model_name = self.store_config.get('embedding_model', 'sentence-transformers/all-mpnet-base-v2')
        
        # Ensure directories exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.client = None
        self.collection = None
        self.embedding_model = None
        
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize vector store and embedding model"""
        if not chromadb:
            self.logger.warning("ChromaDB not available. Vector store will use fallback mode.")
            return
        
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    is_persistent=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                self.logger.info(f"Connected to existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"created_at": datetime.now().isoformat()}
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
            
            # Initialize embedding model
            if SentenceTransformer:
                try:
                    self.embedding_model = SentenceTransformer(self.embedding_model_name)
                    self.logger.info(f"Loaded embedding model: {self.embedding_model_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load embedding model: {str(e)}")
                    self.embedding_model = None
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {str(e)}")
            self.client = None
            self.collection = None
    
    def store_contextual_chunks(self, chunks: List[ContextualChunk]) -> bool:
        """Store contextual chunks in vector database"""
        if not self.collection:
            self.logger.warning("Vector store not available. Storing chunks in fallback mode.")
            return self._store_chunks_fallback(chunks)
        
        try:
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            for chunk in chunks:
                documents.append(chunk.content)
                metadatas.append(chunk.to_vector_metadata())
                ids.append(chunk.chunk_id)
                
                # Generate embedding if model is available
                if self.embedding_model:
                    try:
                        embedding = self.embedding_model.encode(chunk.content).tolist()
                        embeddings.append(embedding)
                    except Exception as e:
                        self.logger.error(f"Failed to generate embedding for chunk {chunk.chunk_id}: {str(e)}")
                        embeddings.append(None)
                else:
                    embeddings.append(None)
            
            # Store in ChromaDB
            if embeddings and all(e is not None for e in embeddings):
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                # Let ChromaDB generate embeddings
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            self.logger.info(f"Successfully stored {len(chunks)} chunks in vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing chunks in vector database: {str(e)}")
            return False
    
    def search_similar_chunks(self, 
                            query: str, 
                            n_results: int = 5,
                            filters: Optional[Dict] = None) -> List[Dict]:
        """Search for similar chunks"""
        if not self.collection:
            self.logger.warning("Vector store not available for search")
            return []
        
        try:
            # Build where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if key in ['document_id', 'document_type', 'chunk_type', 'semantic_role']:
                        where_clause[key] = value
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'chunk_id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching chunks: {str(e)}")
            return []
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """Get specific chunk by ID"""
        if not self.collection:
            return None
        
        try:
            results = self.collection.get(ids=[chunk_id])
            
            if results['documents'] and results['documents'][0]:
                return {
                    'chunk_id': chunk_id,
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving chunk {chunk_id}: {str(e)}")
            return None
    
    def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        """Get all chunks for a specific document"""
        if not self.collection:
            return []
        
        try:
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            formatted_results = []
            
            if results['documents']:
                for i in range(len(results['documents'])):
                    result = {
                        'chunk_id': results['ids'][i],
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error retrieving chunks for document {document_id}: {str(e)}")
            return []
    
    def delete_document_chunks(self, document_id: str) -> bool:
        """Delete all chunks for a specific document"""
        if not self.collection:
            return False
        
        try:
            # Get all chunk IDs for the document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                self.logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            
            return True  # No chunks to delete
            
        except Exception as e:
            self.logger.error(f"Error deleting chunks for document {document_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        if not self.collection:
            return {'error': 'Collection not available'}
        
        try:
            # Get collection info
            collection_info = self.collection.get()
            
            stats = {
                'total_chunks': len(collection_info['ids']) if collection_info['ids'] else 0,
                'collection_name': self.collection_name,
                'persist_directory': str(self.persist_directory)
            }
            
            # Document statistics
            if collection_info['metadatas']:
                document_ids = set()
                document_types = {}
                chunk_types = {}
                
                for metadata in collection_info['metadatas']:
                    doc_id = metadata.get('document_id', 'unknown')
                    document_ids.add(doc_id)
                    
                    doc_type = metadata.get('document_type', 'unknown')
                    document_types[doc_type] = document_types.get(doc_type, 0) + 1
                    
                    chunk_type = metadata.get('chunk_type', 'unknown')
                    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                
                stats.update({
                    'total_documents': len(document_ids),
                    'document_types': document_types,
                    'chunk_types': chunk_types
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}
    
    def _store_chunks_fallback(self, chunks: List[ContextualChunk]) -> bool:
        """Fallback storage method when ChromaDB is not available"""
        try:
            fallback_dir = self.persist_directory / 'fallback'
            fallback_dir.mkdir(exist_ok=True)
            
            # Store chunks as JSON files
            for chunk in chunks:
                chunk_data = {
                    'chunk_id': chunk.chunk_id,
                    'content': chunk.content,
                    'metadata': chunk.to_vector_metadata(),
                    'stored_at': datetime.now().isoformat()
                }
                
                chunk_file = fallback_dir / f"{chunk.chunk_id}.json"
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Stored {len(chunks)} chunks in fallback mode")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in fallback storage: {str(e)}")
            return False
    
    def reset_collection(self) -> bool:
        """Reset the entire collection (delete all data)"""
        if not self.client:
            return False
        
        try:
            # Delete existing collection
            self.client.delete_collection(name=self.collection_name)
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"created_at": datetime.now().isoformat()}
            )
            
            self.logger.info(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting collection: {str(e)}")
            return False
    
    def backup_collection(self, backup_path: Path) -> bool:
        """Create a backup of the collection"""
        if not self.collection:
            return False
        
        try:
            # Get all data
            all_data = self.collection.get()
            
            backup_data = {
                'collection_name': self.collection_name,
                'backup_timestamp': datetime.now().isoformat(),
                'total_chunks': len(all_data['ids']) if all_data['ids'] else 0,
                'data': all_data
            }
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save backup
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            return False
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """Restore collection from backup"""
        if not self.client or not backup_path.exists():
            return False
        
        try:
            # Load backup data
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Reset collection
            self.reset_collection()
            
            # Restore data
            data = backup_data['data']
            
            if data['ids']:
                self.collection.add(
                    documents=data['documents'],
                    metadatas=data['metadatas'],
                    ids=data['ids'],
                    embeddings=data.get('embeddings')
                )
            
            self.logger.info(f"Restored {len(data['ids']) if data['ids'] else 0} chunks from backup")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {str(e)}")
            return False
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class ChunkType(Enum):
    INTRODUCTION = "introduction"
    DEFINITION = "definition"
    EXAMPLE = "example"
    PROCEDURE = "procedure"
    WARNING = "warning"
    BEST_PRACTICE = "best_practice"
    REFERENCE = "reference"
    SUMMARY = "summary"
    UNKNOWN = "unknown"

class SemanticRole(Enum):
    MAIN_CONTENT = "main_content"
    SUPPORTING = "supporting"
    PREREQUISITE = "prerequisite"
    ADVANCED = "advanced"
    TROUBLESHOOTING = "troubleshooting"

class DocumentContext(BaseModel):
    """Umfassender Dokumentkontext"""
    document_id: str
    document_title: str
    document_type: str
    document_version: Optional[str] = None
    total_pages: int
    total_chunks: int
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    authors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
class HierarchicalContext(BaseModel):
    """Hierarchische Position im Dokument"""
    chapter: Optional[str] = None
    chapter_number: Optional[str] = None
    section: Optional[str] = None
    section_number: Optional[str] = None
    subsection: Optional[str] = None
    subsection_number: Optional[str] = None
    depth_level: int = 0
    
class NavigationalContext(BaseModel):
    """Navigation zu anderen Chunks"""
    previous_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = Field(default_factory=list)
    related_chunk_ids: List[str] = Field(default_factory=list)
    
class ContentContext(BaseModel):
    """Inhaltlicher Kontext"""
    chunk_type: ChunkType
    semantic_role: SemanticRole
    key_concepts: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    references_to: List[str] = Field(default_factory=list)  # Andere Dokumente
    referenced_by: List[str] = Field(default_factory=list)
    
class ContextualChunk(BaseModel):
    """Chunk mit vollständigem Kontext für RAG"""
    # Basis
    chunk_id: str
    content: str
    
    # Tokenization
    token_count: int
    char_count: int
    
    # Position
    page_numbers: List[int]
    position_in_document: float  # 0.0 bis 1.0
    
    # Kontext
    document_context: DocumentContext
    hierarchical_context: HierarchicalContext
    navigational_context: NavigationalContext
    content_context: ContentContext
    
    # Qualität
    extraction_confidence: float
    completeness_score: float
    
    # Metadaten
    extraction_method: str
    processed_at: datetime
    processing_version: str
    
    # Embeddings werden separat gespeichert
    embedding_model: Optional[str] = None
    
    def to_vector_metadata(self) -> Dict[str, Any]:
        """Konvertiere zu ChromaDB Metadaten"""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_context.document_id,
            "document_title": self.document_context.document_title,
            "document_type": self.document_context.document_type,
            "chunk_type": self.content_context.chunk_type.value,
            "semantic_role": self.content_context.semantic_role.value,
            "chapter": self.hierarchical_context.chapter or "",
            "section": self.hierarchical_context.section or "",
            "page_numbers": ",".join(map(str, self.page_numbers)),
            "position": self.position_in_document,
            "key_concepts": ",".join(self.content_context.key_concepts),
            "extraction_confidence": self.extraction_confidence,
            "processed_at": self.processed_at.isoformat()
        }
    
    def get_context_summary(self) -> str:
        """Erstelle Kontextzusammenfassung für RAG"""
        context_parts = []
        
        if self.document_context.document_title:
            context_parts.append(f"Document: {self.document_context.document_title}")
        
        if self.hierarchical_context.chapter:
            context_parts.append(f"Chapter: {self.hierarchical_context.chapter}")
        
        if self.hierarchical_context.section:
            context_parts.append(f"Section: {self.hierarchical_context.section}")
        
        if self.content_context.chunk_type != ChunkType.UNKNOWN:
            context_parts.append(f"Type: {self.content_context.chunk_type.value}")
        
        if self.content_context.key_concepts:
            concepts = ", ".join(self.content_context.key_concepts[:3])
            context_parts.append(f"Key concepts: {concepts}")
        
        return " | ".join(context_parts)
    
    def is_high_quality(self, threshold: float = 0.7) -> bool:
        """Prüfe ob Chunk hohe Qualität hat"""
        return (
            self.extraction_confidence >= threshold and
            self.completeness_score >= threshold and
            len(self.content.strip()) > 100
        )
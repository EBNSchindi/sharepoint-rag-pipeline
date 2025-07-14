from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class DocumentNode:
    """Represents a document in the knowledge graph"""
    doc_id: str
    title: str
    doc_type: str
    creation_date: Optional[datetime] = None
    authors: List[str] = None
    tags: List[str] = None
    chunk_count: int = 0
    quality_score: float = 0.0
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.tags is None:
            self.tags = []

@dataclass
class DocumentRelation:
    """Represents a relationship between documents"""
    source_doc_id: str
    target_doc_id: str
    relation_type: str  # 'references', 'similar_to', 'prerequisite', 'follows'
    strength: float = 0.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DocumentGraph:
    """Knowledge graph for document relationships and navigation"""
    
    def __init__(self):
        self.nodes: Dict[str, DocumentNode] = {}
        self.relations: List[DocumentRelation] = []
        self.relation_index: Dict[str, List[DocumentRelation]] = defaultdict(list)
        self.reverse_index: Dict[str, List[DocumentRelation]] = defaultdict(list)
        
    def add_document(self, doc_id: str, title: str, doc_type: str, **kwargs) -> DocumentNode:
        """Add a document to the graph"""
        node = DocumentNode(
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            **kwargs
        )
        self.nodes[doc_id] = node
        return node
    
    def add_relation(self, source_doc_id: str, target_doc_id: str, 
                    relation_type: str, strength: float = 0.0, **metadata) -> DocumentRelation:
        """Add a relationship between documents"""
        if source_doc_id not in self.nodes or target_doc_id not in self.nodes:
            raise ValueError("Both documents must exist in the graph")
        
        relation = DocumentRelation(
            source_doc_id=source_doc_id,
            target_doc_id=target_doc_id,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata
        )
        
        self.relations.append(relation)
        self.relation_index[source_doc_id].append(relation)
        self.reverse_index[target_doc_id].append(relation)
        
        return relation
    
    def get_document(self, doc_id: str) -> Optional[DocumentNode]:
        """Get a document by ID"""
        return self.nodes.get(doc_id)
    
    def get_related_documents(self, doc_id: str, 
                            relation_types: Optional[List[str]] = None,
                            min_strength: float = 0.0) -> List[Tuple[DocumentNode, DocumentRelation]]:
        """Get documents related to a given document"""
        results = []
        
        for relation in self.relation_index.get(doc_id, []):
            if relation_types and relation.relation_type not in relation_types:
                continue
            if relation.strength < min_strength:
                continue
            
            target_doc = self.nodes.get(relation.target_doc_id)
            if target_doc:
                results.append((target_doc, relation))
        
        return results
    
    def get_referring_documents(self, doc_id: str,
                              relation_types: Optional[List[str]] = None,
                              min_strength: float = 0.0) -> List[Tuple[DocumentNode, DocumentRelation]]:
        """Get documents that refer to a given document"""
        results = []
        
        for relation in self.reverse_index.get(doc_id, []):
            if relation_types and relation.relation_type not in relation_types:
                continue
            if relation.strength < min_strength:
                continue
            
            source_doc = self.nodes.get(relation.source_doc_id)
            if source_doc:
                results.append((source_doc, relation))
        
        return results
    
    def find_path(self, start_doc_id: str, end_doc_id: str, 
                 max_depth: int = 3) -> Optional[List[DocumentNode]]:
        """Find a path between two documents"""
        if start_doc_id == end_doc_id:
            return [self.nodes[start_doc_id]]
        
        visited = set()
        queue = [(start_doc_id, [self.nodes[start_doc_id]])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            for relation in self.relation_index.get(current_id, []):
                target_id = relation.target_doc_id
                
                if target_id == end_doc_id:
                    return path + [self.nodes[target_id]]
                
                if target_id not in visited:
                    queue.append((target_id, path + [self.nodes[target_id]]))
        
        return None
    
    def get_similar_documents(self, doc_id: str, 
                            similarity_threshold: float = 0.7) -> List[Tuple[DocumentNode, float]]:
        """Get documents similar to a given document"""
        if doc_id not in self.nodes:
            return []
        
        source_doc = self.nodes[doc_id]
        similar_docs = []
        
        # Find documents with similar tags
        for other_id, other_doc in self.nodes.items():
            if other_id == doc_id:
                continue
            
            # Tag-based similarity
            if source_doc.tags and other_doc.tags:
                common_tags = set(source_doc.tags) & set(other_doc.tags)
                tag_similarity = len(common_tags) / len(set(source_doc.tags) | set(other_doc.tags))
            else:
                tag_similarity = 0.0
            
            # Type-based similarity
            type_similarity = 1.0 if source_doc.doc_type == other_doc.doc_type else 0.0
            
            # Author-based similarity
            if source_doc.authors and other_doc.authors:
                common_authors = set(source_doc.authors) & set(other_doc.authors)
                author_similarity = len(common_authors) / len(set(source_doc.authors) | set(other_doc.authors))
            else:
                author_similarity = 0.0
            
            # Combined similarity
            overall_similarity = (tag_similarity * 0.5 + type_similarity * 0.3 + author_similarity * 0.2)
            
            if overall_similarity >= similarity_threshold:
                similar_docs.append((other_doc, overall_similarity))
        
        return sorted(similar_docs, key=lambda x: x[1], reverse=True)
    
    def get_document_clusters(self, similarity_threshold: float = 0.6) -> List[List[DocumentNode]]:
        """Group documents into clusters based on similarity"""
        clusters = []
        processed = set()
        
        for doc_id, doc in self.nodes.items():
            if doc_id in processed:
                continue
            
            # Start new cluster
            cluster = [doc]
            processed.add(doc_id)
            
            # Find similar documents
            similar_docs = self.get_similar_documents(doc_id, similarity_threshold)
            
            for similar_doc, _ in similar_docs:
                if similar_doc.doc_id not in processed:
                    cluster.append(similar_doc)
                    processed.add(similar_doc.doc_id)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        stats = {
            'total_documents': len(self.nodes),
            'total_relations': len(self.relations),
            'document_types': defaultdict(int),
            'relation_types': defaultdict(int),
            'authors': defaultdict(int),
            'tags': defaultdict(int)
        }
        
        # Document statistics
        for doc in self.nodes.values():
            stats['document_types'][doc.doc_type] += 1
            
            for author in doc.authors:
                stats['authors'][author] += 1
            
            for tag in doc.tags:
                stats['tags'][tag] += 1
        
        # Relation statistics
        for relation in self.relations:
            stats['relation_types'][relation.relation_type] += 1
        
        # Average metrics
        if self.nodes:
            total_quality = sum(doc.quality_score for doc in self.nodes.values())
            stats['average_quality_score'] = total_quality / len(self.nodes)
            
            total_chunks = sum(doc.chunk_count for doc in self.nodes.values())
            stats['average_chunks_per_document'] = total_chunks / len(self.nodes)
        
        return dict(stats)
    
    def export_to_json(self, file_path: str):
        """Export graph to JSON file"""
        data = {
            'nodes': [
                {
                    'doc_id': node.doc_id,
                    'title': node.title,
                    'doc_type': node.doc_type,
                    'creation_date': node.creation_date.isoformat() if node.creation_date else None,
                    'authors': node.authors,
                    'tags': node.tags,
                    'chunk_count': node.chunk_count,
                    'quality_score': node.quality_score
                }
                for node in self.nodes.values()
            ],
            'relations': [
                {
                    'source_doc_id': rel.source_doc_id,
                    'target_doc_id': rel.target_doc_id,
                    'relation_type': rel.relation_type,
                    'strength': rel.strength,
                    'metadata': rel.metadata
                }
                for rel in self.relations
            ],
            'exported_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_from_json(self, file_path: str):
        """Import graph from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Clear existing data
        self.nodes.clear()
        self.relations.clear()
        self.relation_index.clear()
        self.reverse_index.clear()
        
        # Import nodes
        for node_data in data['nodes']:
            creation_date = None
            if node_data.get('creation_date'):
                creation_date = datetime.fromisoformat(node_data['creation_date'])
            
            self.add_document(
                doc_id=node_data['doc_id'],
                title=node_data['title'],
                doc_type=node_data['doc_type'],
                creation_date=creation_date,
                authors=node_data.get('authors', []),
                tags=node_data.get('tags', []),
                chunk_count=node_data.get('chunk_count', 0),
                quality_score=node_data.get('quality_score', 0.0)
            )
        
        # Import relations
        for rel_data in data['relations']:
            self.add_relation(
                source_doc_id=rel_data['source_doc_id'],
                target_doc_id=rel_data['target_doc_id'],
                relation_type=rel_data['relation_type'],
                strength=rel_data.get('strength', 0.0),
                **rel_data.get('metadata', {})
            )
    
    def get_navigation_suggestions(self, current_doc_id: str, 
                                 context: str = "general") -> List[Dict]:
        """Get navigation suggestions for a document"""
        suggestions = []
        
        if current_doc_id not in self.nodes:
            return suggestions
        
        current_doc = self.nodes[current_doc_id]
        
        # Direct references
        related_docs = self.get_related_documents(current_doc_id, ['references'])
        for doc, relation in related_docs:
            suggestions.append({
                'doc_id': doc.doc_id,
                'title': doc.title,
                'type': 'reference',
                'reason': 'Referenced in current document',
                'relevance': relation.strength
            })
        
        # Similar documents
        similar_docs = self.get_similar_documents(current_doc_id, 0.5)
        for doc, similarity in similar_docs[:3]:  # Top 3 similar
            suggestions.append({
                'doc_id': doc.doc_id,
                'title': doc.title,
                'type': 'similar',
                'reason': f'Similar content ({similarity:.0%} match)',
                'relevance': similarity
            })
        
        # Prerequisites
        prereq_docs = self.get_related_documents(current_doc_id, ['prerequisite'])
        for doc, relation in prereq_docs:
            suggestions.append({
                'doc_id': doc.doc_id,
                'title': doc.title,
                'type': 'prerequisite',
                'reason': 'Recommended background reading',
                'relevance': relation.strength
            })
        
        # Follow-up documents
        followup_docs = self.get_related_documents(current_doc_id, ['follows'])
        for doc, relation in followup_docs:
            suggestions.append({
                'doc_id': doc.doc_id,
                'title': doc.title,
                'type': 'followup',
                'reason': 'Recommended next reading',
                'relevance': relation.strength
            })
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x['relevance'], reverse=True)
        
        return suggestions[:10]  # Top 10 suggestions
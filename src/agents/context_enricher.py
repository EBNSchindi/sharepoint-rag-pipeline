import autogen
from typing import List, Dict, Optional, Tuple
import re
from collections import defaultdict
from datetime import datetime

try:
    import spacy
    from transformers import pipeline
except ImportError:
    spacy = None
    pipeline = None

from models.contextual_chunk import (
    ContextualChunk, DocumentContext, HierarchicalContext, 
    NavigationalContext, ContentContext, ChunkType, SemanticRole
)

class ContextEnricherAgent:
    def __init__(self, config: dict):
        self.config = config
        
        # AutoGen Agent
        self.agent = autogen.AssistantAgent(
            name="context_enricher",
            system_message="""You are a context enrichment specialist.
            Analyze document structure, identify relationships between chunks,
            classify content types, and extract semantic information.""",
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER"
        )
        
        # NLP Tools (optional, with fallbacks)
        self.nlp = None
        self.classifier = None
        
        if spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy model not found. Using fallback methods.")
        
        if pipeline:
            try:
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
            except Exception:
                print("Warning: Transformers classifier not available. Using rule-based classification.")
        
        # Kontext-Regeln
        self.load_context_rules()
    
    def enrich_chunks(self, 
                     chunks: List[Dict], 
                     document_data: Dict) -> List[ContextualChunk]:
        """Reichere Chunks mit Kontext an"""
        
        # Erstelle Document Context
        doc_context = self._create_document_context(document_data)
        
        # Analysiere Dokumentstruktur
        hierarchy = self._analyze_document_hierarchy(chunks)
        
        # Erstelle Chunk-Graph für Navigation
        chunk_graph = self._build_chunk_graph(chunks)
        
        enriched_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Hierarchischer Kontext
            hier_context = self._get_hierarchical_context(chunk, hierarchy)
            
            # Navigationaler Kontext
            nav_context = self._get_navigational_context(i, chunks, chunk_graph)
            
            # Inhaltlicher Kontext
            content_context = self._analyze_content_context(chunk, document_data)
            
            # Erstelle ContextualChunk
            contextual_chunk = ContextualChunk(
                chunk_id=chunk['chunk_id'],
                content=chunk['content'],
                token_count=chunk.get('token_count', len(chunk['content'].split())),
                char_count=len(chunk['content']),
                page_numbers=chunk.get('page_numbers', []),
                position_in_document=i / len(chunks),
                document_context=doc_context,
                hierarchical_context=hier_context,
                navigational_context=nav_context,
                content_context=content_context,
                extraction_confidence=chunk.get('confidence', 0.9),
                completeness_score=self._calculate_completeness(chunk),
                extraction_method=chunk.get('extraction_method', 'unknown'),
                processed_at=datetime.now(),
                processing_version=self.config.get('version', '1.0.0')
            )
            
            enriched_chunks.append(contextual_chunk)
        
        # Post-Processing: Querverweise
        self._identify_cross_references(enriched_chunks)
        
        return enriched_chunks
    
    def _create_document_context(self, document_data: Dict) -> DocumentContext:
        """Erstelle Dokumentkontext"""
        return DocumentContext(
            document_id=document_data['doc_id'],
            document_title=document_data.get('title', 'Untitled'),
            document_type=document_data.get('doc_type', 'unknown'),
            document_version=document_data.get('version'),
            total_pages=document_data.get('total_pages', 0),
            total_chunks=len(document_data.get('chunks', [])),
            creation_date=document_data.get('creation_date'),
            last_modified=document_data.get('last_modified'),
            authors=document_data.get('authors', []),
            tags=document_data.get('tags', [])
        )
    
    def _analyze_document_hierarchy(self, chunks: List[Dict]) -> Dict:
        """Analysiere Dokumenthierarchie"""
        hierarchy = {
            'chapters': [],
            'sections': defaultdict(list),
            'subsections': defaultdict(list)
        }
        
        # Patterns für Hierarchie-Erkennung
        chapter_pattern = r'^(Chapter|CHAPTER)\s+(\d+\.?\d*):?\s*(.+)'
        section_pattern = r'^(\d+\.?\d*)\s+([A-Z][^.]+)'
        subsection_pattern = r'^(\d+\.\d+\.?\d*)\s+(.+)'
        
        current_chapter = None
        current_section = None
        
        for chunk in chunks:
            lines = chunk['content'].split('\n')
            
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                
                # Chapter detection
                chapter_match = re.match(chapter_pattern, line)
                if chapter_match:
                    current_chapter = {
                        'number': chapter_match.group(2),
                        'title': chapter_match.group(3),
                        'chunk_id': chunk['chunk_id']
                    }
                    hierarchy['chapters'].append(current_chapter)
                    continue
                
                # Section detection
                section_match = re.match(section_pattern, line)
                if section_match and current_chapter:
                    current_section = {
                        'number': section_match.group(1),
                        'title': section_match.group(2),
                        'chunk_id': chunk['chunk_id'],
                        'chapter': current_chapter['number']
                    }
                    hierarchy['sections'][current_chapter['number']].append(current_section)
                    continue
                
                # Subsection detection
                subsection_match = re.match(subsection_pattern, line)
                if subsection_match and current_section:
                    subsection = {
                        'number': subsection_match.group(1),
                        'title': subsection_match.group(2),
                        'chunk_id': chunk['chunk_id'],
                        'section': current_section['number']
                    }
                    hierarchy['subsections'][current_section['number']].append(subsection)
        
        return hierarchy
    
    def _build_chunk_graph(self, chunks: List[Dict]) -> Dict:
        """Baue Chunk-Beziehungsgraph"""
        graph = defaultdict(lambda: {
            'related': [],
            'references': [],
            'prerequisites': []
        })
        
        # Einfache Heuristik für Beziehungen
        for i, chunk in enumerate(chunks):
            chunk_id = chunk['chunk_id']
            
            # Sequenzielle Navigation
            if i > 0:
                graph[chunk_id]['previous'] = chunks[i-1]['chunk_id']
            if i < len(chunks) - 1:
                graph[chunk_id]['next'] = chunks[i+1]['chunk_id']
            
            # Finde Referenzen
            references = self._find_references(chunk['content'])
            graph[chunk_id]['references'].extend(references)
            
            # Finde verwandte Chunks basierend auf gemeinsamen Konzepten
            key_concepts = self._extract_key_concepts(chunk['content'])
            for j, other_chunk in enumerate(chunks):
                if i != j:
                    other_concepts = self._extract_key_concepts(other_chunk['content'])
                    overlap = len(set(key_concepts) & set(other_concepts))
                    if overlap >= 3:  # Mindestens 3 gemeinsame Konzepte
                        graph[chunk_id]['related'].append({
                            'chunk_id': other_chunk['chunk_id'],
                            'strength': overlap
                        })
        
        return graph
    
    def _analyze_content_context(self, chunk: Dict, document_data: Dict) -> ContentContext:
        """Analysiere inhaltlichen Kontext"""
        content = chunk['content']
        
        # Klassifiziere Chunk-Typ
        chunk_type = self._classify_chunk_type(content)
        
        # Bestimme semantische Rolle
        semantic_role = self._determine_semantic_role(content, document_data)
        
        # Extrahiere Schlüsselkonzepte
        key_concepts = self._extract_key_concepts(content)
        
        # Finde Prerequisites
        prerequisites = self._identify_prerequisites(content)
        
        return ContentContext(
            chunk_type=chunk_type,
            semantic_role=semantic_role,
            key_concepts=key_concepts,
            prerequisites=prerequisites,
            references_to=[],  # Wird später gefüllt
            referenced_by=[]   # Wird später gefüllt
        )
    
    def _classify_chunk_type(self, content: str) -> ChunkType:
        """Klassifiziere Chunk-Typ mit Zero-Shot Classification oder Rules"""
        if self.classifier:
            return self._classify_chunk_type_ml(content)
        else:
            return self._classify_chunk_type_rules(content)
    
    def _classify_chunk_type_ml(self, content: str) -> ChunkType:
        """ML-basierte Chunk-Typ Klassifikation"""
        candidate_labels = [
            "introduction", "definition", "example", "procedure",
            "warning", "best practice", "reference", "summary"
        ]
        
        # Nutze ersten Absatz für Klassifikation
        first_paragraph = content.split('\n\n')[0][:500]
        
        try:
            result = self.classifier(
                first_paragraph,
                candidate_labels=candidate_labels,
                hypothesis_template="This text is a {}."
            )
            
            top_label = result['labels'][0]
            return ChunkType(top_label.replace(" ", "_"))
        except:
            return self._classify_chunk_type_rules(content)
    
    def _classify_chunk_type_rules(self, content: str) -> ChunkType:
        """Regelbasierte Chunk-Typ Klassifikation"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['example:', 'for example', 'e.g.']):
            return ChunkType.EXAMPLE
        elif any(word in content_lower for word in ['warning:', 'caution:', 'important:']):
            return ChunkType.WARNING
        elif any(word in content_lower for word in ['best practice', 'recommended']):
            return ChunkType.BEST_PRACTICE
        elif any(word in content_lower for word in ['step 1', 'procedure:', 'how to']):
            return ChunkType.PROCEDURE
        elif any(word in content_lower for word in ['define', 'definition', 'what is']):
            return ChunkType.DEFINITION
        elif any(word in content_lower for word in ['summary', 'conclusion', 'in summary']):
            return ChunkType.SUMMARY
        elif any(word in content_lower for word in ['introduction', 'overview', 'getting started']):
            return ChunkType.INTRODUCTION
        else:
            return ChunkType.UNKNOWN
    
    def _determine_semantic_role(self, content: str, document_data: Dict) -> SemanticRole:
        """Bestimme semantische Rolle des Chunks"""
        content_lower = content.lower()
        
        # Troubleshooting content
        if any(word in content_lower for word in ['error', 'issue', 'problem', 'troubleshoot']):
            return SemanticRole.TROUBLESHOOTING
        
        # Prerequisites
        elif any(word in content_lower for word in ['prerequisite', 'before you begin', 'required']):
            return SemanticRole.PREREQUISITE
        
        # Advanced content
        elif any(word in content_lower for word in ['advanced', 'expert', 'detailed configuration']):
            return SemanticRole.ADVANCED
        
        # Supporting content
        elif any(word in content_lower for word in ['additional', 'optional', 'see also']):
            return SemanticRole.SUPPORTING
        
        # Default to main content
        else:
            return SemanticRole.MAIN_CONTENT
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extrahiere Schlüsselkonzepte mit NLP oder Regex"""
        if self.nlp:
            return self._extract_key_concepts_nlp(content)
        else:
            return self._extract_key_concepts_regex(content)
    
    def _extract_key_concepts_nlp(self, content: str) -> List[str]:
        """NLP-basierte Konzeptextraktion"""
        doc = self.nlp(content)
        
        concepts = []
        
        # Noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Max 3 Wörter
                concepts.append(chunk.text.lower())
        
        # Named entities
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'ORG', 'TECH']:
                concepts.append(ent.text.lower())
        
        # Deduplizieren und Top-10 zurückgeben
        concept_counts = {}
        for concept in concepts:
            concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        sorted_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)
        return [concept for concept, count in sorted_concepts[:10]]
    
    def _extract_key_concepts_regex(self, content: str) -> List[str]:
        """Regex-basierte Konzeptextraktion"""
        # Einfache Heuristik: Wiederholte Substantive und Eigennamen
        import re
        
        # Finde Wörter mit Großbuchstaben (potentielle Eigennamen)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', content)
        
        # Finde häufige Substantive
        words = re.findall(r'\b[a-z]+\b', content.lower())
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Mindestens 4 Buchstaben
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Kombiniere und sortiere
        all_concepts = proper_nouns + [word for word, count in word_counts.items() if count >= 2]
        
        # Deduplizieren und limitieren
        unique_concepts = list(set(all_concepts))[:10]
        return unique_concepts
    
    def _identify_prerequisites(self, content: str) -> List[str]:
        """Identifiziere Prerequisites"""
        prerequisites = []
        
        # Pattern für Prerequisites
        prereq_patterns = [
            r'requires?\s+(.+)',
            r'prerequisite[s]?:\s*(.+)',
            r'before\s+you\s+begin[,:]?\s*(.+)',
            r'you\s+need\s+(.+)',
            r'must\s+have\s+(.+)'
        ]
        
        for pattern in prereq_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                prereq = match.group(1).strip()
                if len(prereq) < 100:  # Reasonable length
                    prerequisites.append(prereq)
        
        return prerequisites[:5]  # Max 5 prerequisites
    
    def _find_references(self, content: str) -> List[str]:
        """Finde Referenzen zu anderen Dokumenten"""
        references = []
        
        # Pattern für Referenzen
        ref_patterns = [
            r'see\s+(?:also\s+)?[""]([^""]+)[""]',
            r'refer\s+to\s+[""]([^""]+)[""]',
            r'described\s+in\s+[""]([^""]+)[""]',
            r'\(see\s+([^)]+)\)',
            r'documentation:\s*[""]([^""]+)[""]'
        ]
        
        for pattern in ref_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                ref = match.group(1).strip()
                references.append(ref)
        
        return list(set(references))  # Deduplizieren
    
    def _get_hierarchical_context(self, chunk: Dict, hierarchy: Dict) -> HierarchicalContext:
        """Bestimme hierarchischen Kontext für Chunk"""
        chunk_id = chunk['chunk_id']
        
        context = HierarchicalContext()
        
        # Finde Chapter
        for chapter in hierarchy['chapters']:
            if chapter['chunk_id'] == chunk_id:
                context.chapter = chapter['title']
                context.chapter_number = chapter['number']
                context.depth_level = 1
                break
        
        # Finde Section
        for chapter_num, sections in hierarchy['sections'].items():
            for section in sections:
                if section['chunk_id'] == chunk_id:
                    context.section = section['title']
                    context.section_number = section['number']
                    context.chapter_number = chapter_num
                    context.depth_level = 2
                    
                    # Finde zugehöriges Chapter
                    for chapter in hierarchy['chapters']:
                        if chapter['number'] == chapter_num:
                            context.chapter = chapter['title']
                            break
                    break
        
        # Finde Subsection
        for section_num, subsections in hierarchy['subsections'].items():
            for subsection in subsections:
                if subsection['chunk_id'] == chunk_id:
                    context.subsection = subsection['title']
                    context.subsection_number = subsection['number']
                    context.section_number = section_num
                    context.depth_level = 3
                    
                    # Finde zugehörige Section und Chapter
                    for chapter_num, sections in hierarchy['sections'].items():
                        for section in sections:
                            if section['number'] == section_num:
                                context.section = section['title']
                                context.chapter_number = chapter_num
                                
                                for chapter in hierarchy['chapters']:
                                    if chapter['number'] == chapter_num:
                                        context.chapter = chapter['title']
                                        break
                                break
                    break
        
        return context
    
    def _get_navigational_context(self, 
                                 index: int, 
                                 chunks: List[Dict], 
                                 chunk_graph: Dict) -> NavigationalContext:
        """Erstelle Navigationskontext"""
        current_chunk_id = chunks[index]['chunk_id']
        
        context = NavigationalContext()
        
        # Sequential navigation
        if index > 0:
            context.previous_chunk_id = chunks[index - 1]['chunk_id']
        if index < len(chunks) - 1:
            context.next_chunk_id = chunks[index + 1]['chunk_id']
        
        # Related chunks from graph
        if current_chunk_id in chunk_graph:
            related = chunk_graph[current_chunk_id].get('related', [])
            # Sortiere nach Stärke der Beziehung
            related.sort(key=lambda x: x['strength'], reverse=True)
            context.related_chunk_ids = [r['chunk_id'] for r in related[:5]]
        
        return context
    
    def _calculate_completeness(self, chunk: Dict) -> float:
        """Berechne Vollständigkeitsscore"""
        score = 1.0
        content = chunk['content']
        
        # Prüfe auf abgeschnittene Sätze
        if not content.strip().endswith(('.', '!', '?', ':', ';')):
            score -= 0.2
        
        # Prüfe auf Mindestlänge
        if len(content.split()) < 50:
            score -= 0.1
        
        # Prüfe auf Code-Blöcke Vollständigkeit
        if '```' in content:
            if content.count('```') % 2 != 0:
                score -= 0.3
        
        return max(0.0, score)
    
    def _identify_cross_references(self, chunks: List[ContextualChunk]):
        """Identifiziere Querverweise zwischen Chunks"""
        # Baue Index von Konzepten zu Chunks
        concept_index = defaultdict(list)
        
        for chunk in chunks:
            for concept in chunk.content_context.key_concepts:
                concept_index[concept].append(chunk.chunk_id)
        
        # Aktualisiere Querverweise
        for chunk in chunks:
            # Finde Chunks die diesen Chunk referenzieren könnten
            for ref in chunk.content_context.references_to:
                ref_lower = ref.lower()
                for other_chunk in chunks:
                    if ref_lower in other_chunk.content.lower():
                        chunk.content_context.referenced_by.append(other_chunk.chunk_id)
    
    def load_context_rules(self):
        """Lade Kontext-Regeln aus Konfiguration"""
        # Implementierung abhängig von spezifischen Regeln
        pass
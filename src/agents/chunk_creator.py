import autogen
from typing import List, Dict, Optional, Tuple
import re
import logging
from datetime import datetime
import uuid

class ChunkCreatorAgent:
    """Agent für die Erstellung von Dokumentchunks"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # AutoGen Agent
        self.agent = autogen.AssistantAgent(
            name="chunk_creator",
            system_message="""You are a document chunking specialist.
            Split documents into meaningful chunks that preserve context
            and maintain readability for retrieval-augmented generation.""",
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER"
        )
        
        # Chunking configuration
        self.chunking_config = config.get('chunking', {})
        self.strategy = self.chunking_config.get('strategy', 'contextual')
        self.chunk_size = self.chunking_config.get('chunk_size', 1000)
        self.chunk_overlap = self.chunking_config.get('chunk_overlap', 200)
        self.min_chunk_size = self.chunking_config.get('min_chunk_size', 100)
        self.max_chunk_size = self.chunking_config.get('max_chunk_size', 2000)
        
        # Contextual chunking settings
        self.contextual_config = self.chunking_config.get('contextual_chunking', {})
        self.preserve_structure = self.contextual_config.get('preserve_structure', True)
        self.respect_boundaries = self.contextual_config.get('respect_boundaries', True)
        self.include_headers = self.contextual_config.get('include_headers', True)
    
    def create_chunks(self, pages: List[Dict], document_data: Dict) -> List[Dict]:
        """Erstelle Chunks aus den Dokumentseiten"""
        self.logger.info(f"Creating chunks using strategy: {self.strategy}")
        
        if self.strategy == 'contextual':
            return self._create_contextual_chunks(pages, document_data)
        elif self.strategy == 'semantic':
            return self._create_semantic_chunks(pages, document_data)
        elif self.strategy == 'fixed':
            return self._create_fixed_chunks(pages, document_data)
        else:
            self.logger.warning(f"Unknown chunking strategy: {self.strategy}, using contextual")
            return self._create_contextual_chunks(pages, document_data)
    
    def _create_contextual_chunks(self, pages: List[Dict], document_data: Dict) -> List[Dict]:
        """Erstelle kontextbewusste Chunks"""
        chunks = []
        
        # Kombiniere alle Seiten zu einem Text
        full_text = ""
        page_boundaries = []
        
        for page in pages:
            start_pos = len(full_text)
            page_content = page.get('content', '')
            full_text += page_content + "\n\n"
            
            page_boundaries.append({
                'page_number': page.get('page_number', 1),
                'start': start_pos,
                'end': len(full_text)
            })
        
        # Identifiziere Strukturelemente
        structure_elements = self._identify_structure_elements(full_text)
        
        # Erstelle Chunks basierend auf Struktur
        if self.preserve_structure and structure_elements:
            chunks = self._create_structure_based_chunks(
                full_text, 
                structure_elements, 
                page_boundaries, 
                document_data
            )
        else:
            # Fallback zu überlappendem Chunking
            chunks = self._create_overlapping_chunks(
                full_text, 
                page_boundaries, 
                document_data
            )
        
        return chunks
    
    def _create_semantic_chunks(self, pages: List[Dict], document_data: Dict) -> List[Dict]:
        """Erstelle semantische Chunks (vereinfachte Implementierung)"""
        # Für semantisches Chunking würde man normalerweise Sentence Embeddings verwenden
        # Hier implementieren wir eine vereinfachte Version basierend auf Absätzen
        
        chunks = []
        chunk_id_counter = 0
        
        for page in pages:
            content = page.get('content', '')
            paragraphs = self._split_into_paragraphs(content)
            
            current_chunk = ""
            current_chunk_tokens = 0
            
            for paragraph in paragraphs:
                paragraph_tokens = len(paragraph.split())
                
                if (current_chunk_tokens + paragraph_tokens > self.chunk_size and 
                    current_chunk_tokens > 0):
                    
                    # Erstelle Chunk
                    if current_chunk.strip():
                        chunk = self._create_chunk(
                            current_chunk.strip(),
                            chunk_id_counter,
                            [page.get('page_number', 1)],
                            document_data,
                            'semantic'
                        )
                        chunks.append(chunk)
                        chunk_id_counter += 1
                    
                    # Starte neuen Chunk
                    current_chunk = paragraph
                    current_chunk_tokens = paragraph_tokens
                else:
                    current_chunk += "\n\n" + paragraph
                    current_chunk_tokens += paragraph_tokens
            
            # Letzten Chunk hinzufügen
            if current_chunk.strip():
                chunk = self._create_chunk(
                    current_chunk.strip(),
                    chunk_id_counter,
                    [page.get('page_number', 1)],
                    document_data,
                    'semantic'
                )
                chunks.append(chunk)
                chunk_id_counter += 1
        
        return chunks
    
    def _create_fixed_chunks(self, pages: List[Dict], document_data: Dict) -> List[Dict]:
        """Erstelle Chunks mit fixer Größe"""
        chunks = []
        chunk_id_counter = 0
        
        # Kombiniere allen Text
        full_text = ""
        page_map = {}
        
        for page in pages:
            start_pos = len(full_text)
            page_content = page.get('content', '')
            full_text += page_content + " "
            
            # Mappe Textposition zu Seitenzahl
            for i in range(start_pos, len(full_text)):
                page_map[i] = page.get('page_number', 1)
        
        # Teile in fixe Chunks
        words = full_text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            
            if len(chunk_words) < self.min_chunk_size // 10:  # Approximation
                continue
            
            chunk_text = " ".join(chunk_words)
            
            # Bestimme Seitenzahlen für diesen Chunk
            chunk_start = len(" ".join(words[:i]))
            chunk_end = chunk_start + len(chunk_text)
            
            page_numbers = set()
            for pos in range(chunk_start, min(chunk_end, len(full_text))):
                if pos in page_map:
                    page_numbers.add(page_map[pos])
            
            chunk = self._create_chunk(
                chunk_text,
                chunk_id_counter,
                sorted(list(page_numbers)),
                document_data,
                'fixed'
            )
            chunks.append(chunk)
            chunk_id_counter += 1
        
        return chunks
    
    def _identify_structure_elements(self, text: str) -> List[Dict]:
        """Identifiziere Strukturelemente im Text"""
        elements = []
        
        # Patterns für verschiedene Strukturelemente
        patterns = [
            # Chapters
            (r'^(Chapter|CHAPTER)\s+(\d+)\.?\s*:?\s*(.+)', 'chapter', 1),
            (r'^(Kapitel)\s+(\d+)\.?\s*:?\s*(.+)', 'chapter', 1),
            
            # Sections
            (r'^(\d+)\.\s+([A-Z][^.]+)', 'section', 2),
            (r'^(\d+\.\d+)\s+([A-Z][^.]+)', 'subsection', 3),
            (r'^(\d+\.\d+\.\d+)\s+([A-Z][^.]+)', 'subsubsection', 4),
            
            # Headers
            (r'^([A-Z][A-Z\s]+)$', 'header', 2),
            (r'^([A-Z][a-z\s]+)$', 'header', 2),
            
            # Lists
            (r'^(\d+\.|\-|\*|\•)\s+(.+)', 'list_item', 5),
            
            # Special sections
            (r'^(Abstract|Summary|Zusammenfassung|Introduction|Einleitung|Conclusion|Fazit)', 'special_section', 2),
        ]
        
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            for pattern, element_type, priority in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    elements.append({
                        'type': element_type,
                        'line_number': line_num,
                        'text': line,
                        'priority': priority,
                        'match': match
                    })
                    break
        
        return sorted(elements, key=lambda x: x['line_number'])
    
    def _create_structure_based_chunks(self, 
                                     text: str, 
                                     structure_elements: List[Dict], 
                                     page_boundaries: List[Dict], 
                                     document_data: Dict) -> List[Dict]:
        """Erstelle Chunks basierend auf Dokumentstruktur"""
        chunks = []
        lines = text.split('\n')
        chunk_id_counter = 0
        
        # Gruppiere Strukturelemente
        sections = []
        current_section = {
            'start_line': 0,
            'end_line': len(lines),
            'header': '',
            'level': 0
        }
        
        for element in structure_elements:
            if element['type'] in ['chapter', 'section', 'subsection', 'special_section']:
                # Schließe vorherige Section
                if current_section['start_line'] < element['line_number']:
                    current_section['end_line'] = element['line_number']
                    sections.append(current_section)
                
                # Starte neue Section
                current_section = {
                    'start_line': element['line_number'],
                    'end_line': len(lines),
                    'header': element['text'],
                    'level': element['priority']
                }
        
        # Füge letzte Section hinzu
        if current_section['start_line'] < current_section['end_line']:
            sections.append(current_section)
        
        # Erstelle Chunks pro Section
        for section in sections:
            section_text = '\n'.join(lines[section['start_line']:section['end_line']])
            
            if len(section_text.strip()) < self.min_chunk_size:
                continue
            
            # Teile große Sections in mehrere Chunks
            section_chunks = self._split_large_section(
                section_text, 
                section['header'], 
                page_boundaries, 
                document_data
            )
            
            for chunk_text in section_chunks:
                if len(chunk_text.strip()) >= self.min_chunk_size:
                    # Bestimme Seitenzahlen
                    page_numbers = self._get_page_numbers_for_text(
                        chunk_text, 
                        page_boundaries, 
                        text
                    )
                    
                    chunk = self._create_chunk(
                        chunk_text,
                        chunk_id_counter,
                        page_numbers,
                        document_data,
                        'contextual',
                        section['header']
                    )
                    chunks.append(chunk)
                    chunk_id_counter += 1
        
        return chunks
    
    def _create_overlapping_chunks(self, 
                                 text: str, 
                                 page_boundaries: List[Dict], 
                                 document_data: Dict) -> List[Dict]:
        """Erstelle überlappende Chunks"""
        chunks = []
        chunk_id_counter = 0
        
        # Teile in Wörter
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            
            if len(chunk_words) < self.min_chunk_size // 10:  # Approximation
                continue
            
            chunk_text = " ".join(chunk_words)
            
            # Bestimme Seitenzahlen
            page_numbers = self._get_page_numbers_for_text(
                chunk_text, 
                page_boundaries, 
                text
            )
            
            chunk = self._create_chunk(
                chunk_text,
                chunk_id_counter,
                page_numbers,
                document_data,
                'overlapping'
            )
            chunks.append(chunk)
            chunk_id_counter += 1
        
        return chunks
    
    def _split_large_section(self, 
                           section_text: str, 
                           header: str, 
                           page_boundaries: List[Dict], 
                           document_data: Dict) -> List[str]:
        """Teile große Sections in kleinere Chunks"""
        if len(section_text.split()) <= self.max_chunk_size:
            return [section_text]
        
        chunks = []
        paragraphs = self._split_into_paragraphs(section_text)
        
        current_chunk = ""
        if self.include_headers and header:
            current_chunk = header + "\n\n"
        
        current_size = len(current_chunk.split())
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph.split())
            
            if current_size + paragraph_size > self.max_chunk_size and current_chunk.strip():
                chunks.append(current_chunk.strip())
                
                # Neuer Chunk mit Header
                current_chunk = ""
                if self.include_headers and header:
                    current_chunk = header + "\n\n"
                current_size = len(current_chunk.split())
            
            current_chunk += paragraph + "\n\n"
            current_size += paragraph_size
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Teile Text in Absätze"""
        # Teile bei doppelten Zeilenumbrüchen
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Entferne leere Absätze
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _get_page_numbers_for_text(self, 
                                  chunk_text: str, 
                                  page_boundaries: List[Dict], 
                                  full_text: str) -> List[int]:
        """Bestimme Seitenzahlen für einen Chunk"""
        # Finde Position des Chunks im Volltext
        chunk_start = full_text.find(chunk_text[:100])  # Erste 100 Zeichen
        
        if chunk_start == -1:
            return [1]  # Fallback
        
        chunk_end = chunk_start + len(chunk_text)
        
        # Finde betroffene Seiten
        page_numbers = set()
        
        for boundary in page_boundaries:
            if (boundary['start'] <= chunk_start <= boundary['end'] or 
                boundary['start'] <= chunk_end <= boundary['end'] or 
                (chunk_start <= boundary['start'] and chunk_end >= boundary['end'])):
                page_numbers.add(boundary['page_number'])
        
        return sorted(list(page_numbers)) if page_numbers else [1]
    
    def _create_chunk(self, 
                     content: str, 
                     chunk_id: int, 
                     page_numbers: List[int], 
                     document_data: Dict,
                     chunking_method: str,
                     header: str = "") -> Dict:
        """Erstelle einen Chunk"""
        chunk_uid = f"{document_data['doc_id']}_chunk_{chunk_id}"
        
        # Berechne Metriken
        token_count = len(content.split())
        char_count = len(content)
        
        # Qualitätsbewertung
        confidence = self._calculate_chunk_confidence(content, token_count)
        
        chunk = {
            'chunk_id': chunk_uid,
            'content': content,
            'token_count': token_count,
            'char_count': char_count,
            'page_numbers': page_numbers,
            'chunking_method': chunking_method,
            'confidence': confidence,
            'header': header,
            'created_at': datetime.now().isoformat()
        }
        
        return chunk
    
    def _calculate_chunk_confidence(self, content: str, token_count: int) -> float:
        """Berechne Confidence Score für einen Chunk"""
        confidence = 1.0
        
        # Größe-basierte Bewertung
        if token_count < self.min_chunk_size // 10:
            confidence *= 0.6
        elif token_count > self.max_chunk_size:
            confidence *= 0.8
        
        # Inhalt-basierte Bewertung
        if not content.strip():
            confidence = 0.0
        elif len(content.strip()) < 50:
            confidence *= 0.7
        
        # Struktur-basierte Bewertung
        if content.count('\n') == 0:  # Keine Zeilenumbrüche
            confidence *= 0.9
        
        # Vollständigkeit
        if not content.strip().endswith(('.', '!', '?', ':', ';')):
            confidence *= 0.9
        
        return max(0.0, min(1.0, confidence))
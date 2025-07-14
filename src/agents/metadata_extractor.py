import autogen
from typing import Dict, List, Optional
import re
from datetime import datetime, timezone
import logging

class MetadataExtractorAgent:
    """Agent für die Extraktion von Dokumentmetadaten"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # AutoGen Agent
        self.agent = autogen.AssistantAgent(
            name="metadata_extractor",
            system_message="""You are a metadata extraction specialist.
            Extract document metadata including title, authors, creation date,
            document type, and other relevant information from document content.""",
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER"
        )
    
    def extract_metadata(self, extraction_result: Dict) -> Dict:
        """Extrahiere Metadaten aus dem Extraktionsergebnis"""
        metadata = {}
        
        # Basis-Metadaten
        metadata['total_pages'] = extraction_result.get('total_pages', 0)
        metadata['total_chars'] = extraction_result.get('total_chars', 0)
        metadata['extraction_method'] = extraction_result.get('extraction_method', 'unknown')
        
        # Hole ersten Seiten-Content für Analyse
        pages = extraction_result.get('pages', [])
        if not pages:
            return metadata
        
        # Analysiere erste 3 Seiten für Metadaten
        content_for_analysis = ""
        for page in pages[:3]:
            content_for_analysis += page.get('content', '') + "\n"
        
        # Extrahiere spezifische Metadaten
        metadata.update(self._extract_title(content_for_analysis))
        metadata.update(self._extract_authors(content_for_analysis))
        metadata.update(self._extract_dates(content_for_analysis))
        metadata.update(self._extract_document_type(content_for_analysis))
        metadata.update(self._extract_version(content_for_analysis))
        metadata.update(self._extract_tags(content_for_analysis))
        metadata.update(self._extract_language(content_for_analysis))
        
        # Strukturelle Analyse
        metadata.update(self._analyze_structure(pages))
        
        return metadata
    
    def _extract_title(self, content: str) -> Dict:
        """Extrahiere Dokumenttitel"""
        title_patterns = [
            r'^(.+)(?:\n|\r\n?)(?:={3,}|-{3,})',  # Underlined title
            r'^([A-Z][A-Za-z\s]+(?:Guide|Manual|Documentation|Handbook|Reference))',  # Common document types
            r'^([A-Z][A-Za-z\s:]+)\s*\n\s*\n',  # Title followed by blank line
            r'Title:\s*(.+)',  # Explicit title
            r'^([A-Z][A-Za-z\s]+)\s*\n\s*Version',  # Title followed by version
        ]
        
        lines = content.split('\n')[:10]  # First 10 lines
        
        for pattern in title_patterns:
            for line in lines:
                match = re.search(pattern, line.strip(), re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if 3 <= len(title) <= 100:  # Reasonable title length
                        return {'title': title}
        
        # Fallback: First meaningful line
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not line.startswith(('Page', 'Chapter', 'Section')):
                return {'title': line[:100]}
        
        return {'title': 'Untitled Document'}
    
    def _extract_authors(self, content: str) -> Dict:
        """Extrahiere Autoren"""
        author_patterns = [
            r'(?:Author|Authors|By|Written by|Created by):\s*(.+)',
            r'(?:Author|Authors|By)\s*\n\s*(.+)',
            r'(?:©|Copyright).*?(\d{4}).*?([A-Z][a-z]+ [A-Z][a-z]+)',
        ]
        
        authors = []
        
        for pattern in author_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                author_text = match.group(1) if len(match.groups()) == 1 else match.group(2)
                
                # Split multiple authors
                potential_authors = re.split(r'[,;&]|\sand\s', author_text)
                
                for author in potential_authors:
                    author = author.strip()
                    if self._is_valid_author_name(author):
                        authors.append(author)
        
        return {'authors': list(set(authors))}  # Remove duplicates
    
    def _extract_dates(self, content: str) -> Dict:
        """Extrahiere Daten (Erstellung, Modifikation)"""
        date_patterns = [
            r'(?:Created|Date|Published):\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?:Created|Date|Published):\s*(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})',
            r'(?:Last updated|Modified|Revised):\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?:Last updated|Modified|Revised):\s*(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})',
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        ]
        
        dates = {}
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                
                if parsed_date:
                    if 'created' in match.group(0).lower():
                        dates['creation_date'] = parsed_date
                    elif any(word in match.group(0).lower() for word in ['updated', 'modified', 'revised']):
                        dates['last_modified'] = parsed_date
                    else:
                        dates['creation_date'] = parsed_date
        
        return dates
    
    def _extract_document_type(self, content: str) -> Dict:
        """Bestimme Dokumenttyp"""
        type_indicators = {
            'manual': ['manual', 'handbook', 'guide', 'instructions'],
            'reference': ['reference', 'api', 'documentation', 'spec', 'specification'],
            'tutorial': ['tutorial', 'walkthrough', 'getting started', 'quick start'],
            'policy': ['policy', 'procedure', 'process', 'standard'],
            'report': ['report', 'analysis', 'study', 'findings'],
            'presentation': ['presentation', 'slides', 'overview'],
            'whitepaper': ['whitepaper', 'white paper', 'research'],
            'faq': ['faq', 'frequently asked', 'questions and answers'],
            'readme': ['readme', 'read me', 'getting started'],
            'changelog': ['changelog', 'change log', 'release notes', 'version history']
        }
        
        content_lower = content.lower()
        
        for doc_type, indicators in type_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return {'doc_type': doc_type}
        
        return {'doc_type': 'unknown'}
    
    def _extract_version(self, content: str) -> Dict:
        """Extrahiere Versionsinformationen"""
        version_patterns = [
            r'Version\s*[:=]?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)',
            r'v\.?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)',
            r'Release\s*[:=]?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)',
            r'Rev\.?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return {'version': match.group(1)}
        
        return {}
    
    def _extract_tags(self, content: str) -> Dict:
        """Extrahiere Tags/Schlagwörter"""
        tag_patterns = [
            r'(?:Tags|Keywords|Topics):\s*(.+)',
            r'(?:Category|Categories):\s*(.+)',
            r'(?:Subject|Subjects):\s*(.+)',
        ]
        
        tags = []
        
        for pattern in tag_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                tag_text = match.group(1)
                
                # Split tags
                potential_tags = re.split(r'[,;]|\sand\s', tag_text)
                
                for tag in potential_tags:
                    tag = tag.strip()
                    if 2 <= len(tag) <= 30:  # Reasonable tag length
                        tags.append(tag.lower())
        
        # Automatische Tag-Extraktion basierend auf Inhalt
        auto_tags = self._extract_automatic_tags(content)
        tags.extend(auto_tags)
        
        return {'tags': list(set(tags))}  # Remove duplicates
    
    def _extract_language(self, content: str) -> Dict:
        """Bestimme Dokumentsprache"""
        # Einfache Heuristik basierend auf häufigen Wörtern
        english_indicators = ['the', 'and', 'for', 'are', 'with', 'this', 'that', 'have', 'from']
        german_indicators = ['der', 'die', 'das', 'und', 'für', 'sind', 'mit', 'dass', 'haben', 'von']
        
        content_lower = content.lower()
        
        english_count = sum(1 for word in english_indicators if word in content_lower)
        german_count = sum(1 for word in german_indicators if word in content_lower)
        
        if english_count > german_count:
            return {'language': 'en'}
        elif german_count > english_count:
            return {'language': 'de'}
        else:
            return {'language': 'unknown'}
    
    def _analyze_structure(self, pages: List[Dict]) -> Dict:
        """Analysiere Dokumentstruktur"""
        structure_info = {
            'has_table_of_contents': False,
            'has_index': False,
            'has_references': False,
            'has_appendix': False,
            'chapter_count': 0,
            'section_count': 0,
            'estimated_reading_time': 0
        }
        
        total_words = 0
        
        for page in pages:
            content = page.get('content', '')
            total_words += len(content.split())
            
            content_lower = content.lower()
            
            # Struktur-Indikatoren
            if any(indicator in content_lower for indicator in ['table of contents', 'contents', 'inhaltsverzeichnis']):
                structure_info['has_table_of_contents'] = True
            
            if any(indicator in content_lower for indicator in ['index', 'stichwortverzeichnis']):
                structure_info['has_index'] = True
            
            if any(indicator in content_lower for indicator in ['references', 'bibliography', 'literatur']):
                structure_info['has_references'] = True
            
            if any(indicator in content_lower for indicator in ['appendix', 'anhang']):
                structure_info['has_appendix'] = True
            
            # Zähle Kapitel und Sektionen
            chapter_matches = re.findall(r'^\s*(?:Chapter|Kapitel)\s+\d+', content, re.MULTILINE | re.IGNORECASE)
            structure_info['chapter_count'] += len(chapter_matches)
            
            section_matches = re.findall(r'^\s*\d+\.\d+\s+', content, re.MULTILINE)
            structure_info['section_count'] += len(section_matches)
        
        # Geschätzte Lesezeit (200 Wörter pro Minute)
        structure_info['estimated_reading_time'] = max(1, total_words // 200)
        
        return structure_info
    
    def _extract_automatic_tags(self, content: str) -> List[str]:
        """Automatische Tag-Extraktion"""
        # Technische Begriffe
        tech_patterns = [
            r'\b(API|REST|HTTP|JSON|XML|SQL|database|server|client|web|mobile|app|application)\b',
            r'\b(security|authentication|authorization|encryption|SSL|TLS)\b',
            r'\b(cloud|AWS|Azure|Google Cloud|Docker|Kubernetes|microservices)\b',
            r'\b(Python|Java|JavaScript|C\+\+|C#|PHP|Ruby|Go|Rust)\b',
            r'\b(React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel)\b',
        ]
        
        tags = []
        content_lower = content.lower()
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            tags.extend(matches)
        
        return list(set(tags))[:10]  # Max 10 automatic tags
    
    def _is_valid_author_name(self, name: str) -> bool:
        """Prüfe ob Name ein gültiger Autorenname ist"""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Muss mindestens einen Buchstaben enthalten
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Sollte nicht nur Zahlen oder Sonderzeichen sein
        if re.match(r'^[0-9\s\-\.]+$', name):
            return False
        
        return True
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse verschiedene Datumsformate"""
        date_formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
            '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
            '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d',
            '%d %B %Y', '%B %d, %Y', '%B %d %Y',
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.isoformat()
            except ValueError:
                continue
        
        return None
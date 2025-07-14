import autogen
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

try:
    import PyPDF2
    import pdfplumber
    import fitz  # PyMuPDF
except ImportError:
    PyPDF2 = None
    pdfplumber = None
    fitz = None

class PDFExtractorAgent:
    """Agent für PDF-Extraktion mit mehreren Fallback-Methoden"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # AutoGen Agent
        self.agent = autogen.AssistantAgent(
            name="pdf_extractor",
            system_message="""You are a PDF extraction specialist.
            Extract text content from PDF files using the most appropriate method.
            Preserve document structure and handle various PDF formats.""",
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER"
        )
        
        # Extraction settings
        self.extraction_config = config.get('extraction', {})
        self.primary_method = self.extraction_config.get('primary_method', 'pdfplumber')
        self.fallback_method = self.extraction_config.get('fallback_method', 'pypdf2')
        self.ocr_enabled = self.extraction_config.get('ocr_enabled', False)
    
    def process_pdf(self, file_path: Path) -> Dict:
        """Hauptmethode für PDF-Verarbeitung"""
        self.logger.info(f"Processing PDF: {file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Versuche verschiedene Extraktionsmethoden
        extraction_methods = self._get_extraction_methods()
        
        for method_name, method_func in extraction_methods:
            try:
                self.logger.info(f"Trying extraction method: {method_name}")
                result = method_func(file_path)
                
                if result and self._validate_extraction(result):
                    result['extraction_method'] = method_name
                    result['file_path'] = str(file_path)
                    result['extracted_at'] = datetime.now().isoformat()
                    
                    self.logger.info(f"Successfully extracted {result['total_pages']} pages using {method_name}")
                    return result
                    
            except Exception as e:
                self.logger.warning(f"Extraction method {method_name} failed: {str(e)}")
                continue
        
        # Wenn alle Methoden fehlschlagen, fallback
        self.logger.error(f"All extraction methods failed for {file_path}")
        return self._create_fallback_result(file_path)
    
    def _get_extraction_methods(self) -> List[tuple]:
        """Hole verfügbare Extraktionsmethoden in Prioritätsreihenfolge"""
        methods = []
        
        # Primäre Methode
        if self.primary_method == 'pdfplumber' and pdfplumber:
            methods.append(('pdfplumber', self._extract_with_pdfplumber))
        elif self.primary_method == 'pymupdf' and fitz:
            methods.append(('pymupdf', self._extract_with_pymupdf))
        elif self.primary_method == 'pypdf2' and PyPDF2:
            methods.append(('pypdf2', self._extract_with_pypdf2))
        
        # Fallback-Methoden
        if self.fallback_method == 'pdfplumber' and pdfplumber and self.primary_method != 'pdfplumber':
            methods.append(('pdfplumber', self._extract_with_pdfplumber))
        elif self.fallback_method == 'pymupdf' and fitz and self.primary_method != 'pymupdf':
            methods.append(('pymupdf', self._extract_with_pymupdf))
        elif self.fallback_method == 'pypdf2' and PyPDF2 and self.primary_method != 'pypdf2':
            methods.append(('pypdf2', self._extract_with_pypdf2))
        
        # Füge alle verfügbaren Methoden hinzu falls noch nicht vorhanden
        if pdfplumber and not any(m[0] == 'pdfplumber' for m in methods):
            methods.append(('pdfplumber', self._extract_with_pdfplumber))
        if fitz and not any(m[0] == 'pymupdf' for m in methods):
            methods.append(('pymupdf', self._extract_with_pymupdf))
        if PyPDF2 and not any(m[0] == 'pypdf2' for m in methods):
            methods.append(('pypdf2', self._extract_with_pypdf2))
        
        return methods
    
    def _extract_with_pdfplumber(self, file_path: Path) -> Dict:
        """Extraktion mit pdfplumber"""
        pages = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                
                if text:
                    # Extrahiere auch Tabellen
                    tables = page.extract_tables()
                    table_text = ""
                    
                    for table in tables:
                        for row in table:
                            if row:
                                table_text += " | ".join(str(cell) if cell else "" for cell in row) + "\n"
                    
                    full_text = text
                    if table_text:
                        full_text += "\n\nTables:\n" + table_text
                    
                    pages.append({
                        'page_number': page_num,
                        'content': full_text,
                        'char_count': len(full_text),
                        'has_tables': bool(tables),
                        'table_count': len(tables)
                    })
        
        return {
            'pages': pages,
            'total_pages': len(pages),
            'total_chars': sum(p['char_count'] for p in pages)
        }
    
    def _extract_with_pymupdf(self, file_path: Path) -> Dict:
        """Extraktion mit PyMuPDF"""
        pages = []
        
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            if text:
                # Extrahiere auch Bilder und Metadaten
                images = page.get_images()
                
                page_data = {
                    'page_number': page_num + 1,
                    'content': text,
                    'char_count': len(text),
                    'has_images': bool(images),
                    'image_count': len(images)
                }
                
                pages.append(page_data)
        
        doc.close()
        
        return {
            'pages': pages,
            'total_pages': len(pages),
            'total_chars': sum(p['char_count'] for p in pages)
        }
    
    def _extract_with_pypdf2(self, file_path: Path) -> Dict:
        """Extraktion mit PyPDF2"""
        pages = []
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                
                if text:
                    pages.append({
                        'page_number': page_num,
                        'content': text,
                        'char_count': len(text)
                    })
        
        return {
            'pages': pages,
            'total_pages': len(pages),
            'total_chars': sum(p['char_count'] for p in pages)
        }
    
    def _validate_extraction(self, result: Dict) -> bool:
        """Validiere Extraktionsergebnis"""
        if not result or not result.get('pages'):
            return False
        
        # Prüfe ob mindestens eine Seite Text enthält
        total_chars = sum(p.get('char_count', 0) for p in result['pages'])
        
        if total_chars < 100:  # Mindestens 100 Zeichen
            return False
        
        # Prüfe auf verdächtige Patterns (OCR-Fehler)
        for page in result['pages']:
            content = page.get('content', '')
            if len(content) > 1000:  # Nur bei längeren Texten prüfen
                # Zu viele einzelne Zeichen könnten OCR-Fehler sein
                single_chars = sum(1 for char in content if char.isalpha() and content.count(char) == 1)
                if single_chars > len(content) * 0.3:  # Mehr als 30% einzelne Zeichen
                    return False
        
        return True
    
    def _create_fallback_result(self, file_path: Path) -> Dict:
        """Erstelle Fallback-Ergebnis wenn alle Methoden fehlschlagen"""
        return {
            'pages': [{
                'page_number': 1,
                'content': f'[PDF extraction failed for {file_path.name}]',
                'char_count': 0,
                'extraction_error': True
            }],
            'total_pages': 1,
            'total_chars': 0,
            'extraction_method': 'fallback',
            'extraction_failed': True
        }
    
    def get_supported_methods(self) -> List[str]:
        """Hole Liste der unterstützten Extraktionsmethoden"""
        methods = []
        
        if pdfplumber:
            methods.append('pdfplumber')
        if fitz:
            methods.append('pymupdf')
        if PyPDF2:
            methods.append('pypdf2')
        
        return methods
    
    def extract_metadata(self, file_path: Path) -> Dict:
        """Extrahiere PDF-Metadaten"""
        metadata = {
            'file_size': file_path.stat().st_size,
            'file_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'extraction_methods_available': self.get_supported_methods()
        }
        
        # Versuche Metadaten mit PyMuPDF zu extrahieren
        if fitz:
            try:
                doc = fitz.open(file_path)
                pdf_metadata = doc.metadata
                
                metadata.update({
                    'title': pdf_metadata.get('title', ''),
                    'author': pdf_metadata.get('author', ''),
                    'subject': pdf_metadata.get('subject', ''),
                    'creator': pdf_metadata.get('creator', ''),
                    'producer': pdf_metadata.get('producer', ''),
                    'creation_date': pdf_metadata.get('creationDate', ''),
                    'modification_date': pdf_metadata.get('modDate', '')
                })
                
                doc.close()
                
            except Exception as e:
                self.logger.warning(f"Could not extract PDF metadata: {str(e)}")
        
        return metadata
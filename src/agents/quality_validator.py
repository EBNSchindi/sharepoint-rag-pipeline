import autogen
from typing import List, Dict, Optional, Any
import re
import logging
from collections import Counter
from datetime import datetime

from models.contextual_chunk import ContextualChunk

class QualityValidatorAgent:
    """Agent für die Qualitätsvalidierung von Chunks"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # AutoGen Agent
        self.agent = autogen.AssistantAgent(
            name="quality_validator",
            system_message="""You are a quality validation specialist.
            Assess the quality of document chunks by checking completeness,
            coherence, information density, and contextual consistency.""",
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER"
        )
        
        # Validation settings
        self.validation_config = config.get('quality_validation', {})
        self.min_quality_score = self.validation_config.get('min_quality_score', 70)
        self.check_completeness = self.validation_config.get('check_completeness', True)
        self.check_context_consistency = self.validation_config.get('check_context_consistency', True)
        self.validate_references = self.validation_config.get('validate_references', True)
    
    def validate_chunks(self, 
                       chunks: List[ContextualChunk], 
                       document_data: Dict) -> Dict:
        """Validiere eine Liste von Chunks"""
        self.logger.info(f"Validating {len(chunks)} chunks")
        
        validation_results = {
            'total_chunks': len(chunks),
            'chunk_scores': [],
            'quality_issues': [],
            'overall_score': 0,
            'validation_timestamp': datetime.now().isoformat(),
            'validation_details': {}
        }
        
        scores = []
        
        for i, chunk in enumerate(chunks):
            chunk_validation = self._validate_single_chunk(chunk, document_data, i)
            scores.append(chunk_validation['score'])
            validation_results['chunk_scores'].append(chunk_validation)
            
            # Sammle Probleme
            if chunk_validation['issues']:
                validation_results['quality_issues'].extend(chunk_validation['issues'])
        
        # Berechne Gesamtscore
        validation_results['overall_score'] = sum(scores) / len(scores) if scores else 0
        
        # Zusätzliche Validierungen
        validation_results['validation_details'] = self._perform_document_level_validation(
            chunks, document_data
        )
        
        # Qualitätszusammenfassung
        validation_results['quality_summary'] = self._generate_quality_summary(
            validation_results
        )
        
        return validation_results
    
    def _validate_single_chunk(self, 
                              chunk: ContextualChunk, 
                              document_data: Dict,
                              chunk_index: int) -> Dict:
        """Validiere einzelnen Chunk"""
        validation = {
            'chunk_id': chunk.chunk_id,
            'chunk_index': chunk_index,
            'score': 0,
            'issues': [],
            'metrics': {},
            'passed_checks': []
        }
        
        # Verschiedene Qualitätschecks
        checks = [
            self._check_content_completeness,
            self._check_content_coherence,
            self._check_information_density,
            self._check_context_consistency,
            self._check_chunk_size,
            self._check_language_quality,
            self._check_structural_integrity
        ]
        
        total_score = 0
        max_score = len(checks) * 100
        
        for check in checks:
            try:
                check_result = check(chunk, document_data)
                total_score += check_result['score']
                validation['metrics'][check_result['name']] = check_result
                
                if check_result['score'] >= 70:
                    validation['passed_checks'].append(check_result['name'])
                
                if check_result['issues']:
                    validation['issues'].extend(check_result['issues'])
                    
            except Exception as e:
                self.logger.error(f"Check {check.__name__} failed: {str(e)}")
                validation['issues'].append(f"Validation check failed: {check.__name__}")
        
        validation['score'] = (total_score / max_score) * 100 if max_score > 0 else 0
        
        return validation
    
    def _check_content_completeness(self, chunk: ContextualChunk, document_data: Dict) -> Dict:
        """Prüfe Vollständigkeit des Inhalts"""
        result = {
            'name': 'content_completeness',
            'score': 0,
            'issues': [],
            'details': {}
        }
        
        content = chunk.content
        
        # Minimale Länge
        if len(content.strip()) < 50:
            result['issues'].append("Content too short")
            result['score'] = 20
        elif len(content.strip()) < 100:
            result['issues'].append("Content quite short")
            result['score'] = 60
        else:
            result['score'] = 100
        
        # Vollständigkeit von Sätzen
        sentences = re.split(r'[.!?]+', content)
        complete_sentences = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 10 and 
                sentence[0].isupper() and 
                sentence[-1] not in '.!?'):
                complete_sentences += 1
        
        if complete_sentences / max(len(sentences), 1) > 0.8:
            result['score'] = min(result['score'] + 20, 100)
        
        # Abgeschnittene Wörter
        if re.search(r'\b[A-Za-z]{2,}-\s*$', content):
            result['issues'].append("Content appears to be cut off")
            result['score'] = max(result['score'] - 30, 0)
        
        result['details'] = {
            'content_length': len(content),
            'sentence_count': len(sentences),
            'complete_sentences': complete_sentences
        }
        
        return result
    
    def _check_content_coherence(self, chunk: ContextualChunk, document_data: Dict) -> Dict:
        """Prüfe Kohärenz des Inhalts"""
        result = {
            'name': 'content_coherence',
            'score': 80,  # Basis-Score
            'issues': [],
            'details': {}
        }
        
        content = chunk.content
        
        # Wiederholungen
        words = content.lower().split()
        word_counts = Counter(words)
        
        # Prüfe auf übermäßige Wiederholungen
        max_repetitions = 0
        for word, count in word_counts.items():
            if len(word) > 3 and count > 5:
                max_repetitions = max(max_repetitions, count)
        
        if max_repetitions > 8:
            result['issues'].append("Excessive word repetition detected")
            result['score'] -= 20
        
        # Logische Verbindungen
        connectives = ['however', 'therefore', 'furthermore', 'moreover', 'consequently']
        connective_count = sum(1 for conn in connectives if conn in content.lower())
        
        if connective_count > 0:
            result['score'] = min(result['score'] + 10, 100)
        
        # Fragmentierung
        if content.count('\n') > len(content) / 50:  # Zu viele Zeilenumbrüche
            result['issues'].append("Content appears fragmented")
            result['score'] -= 15
        
        result['details'] = {
            'max_word_repetitions': max_repetitions,
            'connective_count': connective_count,
            'line_breaks': content.count('\n')
        }
        
        return result
    
    def _check_information_density(self, chunk: ContextualChunk, document_data: Dict) -> Dict:
        """Prüfe Informationsdichte"""
        result = {
            'name': 'information_density',
            'score': 70,  # Basis-Score
            'issues': [],
            'details': {}
        }
        
        content = chunk.content
        
        # Verhältnis von Inhaltswörtern zu Funktionswörtern
        words = content.lower().split()
        
        # Häufige Funktionswörter
        function_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        content_words = [w for w in words if w not in function_words and len(w) > 2]
        
        if len(words) > 0:
            density_ratio = len(content_words) / len(words)
            
            if density_ratio > 0.6:
                result['score'] = min(result['score'] + 20, 100)
            elif density_ratio < 0.3:
                result['issues'].append("Low information density")
                result['score'] -= 20
        
        # Eindeutige Substantive
        nouns = []
        for word in words:
            if len(word) > 3 and word.isalpha():
                nouns.append(word)
        
        unique_nouns = len(set(nouns))
        
        if unique_nouns > len(words) * 0.15:  # Mehr als 15% eindeutige Substantive
            result['score'] = min(result['score'] + 15, 100)
        
        result['details'] = {
            'total_words': len(words),
            'content_words': len(content_words),
            'density_ratio': density_ratio if len(words) > 0 else 0,
            'unique_nouns': unique_nouns
        }
        
        return result
    
    def _check_context_consistency(self, chunk: ContextualChunk, document_data: Dict) -> Dict:
        """Prüfe Kontextkonsistenz"""
        result = {
            'name': 'context_consistency',
            'score': 85,  # Basis-Score
            'issues': [],
            'details': {}
        }
        
        # Prüfe Konsistenz mit Hierarchie
        if (chunk.hierarchical_context.chapter and 
            chunk.hierarchical_context.chapter.lower() not in chunk.content.lower()):
            
            # Erlaubt, wenn Kapitel im Header steht
            if not chunk.hierarchical_context.section:
                result['score'] -= 5
        
        # Prüfe Navigation
        if chunk.navigational_context.previous_chunk_id and not chunk.navigational_context.next_chunk_id:
            # Letzter Chunk sollte abschließenden Charakter haben
            if not any(word in chunk.content.lower() for word in ['conclusion', 'summary', 'fazit']):
                result['score'] -= 10
        
        # Prüfe Chunk-Typ Konsistenz
        chunk_type = chunk.content_context.chunk_type
        content_lower = chunk.content.lower()
        
        type_consistency = True
        
        if chunk_type.value == 'example' and 'example' not in content_lower:
            type_consistency = False
        elif chunk_type.value == 'warning' and not any(w in content_lower for w in ['warning', 'caution', 'important']):
            type_consistency = False
        elif chunk_type.value == 'procedure' and not any(w in content_lower for w in ['step', 'procedure', 'how to']):
            type_consistency = False
        
        if not type_consistency:
            result['issues'].append(f"Chunk type '{chunk_type.value}' inconsistent with content")
            result['score'] -= 15
        
        result['details'] = {
            'chunk_type': chunk_type.value,
            'has_chapter_context': bool(chunk.hierarchical_context.chapter),
            'has_navigation': bool(chunk.navigational_context.previous_chunk_id or chunk.navigational_context.next_chunk_id),
            'type_consistency': type_consistency
        }
        
        return result
    
    def _check_chunk_size(self, chunk: ContextualChunk, document_data: Dict) -> Dict:
        """Prüfe Chunk-Größe"""
        result = {
            'name': 'chunk_size',
            'score': 100,
            'issues': [],
            'details': {}
        }
        
        token_count = chunk.token_count
        char_count = chunk.char_count
        
        min_tokens = 50
        max_tokens = 2000
        optimal_range = (200, 1000)
        
        if token_count < min_tokens:
            result['issues'].append("Chunk too small")
            result['score'] = 30
        elif token_count > max_tokens:
            result['issues'].append("Chunk too large")
            result['score'] = 60
        elif optimal_range[0] <= token_count <= optimal_range[1]:
            result['score'] = 100
        else:
            result['score'] = 80
        
        # Verhältnis Token zu Zeichen
        if token_count > 0:
            char_per_token = char_count / token_count
            if char_per_token < 3 or char_per_token > 10:
                result['issues'].append("Unusual character-to-token ratio")
                result['score'] -= 10
        
        result['details'] = {
            'token_count': token_count,
            'char_count': char_count,
            'char_per_token': char_count / token_count if token_count > 0 else 0,
            'in_optimal_range': optimal_range[0] <= token_count <= optimal_range[1]
        }
        
        return result
    
    def _check_language_quality(self, chunk: ContextualChunk, document_data: Dict) -> Dict:
        """Prüfe Sprachqualität"""
        result = {
            'name': 'language_quality',
            'score': 80,  # Basis-Score
            'issues': [],
            'details': {}
        }
        
        content = chunk.content
        
        # Encoding-Probleme
        if '�' in content:
            result['issues'].append("Encoding problems detected")
            result['score'] -= 30
        
        # Übermäßige Whitespaces
        if re.search(r'\s{5,}', content):
            result['issues'].append("Excessive whitespace")
            result['score'] -= 10
        
        # Zeilen mit nur Sonderzeichen
        lines = content.split('\n')
        special_char_lines = sum(1 for line in lines if line.strip() and not re.search(r'[a-zA-Z]', line))
        
        if special_char_lines > len(lines) * 0.3:
            result['issues'].append("Too many lines with special characters only")
            result['score'] -= 20
        
        # Durchschnittliche Wortlänge
        words = content.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            if avg_word_length < 3:
                result['issues'].append("Average word length too short")
                result['score'] -= 15
            elif avg_word_length > 8:
                result['issues'].append("Average word length too long")
                result['score'] -= 10
        
        result['details'] = {
            'has_encoding_issues': '�' in content,
            'special_char_lines': special_char_lines,
            'avg_word_length': avg_word_length if words else 0,
            'total_lines': len(lines)
        }
        
        return result
    
    def _check_structural_integrity(self, chunk: ContextualChunk, document_data: Dict) -> Dict:
        """Prüfe strukturelle Integrität"""
        result = {
            'name': 'structural_integrity',
            'score': 90,  # Basis-Score
            'issues': [],
            'details': {}
        }
        
        content = chunk.content
        
        # Unvollständige Tabellen
        if '|' in content:
            lines_with_pipes = [line for line in content.split('\n') if '|' in line]
            if len(lines_with_pipes) > 1:
                # Prüfe Konsistenz der Spaltenanzahl
                column_counts = [line.count('|') for line in lines_with_pipes]
                if len(set(column_counts)) > 2:  # Mehr als 2 verschiedene Spaltenanzahlen
                    result['issues'].append("Inconsistent table structure")
                    result['score'] -= 15
        
        # Unvollständige Listen
        list_markers = re.findall(r'^[\s]*[\d\-\*\•]\s+', content, re.MULTILINE)
        if len(list_markers) > 1:
            # Prüfe auf unterbrochene Listen
            list_lines = [i for i, line in enumerate(content.split('\n')) 
                         if re.match(r'^[\s]*[\d\-\*\•]\s+', line)]
            
            if list_lines:
                gaps = [list_lines[i+1] - list_lines[i] for i in range(len(list_lines)-1)]
                if any(gap > 3 for gap in gaps):
                    result['issues'].append("Interrupted list structure")
                    result['score'] -= 10
        
        # Code-Blöcke
        if '```' in content:
            code_blocks = content.count('```')
            if code_blocks % 2 != 0:
                result['issues'].append("Incomplete code block")
                result['score'] -= 20
        
        result['details'] = {
            'has_tables': '|' in content,
            'has_lists': len(list_markers) > 0,
            'has_code_blocks': '```' in content,
            'code_block_count': content.count('```')
        }
        
        return result
    
    def _perform_document_level_validation(self, 
                                         chunks: List[ContextualChunk], 
                                         document_data: Dict) -> Dict:
        """Führe dokumentweite Validierung durch"""
        details = {
            'chunk_distribution': {},
            'content_coverage': {},
            'consistency_checks': {},
            'navigation_integrity': {}
        }
        
        # Chunk-Typ-Verteilung
        type_distribution = {}
        for chunk in chunks:
            chunk_type = chunk.content_context.chunk_type.value
            type_distribution[chunk_type] = type_distribution.get(chunk_type, 0) + 1
        
        details['chunk_distribution'] = type_distribution
        
        # Content Coverage
        total_chars = sum(chunk.char_count for chunk in chunks)
        page_coverage = set()
        
        for chunk in chunks:
            page_coverage.update(chunk.page_numbers)
        
        details['content_coverage'] = {
            'total_characters': total_chars,
            'pages_covered': len(page_coverage),
            'expected_pages': document_data.get('total_pages', 1),
            'coverage_ratio': len(page_coverage) / max(document_data.get('total_pages', 1), 1)
        }
        
        # Navigation Integrity
        navigation_issues = []
        for i, chunk in enumerate(chunks):
            if chunk.navigational_context.previous_chunk_id:
                if i == 0:
                    navigation_issues.append(f"First chunk has previous reference: {chunk.chunk_id}")
            
            if chunk.navigational_context.next_chunk_id:
                if i == len(chunks) - 1:
                    navigation_issues.append(f"Last chunk has next reference: {chunk.chunk_id}")
        
        details['navigation_integrity'] = {
            'issues': navigation_issues,
            'chunks_with_navigation': sum(1 for chunk in chunks 
                                        if chunk.navigational_context.previous_chunk_id or 
                                           chunk.navigational_context.next_chunk_id)
        }
        
        return details
    
    def _generate_quality_summary(self, validation_results: Dict) -> Dict:
        """Generiere Qualitätszusammenfassung"""
        summary = {
            'overall_grade': 'Unknown',
            'major_issues': [],
            'recommendations': [],
            'strengths': []
        }
        
        overall_score = validation_results['overall_score']
        
        # Gesamtbewertung
        if overall_score >= 90:
            summary['overall_grade'] = 'Excellent'
        elif overall_score >= 80:
            summary['overall_grade'] = 'Good'
        elif overall_score >= 70:
            summary['overall_grade'] = 'Acceptable'
        elif overall_score >= 60:
            summary['overall_grade'] = 'Needs Improvement'
        else:
            summary['overall_grade'] = 'Poor'
        
        # Sammle häufige Probleme
        issue_counts = {}
        for chunk_validation in validation_results['chunk_scores']:
            for issue in chunk_validation['issues']:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Top-3 Probleme
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        summary['major_issues'] = [f"{issue} ({count} chunks)" for issue, count in top_issues]
        
        # Empfehlungen
        if overall_score < 70:
            summary['recommendations'].append("Consider improving content extraction method")
        
        if any('too short' in str(issue).lower() for issue in summary['major_issues']):
            summary['recommendations'].append("Increase minimum chunk size")
        
        if any('fragmented' in str(issue).lower() for issue in summary['major_issues']):
            summary['recommendations'].append("Improve chunk boundary detection")
        
        # Stärken
        good_chunks = sum(1 for score in validation_results['chunk_scores'] if score['score'] >= 80)
        if good_chunks > len(validation_results['chunk_scores']) * 0.8:
            summary['strengths'].append("High percentage of quality chunks")
        
        if validation_results['validation_details']['content_coverage']['coverage_ratio'] > 0.9:
            summary['strengths'].append("Excellent page coverage")
        
        return summary
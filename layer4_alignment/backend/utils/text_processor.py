"""
Text Processor

Utilities for multilingual text normalization and processing.
"""

import re
from typing import List, Set


class TextProcessor:
    """
    Text processing utilities for alignment.
    """
    
    # Common stopwords
    STOPWORDS_EN = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'to', 'of', 'in', 'for', 'on',
        'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
        'if', 'then', 'else', 'when', 'where', 'why', 'how', 'which', 'who',
        'this', 'that', 'these', 'those', 'it', 'its', 'not', 'no', 'yes'
    }
    
    STOPWORDS_ZH = {'的', '是', '在', '了', '和', '与', '或', '等', '及', '把', '被', '也', '有'}
    
    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normalize text for comparison.
        
        - Lowercase
        - Collapse whitespace
        - Remove extra punctuation
        """
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        text = text.strip()
        
        return text
    
    @classmethod
    def extract_keywords(cls, text: str, min_length: int = 2) -> Set[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Input text
            min_length: Minimum word length
            
        Returns:
            Set of keywords
        """
        text = cls.normalize(text)
        
        keywords = set()
        
        # English words
        words = re.findall(r'\b[a-z]+\b', text)
        for word in words:
            if len(word) >= min_length and word not in cls.STOPWORDS_EN:
                keywords.add(word)
        
        # Chinese terms (2+ character sequences)
        chinese = re.findall(r'[\u4e00-\u9fff]+', text)
        for term in chinese:
            if len(term) >= 2 and term not in cls.STOPWORDS_ZH:
                keywords.add(term)
        
        return keywords
    
    @classmethod
    def truncate(cls, text: str, max_length: int = 500, suffix: str = "...") -> str:
        """
        Truncate text to max length with suffix.
        """
        if not text or len(text) <= max_length:
            return text or ""
        
        return text[:max_length - len(suffix)] + suffix
    
    @classmethod
    def clean_for_export(cls, text: str) -> str:
        """
        Clean text for export (remove problematic characters).
        """
        if not text:
            return ""
        
        # Remove newlines and tabs
        text = re.sub(r'[\r\n\t]+', ' ', text)
        # Collapse whitespace
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Simple language detection based on character types.
        
        Returns:
            Language code guess ('en', 'zh', 'ja', 'ko', 'other')
        """
        if not text:
            return 'unknown'
        
        # Count character types
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        japanese = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        korean = len(re.findall(r'[\uac00-\ud7af]', text))
        latin = len(re.findall(r'[a-zA-Z]', text))
        
        total = chinese + japanese + korean + latin
        if total == 0:
            return 'unknown'
        
        if japanese > 0.1 * total:
            return 'ja'
        if korean > 0.1 * total:
            return 'ko'
        if chinese > 0.3 * total:
            return 'zh'
        if latin > 0.5 * total:
            return 'en'
        
        return 'other'

"""
Rule-Based Keyword Aligner

Uses keyword matching and TF-IDF to score candidate relevance.
Deterministic and explainable, no API dependencies.
"""

import re
from typing import List, Dict, Any, Set
from collections import Counter

from .base_aligner import BaseAligner, AlignmentResult


class RuleAligner(BaseAligner):
    """
    Aligns candidates using keyword and TF-IDF matching.
    
    Extracts keywords from term and definition, then scores
    candidates based on keyword overlap and TF-IDF weighting.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.use_fuzzy = config.get("use_fuzzy", True)
        self.fuzzy_threshold = config.get("fuzzy_threshold", 0.85)
        self.tfidf_top_k = config.get("tfidf_top_k", 20)
        
        # Common stopwords for filtering
        self.stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'and', 'but', 'if', 'or', 'because', 'until', 'while', 'although',
            'this', 'that', 'these', 'those', 'it', 'its', 'which', 'who',
            '的', '是', '在', '了', '和', '与', '或', '等', '及', '把', '被'
        }
    
    async def align(
        self,
        term: str,
        term_definition: str,
        candidates: List[Dict[str, Any]],
        layer: str
    ) -> List[AlignmentResult]:
        """
        Score candidates using keyword matching.
        """
        if not candidates:
            return []
        
        # Extract keywords from term and definition
        term_keywords = self._extract_keywords(f"{term} {term_definition}")
        
        results = []
        
        for candidate in candidates:
            text = candidate.get('text', candidate.get('title', ''))
            if candidate.get('summary'):
                text = f"{candidate.get('title', '')} {candidate.get('summary', '')}"
            
            # Calculate score
            score = self._calculate_score(term, term_keywords, text)
            
            # Get matched keywords for explanation
            candidate_keywords = self._extract_keywords(text)
            matched = term_keywords & candidate_keywords
            
            results.append(AlignmentResult(
                candidate_id=candidate['id'],
                score=score,
                method="rule_keyword",
                reason=f"Matched: {', '.join(list(matched)[:5])}" if matched else None,
                metadata={
                    "matched_keywords": list(matched),
                    "match_count": len(matched),
                    "term_keywords_count": len(term_keywords)
                }
            ))
        
        return results
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text."""
        # Normalize
        text = text.lower()
        
        # Tokenize (handles both English and Chinese)
        # English words
        words = re.findall(r'\b[a-z]{2,}\b', text)
        
        # Chinese characters (as individual tokens for matching)
        chinese = re.findall(r'[\u4e00-\u9fff]+', text)
        
        # Filter stopwords
        keywords = set()
        for word in words:
            if word not in self.stopwords and len(word) > 2:
                keywords.add(word)
        
        # Add Chinese terms
        for term in chinese:
            if len(term) >= 2:
                keywords.add(term)
        
        return keywords
    
    def _calculate_score(
        self,
        term: str,
        term_keywords: Set[str],
        candidate_text: str
    ) -> float:
        """Calculate relevance score based on keyword matching."""
        
        if not term_keywords:
            return 0.0
        
        candidate_text_lower = candidate_text.lower()
        
        # Direct term match (highest weight)
        term_lower = term.lower()
        direct_match = 1.0 if term_lower in candidate_text_lower else 0.0
        
        # Keyword overlap
        candidate_keywords = self._extract_keywords(candidate_text)
        
        if not candidate_keywords:
            overlap_score = 0.0
        else:
            matched = term_keywords & candidate_keywords
            # Jaccard similarity
            union = term_keywords | candidate_keywords
            overlap_score = len(matched) / len(union) if union else 0.0
        
        # Keyword frequency in candidate
        keyword_freq_score = 0.0
        for kw in term_keywords:
            count = candidate_text_lower.count(kw)
            if count > 0:
                keyword_freq_score += min(count * 0.1, 0.3)
        keyword_freq_score = min(keyword_freq_score, 1.0)
        
        # Fuzzy matching for term variants (if enabled)
        fuzzy_score = 0.0
        if self.use_fuzzy:
            fuzzy_score = self._fuzzy_match_score(term, candidate_text)
        
        # Weighted combination
        final_score = (
            direct_match * 0.4 +
            overlap_score * 0.3 +
            keyword_freq_score * 0.2 +
            fuzzy_score * 0.1
        )
        
        return min(final_score, 1.0)
    
    def _fuzzy_match_score(self, term: str, text: str) -> float:
        """Calculate fuzzy match score for term variants."""
        term_lower = term.lower()
        text_lower = text.lower()
        
        # Check for common variants
        variants = self._generate_variants(term_lower)
        
        score = 0.0
        for variant in variants:
            if variant in text_lower:
                score = max(score, 0.8)
                break
        
        return score
    
    def _generate_variants(self, term: str) -> List[str]:
        """Generate common term variants."""
        variants = [term]
        
        # Singular/plural
        if term.endswith('s'):
            variants.append(term[:-1])
        else:
            variants.append(term + 's')
        
        # -tion/-ting variants
        if term.endswith('tion'):
            variants.append(term[:-4] + 'ting')
            variants.append(term[:-4] + 't')
        elif term.endswith('ting'):
            variants.append(term[:-4] + 'tion')
        
        # -ary/-ory variants
        if term.endswith('ary'):
            variants.append(term[:-3] + 'ory')
        
        # Space/hyphen variants
        if ' ' in term:
            variants.append(term.replace(' ', '-'))
            variants.append(term.replace(' ', ''))
        
        return variants

"""
Layer 2: Paragraph Alignment Module
Aligns paragraphs between PBOC and Fed reports using semantic similarity.

Supports:
- Sentence-BERT multilingual semantic similarity
- Topic-based alignment
- Keyword matching fallback

Usage:
    from alignment import PolicyAligner
    
    aligner = PolicyAligner()
    alignments = aligner.align_reports(pboc_paragraphs, fed_paragraphs)
"""

import os
import re
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import numpy as np

# Try to import Sentence-BERT
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")

# Import local models
try:
    from .models import (
        PolicyParagraph, PolicyAlignment, AlignmentMethod,
        POLICY_TOPICS, get_topic_by_keywords
    )
except ImportError:
    from models import (
        PolicyParagraph, PolicyAlignment, AlignmentMethod,
        POLICY_TOPICS, get_topic_by_keywords
    )


@dataclass
class AlignmentResult:
    """Result of aligning two sets of paragraphs."""
    success: bool
    alignments: List[PolicyAlignment]
    source_count: int
    target_count: int
    method: AlignmentMethod
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "total_alignments": len(self.alignments),
            "source_paragraphs": self.source_count,
            "target_paragraphs": self.target_count,
            "method": self.method.value,
            "alignments": [a.to_dict() for a in self.alignments],
            "error": self.error
        }


class PolicyAligner:
    """
    Aligns paragraphs between policy reports from different sources.
    Uses semantic similarity and topic matching.
    """
    
    # Default model for multilingual semantic similarity
    DEFAULT_MODEL = "paraphrase-multilingual-mpnet-base-v2"
    
    # Alternative lighter models
    ALTERNATIVE_MODELS = [
        "distiluse-base-multilingual-cased-v2",  # Faster, slightly less accurate
        "paraphrase-multilingual-MiniLM-L12-v2",  # Good balance
    ]
    
    def __init__(
        self,
        model_name: str = None,
        cache_dir: str = None,
        device: str = None
    ):
        """
        Initialize the aligner.
        
        Args:
            model_name: Sentence-BERT model name (default: multilingual mpnet)
            cache_dir: Directory to cache model and embeddings
            device: Device to run model on ('cpu', 'cuda', 'mps')
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./embedding_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        self._model = None
    
    def _load_model(self):
        """Load Sentence-BERT model (lazy loading)."""
        if self._model is None:
            if not SBERT_AVAILABLE:
                raise RuntimeError(
                    "sentence-transformers not installed.\n"
                    "Install with: pip install sentence-transformers\n"
                    "Note: Requires PyTorch"
                )
            
            print(f"Loading Sentence-BERT model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            print("Model loaded.")
    
    def compute_embeddings(
        self,
        texts: List[str],
        cache_key: str = None,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Compute sentence embeddings for texts.
        
        Args:
            texts: List of text strings
            cache_key: Optional key to cache embeddings
            show_progress: Show progress bar
            
        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        # Check cache
        if cache_key:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                print(f"Loading embeddings from cache: {cache_key}")
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        
        self._load_model()
        
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
            batch_size=32
        )
        
        # Save to cache
        if cache_key:
            with open(cache_file, 'wb') as f:
                pickle.dump(embeddings, f)
        
        return embeddings
    
    def compute_similarity_matrix(
        self,
        source_embeddings: np.ndarray,
        target_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity matrix between two sets of embeddings.
        
        Args:
            source_embeddings: Embeddings of source paragraphs
            target_embeddings: Embeddings of target paragraphs
            
        Returns:
            Similarity matrix (n_source, n_target)
        """
        # Normalize embeddings
        source_norm = source_embeddings / np.linalg.norm(source_embeddings, axis=1, keepdims=True)
        target_norm = target_embeddings / np.linalg.norm(target_embeddings, axis=1, keepdims=True)
        
        # Compute cosine similarity
        return np.dot(source_norm, target_norm.T)
    
    def align_paragraphs_sbert(
        self,
        source_paragraphs: List[PolicyParagraph],
        target_paragraphs: List[PolicyParagraph],
        threshold: float = 0.5,
        top_k: int = 3,
        source_cache_key: str = None,
        target_cache_key: str = None
    ) -> List[PolicyAlignment]:
        """
        Align paragraphs using Sentence-BERT semantic similarity.
        
        Args:
            source_paragraphs: Source document paragraphs (e.g., PBOC)
            target_paragraphs: Target document paragraphs (e.g., Fed)
            threshold: Minimum similarity score to consider a match
            top_k: Maximum matches per source paragraph
            source_cache_key: Cache key for source embeddings
            target_cache_key: Cache key for target embeddings
            
        Returns:
            List of PolicyAlignment objects
        """
        source_texts = [p.paragraph_text for p in source_paragraphs]
        target_texts = [p.paragraph_text for p in target_paragraphs]
        
        # Compute embeddings
        source_embeddings = self.compute_embeddings(source_texts, source_cache_key)
        target_embeddings = self.compute_embeddings(target_texts, target_cache_key)
        
        # Compute similarity matrix
        similarity_matrix = self.compute_similarity_matrix(source_embeddings, target_embeddings)
        
        # Find alignments
        alignments = []
        for i, source_para in enumerate(source_paragraphs):
            similarities = similarity_matrix[i]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            for j in top_indices:
                score = float(similarities[j])
                if score >= threshold:
                    target_para = target_paragraphs[j]
                    
                    # Determine shared topic
                    shared_topic = None
                    if source_para.topic and source_para.topic == target_para.topic:
                        shared_topic = source_para.topic
                    elif source_para.topic:
                        shared_topic = source_para.topic
                    elif target_para.topic:
                        shared_topic = target_para.topic
                    
                    alignment = PolicyAlignment(
                        source_paragraph_id=source_para.id or i,
                        target_paragraph_id=target_para.id or int(j),
                        similarity_score=score,
                        alignment_method=AlignmentMethod.SENTENCE_BERT,
                        topic=shared_topic,
                        source_text=source_para.paragraph_text,
                        target_text=target_para.paragraph_text
                    )
                    alignments.append(alignment)
        
        # Sort by similarity score
        alignments.sort(key=lambda x: x.similarity_score, reverse=True)
        return alignments
    
    def align_paragraphs_topic(
        self,
        source_paragraphs: List[PolicyParagraph],
        target_paragraphs: List[PolicyParagraph],
        topic: str = None
    ) -> List[PolicyAlignment]:
        """
        Align paragraphs by matching topics.
        Faster than SBERT but less precise.
        
        Args:
            source_paragraphs: Source document paragraphs
            target_paragraphs: Target document paragraphs
            topic: Optional specific topic to filter
            
        Returns:
            List of PolicyAlignment objects
        """
        alignments = []
        
        # Group paragraphs by topic
        source_by_topic: Dict[str, List[PolicyParagraph]] = {}
        for p in source_paragraphs:
            if p.topic:
                if p.topic not in source_by_topic:
                    source_by_topic[p.topic] = []
                source_by_topic[p.topic].append(p)
        
        target_by_topic: Dict[str, List[PolicyParagraph]] = {}
        for p in target_paragraphs:
            if p.topic:
                if p.topic not in target_by_topic:
                    target_by_topic[p.topic] = []
                target_by_topic[p.topic].append(p)
        
        # Match paragraphs with same topic
        for topic_key in source_by_topic:
            if topic and topic_key != topic:
                continue
            
            if topic_key not in target_by_topic:
                continue
            
            source_list = source_by_topic[topic_key]
            target_list = target_by_topic[topic_key]
            
            # Create pairwise alignments
            for source_para in source_list:
                for target_para in target_list:
                    # Basic keyword overlap score
                    score = self._compute_keyword_overlap(
                        source_para.paragraph_text,
                        target_para.paragraph_text,
                        topic_key
                    )
                    
                    if score > 0.3:  # Minimum overlap threshold
                        alignment = PolicyAlignment(
                            source_paragraph_id=source_para.id or source_para.paragraph_index,
                            target_paragraph_id=target_para.id or target_para.paragraph_index,
                            similarity_score=score,
                            alignment_method=AlignmentMethod.TOPIC_CLUSTERING,
                            topic=topic_key,
                            source_text=source_para.paragraph_text,
                            target_text=target_para.paragraph_text
                        )
                        alignments.append(alignment)
        
        # Sort by similarity score
        alignments.sort(key=lambda x: x.similarity_score, reverse=True)
        return alignments
    
    def _compute_keyword_overlap(
        self,
        source_text: str,
        target_text: str,
        topic: str
    ) -> float:
        """
        Compute keyword overlap score between two texts for a given topic.
        
        Args:
            source_text: Source paragraph text
            target_text: Target paragraph text
            topic: Topic key from POLICY_TOPICS
            
        Returns:
            Overlap score (0-1)
        """
        if topic not in POLICY_TOPICS:
            return 0.0
        
        topic_info = POLICY_TOPICS[topic]
        zh_keywords = set(kw.lower() for kw in topic_info.get("zh_keywords", []))
        en_keywords = set(kw.lower() for kw in topic_info.get("en_keywords", []))
        all_keywords = zh_keywords | en_keywords
        
        source_lower = source_text.lower()
        target_lower = target_text.lower()
        
        source_matches = sum(1 for kw in all_keywords if kw in source_lower)
        target_matches = sum(1 for kw in all_keywords if kw in target_lower)
        
        if source_matches == 0 or target_matches == 0:
            return 0.0
        
        # Geometric mean of match ratios
        source_ratio = source_matches / len(all_keywords)
        target_ratio = target_matches / len(all_keywords)
        
        return (source_ratio * target_ratio) ** 0.5
    
    def align_reports(
        self,
        source_paragraphs: List[PolicyParagraph],
        target_paragraphs: List[PolicyParagraph],
        method: str = "auto",
        threshold: float = 0.5,
        top_k: int = 3,
        topic_filter: str = None
    ) -> AlignmentResult:
        """
        Main method to align two sets of paragraphs.
        
        Args:
            source_paragraphs: Source document paragraphs (e.g., PBOC)
            target_paragraphs: Target document paragraphs (e.g., Fed)
            method: Alignment method ("sbert", "topic", "auto")
            threshold: Minimum similarity for SBERT
            top_k: Max matches per source paragraph for SBERT
            topic_filter: Only align paragraphs with this topic
            
        Returns:
            AlignmentResult with all alignments
        """
        if not source_paragraphs or not target_paragraphs:
            return AlignmentResult(
                success=False,
                alignments=[],
                source_count=len(source_paragraphs),
                target_count=len(target_paragraphs),
                method=AlignmentMethod.SENTENCE_BERT,
                error="Empty paragraph lists"
            )
        
        # Filter by topic if specified
        if topic_filter:
            source_paragraphs = [p for p in source_paragraphs if p.topic == topic_filter]
            target_paragraphs = [p for p in target_paragraphs if p.topic == topic_filter]
        
        # Choose method
        if method == "auto":
            # Use SBERT if available, otherwise fall back to topic matching
            method = "sbert" if SBERT_AVAILABLE else "topic"
        
        try:
            if method == "sbert":
                alignments = self.align_paragraphs_sbert(
                    source_paragraphs,
                    target_paragraphs,
                    threshold=threshold,
                    top_k=top_k
                )
                used_method = AlignmentMethod.SENTENCE_BERT
            else:
                alignments = self.align_paragraphs_topic(
                    source_paragraphs,
                    target_paragraphs,
                    topic=topic_filter
                )
                used_method = AlignmentMethod.TOPIC_CLUSTERING
            
            return AlignmentResult(
                success=True,
                alignments=alignments,
                source_count=len(source_paragraphs),
                target_count=len(target_paragraphs),
                method=used_method
            )
            
        except Exception as e:
            return AlignmentResult(
                success=False,
                alignments=[],
                source_count=len(source_paragraphs),
                target_count=len(target_paragraphs),
                method=AlignmentMethod.SENTENCE_BERT,
                error=str(e)
            )
    
    def find_term_alignments(
        self,
        alignments: List[PolicyAlignment],
        term: str,
        term_id: int = None
    ) -> List[PolicyAlignment]:
        """
        Filter alignments that mention a specific term.
        
        Args:
            alignments: List of alignments to filter
            term: Term to search for (e.g., "Inflation")
            term_id: Optional term ID from Layer 1
            
        Returns:
            Filtered list of alignments
        """
        term_lower = term.lower()
        
        # Chinese translation mappings for common terms
        term_translations = {
            "inflation": ["通胀", "通货膨胀", "物价"],
            "deflation": ["通缩", "通货紧缩"],
            "interest rate": ["利率", "基准利率"],
            "gdp": ["GDP", "国内生产总值", "经济增长"],
            "unemployment": ["失业", "失业率"],
            "employment": ["就业", "就业率"],
            "recession": ["衰退", "经济衰退"],
        }
        
        search_terms = [term_lower]
        if term_lower in term_translations:
            search_terms.extend(term_translations[term_lower])
        
        filtered = []
        for alignment in alignments:
            source_text = (alignment.source_text or "").lower()
            target_text = (alignment.target_text or "").lower()
            
            if any(t in source_text or t in target_text for t in search_terms):
                if term_id:
                    alignment.term_id = term_id
                filtered.append(alignment)
        
        return filtered


class FallbackAligner:
    """
    Simple keyword-based aligner that works without external dependencies.
    Used when Sentence-BERT is not available.
    """
    
    def __init__(self):
        pass
    
    def align(
        self,
        source_paragraphs: List[PolicyParagraph],
        target_paragraphs: List[PolicyParagraph],
        threshold: float = 0.3
    ) -> List[PolicyAlignment]:
        """
        Align paragraphs using keyword overlap.
        """
        alignments = []
        
        for i, source in enumerate(source_paragraphs):
            for j, target in enumerate(target_paragraphs):
                # Only align paragraphs with matching topics
                if source.topic and target.topic and source.topic == target.topic:
                    score = self._jaccard_similarity(
                        source.paragraph_text,
                        target.paragraph_text
                    )
                    
                    if score >= threshold:
                        alignments.append(PolicyAlignment(
                            source_paragraph_id=source.id or i,
                            target_paragraph_id=target.id or j,
                            similarity_score=score,
                            alignment_method=AlignmentMethod.KEYWORD_MATCHING,
                            topic=source.topic,
                            source_text=source.paragraph_text,
                            target_text=target.paragraph_text
                        ))
        
        alignments.sort(key=lambda x: x.similarity_score, reverse=True)
        return alignments
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two texts."""
        # Tokenize (simple word splitting)
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union


# Sample usage and testing
if __name__ == "__main__":
    from pdf_parser import SAMPLE_PBOC_TEXT, SAMPLE_FED_TEXT, parse_text_report
    
    print("Testing Alignment Module")
    print("=" * 60)
    
    # Parse sample texts
    pboc_result = parse_text_report(SAMPLE_PBOC_TEXT, source="pboc")
    fed_result = parse_text_report(SAMPLE_FED_TEXT, source="fed")
    
    pboc_paragraphs = pboc_result.paragraphs
    fed_paragraphs = fed_result.paragraphs
    
    print(f"\nPBOC paragraphs: {len(pboc_paragraphs)}")
    for p in pboc_paragraphs:
        print(f"  [{p.topic or 'unknown'}] {p.paragraph_text[:40]}...")
    
    print(f"\nFed paragraphs: {len(fed_paragraphs)}")
    for p in fed_paragraphs:
        print(f"  [{p.topic or 'unknown'}] {p.paragraph_text[:40]}...")
    
    # Test alignment
    print("\n" + "=" * 60)
    print("Testing alignment...")
    
    # Try SBERT first
    aligner = PolicyAligner()
    
    try:
        result = aligner.align_reports(
            pboc_paragraphs,
            fed_paragraphs,
            method="auto",
            threshold=0.4,
            top_k=2
        )
        
        print(f"\nAlignment result: {result.success}")
        print(f"Method used: {result.method.value}")
        print(f"Total alignments: {len(result.alignments)}")
        
        for i, a in enumerate(result.alignments[:5]):
            print(f"\n  Alignment {i+1} (score: {a.similarity_score:.3f}):")
            print(f"    Topic: {a.topic or 'N/A'}")
            print(f"    PBOC: {a.source_text[:60]}...")
            print(f"    Fed:  {a.target_text[:60]}...")
            
    except Exception as e:
        print(f"SBERT alignment failed: {e}")
        print("\nFalling back to keyword-based alignment...")
        
        fallback = FallbackAligner()
        alignments = fallback.align(pboc_paragraphs, fed_paragraphs)
        
        print(f"Fallback alignments found: {len(alignments)}")
        for a in alignments[:3]:
            print(f"  [{a.topic}] Score: {a.similarity_score:.3f}")
    
    # Test term-specific filtering
    print("\n" + "=" * 60)
    print("Testing term-specific alignment (Inflation)...")
    
    if 'result' in dir() and result.success:
        inflation_alignments = aligner.find_term_alignments(
            result.alignments,
            term="inflation"
        )
        print(f"Alignments mentioning 'inflation': {len(inflation_alignments)}")
    
    print("\n" + "=" * 60)
    print("Alignment module test complete!")

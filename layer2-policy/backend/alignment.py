"""
Layer 2: Paragraph Alignment Module
Uses Sentence-BERT for semantic similarity alignment between PBOC and Fed reports

Usage:
    from alignment import align_paragraphs
    
    alignments = align_paragraphs(pboc_paragraphs, fed_paragraphs)
"""

from typing import List, Tuple, Optional
import numpy as np

# Sentence-BERT import (install with: pip install sentence-transformers)
# from sentence_transformers import SentenceTransformer


class ParagraphAligner:
    """
    Aligns paragraphs between two documents using semantic similarity.
    """
    
    def __init__(self, model_name: str = "paraphrase-multilingual-mpnet-base-v2"):
        """
        Initialize the aligner with a Sentence-BERT model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
                       For multilingual: "paraphrase-multilingual-mpnet-base-v2"
        """
        self.model_name = model_name
        self.model = None  # Lazy loading
    
    def _load_model(self):
        """Load the Sentence-BERT model if not already loaded."""
        if self.model is None:
            # TODO: Uncomment when sentence-transformers is installed
            # from sentence_transformers import SentenceTransformer
            # self.model = SentenceTransformer(self.model_name)
            raise NotImplementedError(
                "Sentence-BERT not yet configured. "
                "Install with: pip install sentence-transformers"
            )
    
    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Compute embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        self._load_model()
        return self.model.encode(texts, convert_to_numpy=True)
    
    def compute_similarity_matrix(
        self, 
        source_texts: List[str], 
        target_texts: List[str]
    ) -> np.ndarray:
        """
        Compute pairwise similarity matrix between two sets of texts.
        
        Args:
            source_texts: Source document paragraphs (e.g., PBOC)
            target_texts: Target document paragraphs (e.g., Fed)
            
        Returns:
            Similarity matrix (n_source, n_target)
        """
        source_embeddings = self.compute_embeddings(source_texts)
        target_embeddings = self.compute_embeddings(target_texts)
        
        # Cosine similarity
        source_norm = source_embeddings / np.linalg.norm(source_embeddings, axis=1, keepdims=True)
        target_norm = target_embeddings / np.linalg.norm(target_embeddings, axis=1, keepdims=True)
        
        return np.dot(source_norm, target_norm.T)
    
    def align_paragraphs(
        self,
        source_texts: List[str],
        target_texts: List[str],
        threshold: float = 0.6,
        top_k: int = 3
    ) -> List[dict]:
        """
        Find aligned paragraphs between source and target documents.
        
        Args:
            source_texts: Source document paragraphs
            target_texts: Target document paragraphs
            threshold: Minimum similarity score to consider a match
            top_k: Maximum number of matches per source paragraph
            
        Returns:
            List of alignment dictionaries with source_idx, target_idx, similarity
        """
        similarity_matrix = self.compute_similarity_matrix(source_texts, target_texts)
        
        alignments = []
        for i, source_text in enumerate(source_texts):
            # Get top-k most similar target paragraphs
            similarities = similarity_matrix[i]
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            for j in top_indices:
                score = float(similarities[j])
                if score >= threshold:
                    alignments.append({
                        "source_idx": i,
                        "source_text": source_text[:200] + "..." if len(source_text) > 200 else source_text,
                        "target_idx": int(j),
                        "target_text": target_texts[j][:200] + "..." if len(target_texts[j]) > 200 else target_texts[j],
                        "similarity": round(score, 4)
                    })
        
        # Sort by similarity score
        alignments.sort(key=lambda x: x["similarity"], reverse=True)
        return alignments


def align_pboc_fed(
    pboc_paragraphs: List[str],
    fed_paragraphs: List[str],
    topic_filter: Optional[str] = None
) -> List[dict]:
    """
    Convenience function to align PBOC and Fed report paragraphs.
    
    Args:
        pboc_paragraphs: List of PBOC report paragraphs
        fed_paragraphs: List of Fed report paragraphs
        topic_filter: Optional topic to filter (e.g., "inflation", "employment")
        
    Returns:
        List of alignment results
    """
    aligner = ParagraphAligner()
    
    # Filter by topic if specified
    if topic_filter:
        # TODO: Implement topic filtering
        # Could use keyword matching or topic classification
        pass
    
    return aligner.align_paragraphs(pboc_paragraphs, fed_paragraphs)


# Topic keywords for filtering
TOPIC_KEYWORDS = {
    "inflation": {
        "en": ["inflation", "price", "cpi", "pce", "cost of living"],
        "zh": ["通胀", "物价", "CPI", "消费价格", "生活成本"]
    },
    "employment": {
        "en": ["employment", "unemployment", "labor", "job", "workforce"],
        "zh": ["就业", "失业", "劳动力", "工作", "人力"]
    },
    "interest_rate": {
        "en": ["interest rate", "federal funds", "policy rate", "lending rate"],
        "zh": ["利率", "基准利率", "存贷款利率", "政策利率"]
    },
    "gdp": {
        "en": ["gdp", "economic growth", "output", "production"],
        "zh": ["GDP", "经济增长", "产出", "生产总值"]
    }
}


if __name__ == "__main__":
    # Test alignment
    pboc_sample = [
        "当前通胀水平保持温和，CPI同比上涨0.4%，核心CPI同比上涨0.3%。",
        "就业形势总体稳定，城镇调查失业率保持在5.0%左右。",
        "人民币汇率在合理均衡水平上保持基本稳定。"
    ]
    
    fed_sample = [
        "Prices continued to rise modestly across most districts, with inflation pressures easing.",
        "Labor market conditions remained tight, though some easing was noted in several districts.",
        "The dollar strengthened against major currencies during the period."
    ]
    
    print("Testing paragraph alignment...")
    try:
        alignments = align_pboc_fed(pboc_sample, fed_sample)
        for a in alignments:
            print(f"\nSimilarity: {a['similarity']}")
            print(f"PBOC: {a['source_text'][:50]}...")
            print(f"Fed: {a['target_text'][:50]}...")
    except NotImplementedError as e:
        print(f"Note: {e}")
        print("Once sentence-transformers is installed, alignment will work.")

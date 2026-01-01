"""
Vector Similarity Aligner

Uses Sentence-BERT embeddings to calculate cosine similarity
between term definitions and candidate texts.
"""

import asyncio
from typing import List, Dict, Any, Optional
import numpy as np

from .base_aligner import BaseAligner, AlignmentResult


class VectorAligner(BaseAligner):
    """
    Aligns candidates using vector embedding similarity.
    
    Uses multilingual Sentence-BERT models to encode texts
    and calculates cosine similarity. Fast and free but
    may miss semantic equivalents with different wording.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.model_name = config.get(
            "model", 
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
        self.device = config.get("device", "cpu")
        self.batch_size = config.get("batch_size", 32)
        
        self._model = None
        self._initialized = False
    
    def _init_model(self):
        """Initialize the Sentence-BERT model."""
        if self._initialized:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            print(f"[INFO] Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._initialized = True
            print(f"[INFO] VectorAligner initialized on {self.device}")
        
        except ImportError:
            print("[WARN] sentence-transformers not installed, vector alignment disabled")
            self._initialized = True
        except Exception as e:
            print(f"[WARN] Failed to load embedding model: {e}")
            self._initialized = True
    
    async def align(
        self,
        term: str,
        term_definition: str,
        candidates: List[Dict[str, Any]],
        layer: str
    ) -> List[AlignmentResult]:
        """
        Score candidates using cosine similarity of embeddings.
        """
        self._init_model()
        
        if not self._model or not candidates:
            return []
        
        # Prepare texts
        query_text = f"{term}: {term_definition[:500]}"
        candidate_texts = []
        
        for c in candidates:
            text = c.get('text', c.get('title', ''))
            if c.get('summary'):
                text = f"{c.get('title', '')} {c.get('summary', '')}"
            candidate_texts.append(text[:500])
        
        # Encode in thread pool to avoid blocking
        results = await asyncio.to_thread(
            self._compute_similarities,
            query_text,
            candidate_texts,
            candidates
        )
        
        return results
    
    def _compute_similarities(
        self,
        query_text: str,
        candidate_texts: List[str],
        candidates: List[Dict[str, Any]]
    ) -> List[AlignmentResult]:
        """Compute cosine similarities between query and candidates."""
        
        try:
            # Encode query
            query_embedding = self._model.encode(
                query_text, 
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Encode candidates in batches
            candidate_embeddings = self._model.encode(
                candidate_texts,
                convert_to_numpy=True,
                batch_size=self.batch_size,
                show_progress_bar=False
            )
            
            # Calculate cosine similarities
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            candidate_norms = candidate_embeddings / np.linalg.norm(
                candidate_embeddings, axis=1, keepdims=True
            )
            
            # Dot product = cosine similarity for normalized vectors
            similarities = np.dot(candidate_norms, query_norm)
            
            # Create results
            results = []
            for i, (sim, candidate) in enumerate(zip(similarities, candidates)):
                score = float(sim)
                results.append(AlignmentResult(
                    candidate_id=candidate['id'],
                    score=max(0, min(1, score)),  # Clamp to [0, 1]
                    method="vector_similarity",
                    metadata={"raw_similarity": score}
                ))
            
            return results
        
        except Exception as e:
            print(f"[WARN] Vector similarity error: {e}")
            return []

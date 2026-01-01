"""
Alignment Strategy Plugins

Each aligner implements a specific alignment method:
- LLMAligner: Semantic judgment using Gemini/GPT-4
- VectorAligner: Sentence-BERT cosine similarity
- RuleAligner: Keyword + TF-IDF matching
- HybridAligner: Weighted ensemble of above methods
"""

from .base_aligner import BaseAligner, AlignmentResult
from .llm_aligner import LLMAligner
from .vector_aligner import VectorAligner
from .rule_aligner import RuleAligner
from .hybrid_aligner import HybridAligner

__all__ = [
    "BaseAligner",
    "AlignmentResult",
    "LLMAligner",
    "VectorAligner",
    "RuleAligner",
    "HybridAligner",
]

"""
Base Aligner Interface

Abstract base class for all alignment strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AlignmentResult:
    """Result from an alignment operation."""
    candidate_id: int
    score: float
    method: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "score": self.score,
            "method": self.method,
            "reason": self.reason,
            "metadata": self.metadata
        }


class BaseAligner(ABC):
    """
    Abstract base class for alignment strategies.
    
    Each aligner must implement the `align` method that scores
    candidates based on their relevance to a term.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize aligner with configuration.
        
        Args:
            config: Strategy-specific configuration from YAML
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.threshold = config.get("threshold", 0.5)
        self.weight = config.get("weight", 0.25)
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def align(
        self,
        term: str,
        term_definition: str,
        candidates: List[Dict[str, Any]],
        layer: str  # "policy" or "sentiment"
    ) -> List[AlignmentResult]:
        """
        Score candidates based on relevance to term.
        
        Args:
            term: The term being aligned
            term_definition: English definition of the term
            candidates: List of candidate texts with 'id' and 'text' keys
            layer: Which layer the candidates are from
            
        Returns:
            List of AlignmentResult with scores for each candidate
        """
        pass
    
    def filter_by_threshold(self, results: List[AlignmentResult]) -> List[AlignmentResult]:
        """Filter results by the configured threshold."""
        return [r for r in results if r.score >= self.threshold]
    
    def is_enabled(self) -> bool:
        """Check if this aligner is enabled."""
        return self.enabled
    
    def get_weight(self) -> float:
        """Get the weight for ensemble scoring."""
        return self.weight

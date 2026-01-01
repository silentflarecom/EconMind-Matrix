"""
Hybrid Ensemble Aligner

Combines results from multiple alignment strategies using
weighted voting to produce final alignment scores.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from .base_aligner import BaseAligner, AlignmentResult
from .llm_aligner import LLMAligner
from .vector_aligner import VectorAligner
from .rule_aligner import RuleAligner


class HybridAligner(BaseAligner):
    """
    Combines multiple alignment strategies using weighted voting.
    
    Strategy weights are configurable. Provides both individual
    method scores and a final ensemble score.
    """
    
    def __init__(self, config: Dict[str, Any], aligners: Dict[str, BaseAligner] = None):
        super().__init__(config)
        
        self.aligners = aligners or {}
        self.ensemble_bonus = config.get("ensemble_bonus", 0.05)
        self.min_agreement = config.get("min_agreement", 2)  # Min methods that must agree
    
    def set_aligners(self, aligners: Dict[str, BaseAligner]):
        """Set the child aligners to combine."""
        self.aligners = aligners
    
    async def align(
        self,
        term: str,
        term_definition: str,
        candidates: List[Dict[str, Any]],
        layer: str
    ) -> List[AlignmentResult]:
        """
        Run all enabled aligners and combine results.
        """
        if not candidates or not self.aligners:
            return []
        
        # Collect results from all aligners
        all_results: Dict[str, List[AlignmentResult]] = {}
        
        for name, aligner in self.aligners.items():
            if aligner.is_enabled():
                results = await aligner.align(term, term_definition, candidates, layer)
                all_results[name] = results
        
        # Combine results
        return self._combine_results(all_results, candidates)
    
    def _combine_results(
        self,
        all_results: Dict[str, List[AlignmentResult]],
        candidates: List[Dict[str, Any]]
    ) -> List[AlignmentResult]:
        """Combine results from multiple aligners using weighted voting."""
        
        # Index results by candidate ID
        scores_by_candidate: Dict[int, Dict[str, float]] = defaultdict(dict)
        reasons_by_candidate: Dict[int, List[str]] = defaultdict(list)
        
        for method_name, results in all_results.items():
            aligner = self.aligners.get(method_name)
            weight = aligner.get_weight() if aligner else 0.25
            
            for result in results:
                cid = result.candidate_id
                scores_by_candidate[cid][method_name] = result.score
                if result.reason:
                    reasons_by_candidate[cid].append(f"{method_name}: {result.reason}")
        
        # Calculate ensemble scores
        combined_results = []
        
        for candidate in candidates:
            cid = candidate['id']
            method_scores = scores_by_candidate.get(cid, {})
            
            if not method_scores:
                # No aligners returned results for this candidate
                combined_results.append(AlignmentResult(
                    candidate_id=cid,
                    score=0.0,
                    method="hybrid_ensemble",
                    metadata={"individual_scores": {}}
                ))
                continue
            
            # Weighted average
            total_weight = 0.0
            weighted_sum = 0.0
            
            for method_name, score in method_scores.items():
                aligner = self.aligners.get(method_name)
                weight = aligner.get_weight() if aligner else 0.25
                weighted_sum += score * weight
                total_weight += weight
            
            base_score = weighted_sum / total_weight if total_weight > 0 else 0.0
            
            # Ensemble bonus if multiple methods agree
            agreeing_methods = sum(
                1 for s in method_scores.values() 
                if s >= self.threshold
            )
            
            bonus = self.ensemble_bonus if agreeing_methods >= self.min_agreement else 0.0
            final_score = min(base_score + bonus, 1.0)
            
            combined_results.append(AlignmentResult(
                candidate_id=cid,
                score=final_score,
                method="hybrid_ensemble",
                reason="; ".join(reasons_by_candidate.get(cid, []))[:200] or None,
                metadata={
                    "individual_scores": method_scores,
                    "agreeing_methods": agreeing_methods,
                    "ensemble_bonus_applied": bonus > 0
                }
            ))
        
        return combined_results
    
    @staticmethod
    def create_default_ensemble(config: Dict[str, Any]) -> "HybridAligner":
        """
        Factory method to create a HybridAligner with default child aligners.
        
        Args:
            config: Full alignment configuration dict
        """
        strategies = config.get("alignment_strategies", {})
        
        aligners = {}
        
        # Initialize LLM aligner
        llm_config = strategies.get("llm_semantic", {"enabled": False})
        if llm_config.get("enabled", False):
            aligners["llm"] = LLMAligner(llm_config)
        
        # Initialize Vector aligner
        vector_config = strategies.get("vector_similarity", {"enabled": True})
        if vector_config.get("enabled", True):
            aligners["vector"] = VectorAligner(vector_config)
        
        # Initialize Rule aligner
        rule_config = strategies.get("keyword_matching", {"enabled": True})
        if rule_config.get("enabled", True):
            aligners["rule"] = RuleAligner(rule_config)
        
        # Create hybrid aligner
        hybrid_config = strategies.get("hybrid", {
            "enabled": True,
            "threshold": 0.65,
            "weight": 1.0,
            "ensemble_bonus": 0.05,
            "min_agreement": 2
        })
        
        hybrid = HybridAligner(hybrid_config)
        hybrid.set_aligners(aligners)
        
        return hybrid

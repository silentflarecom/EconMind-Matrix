"""
Alignment Engine - Core Orchestrator

The main engine that coordinates data loading, alignment strategies,
and Knowledge Cell generation.
"""

import yaml
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from .data_loader import DataLoader, Layer1Term, Layer2Paragraph, Layer3Article
from .knowledge_cell import (
    KnowledgeCell, TermDefinition, PolicyEvidence, SentimentEvidence,
    AlignmentScores, ReportMetadata, SentimentInfo, QualityMetrics, CellMetadata,
    create_empty_cell
)
from .aligners import HybridAligner, AlignmentResult


class AlignmentEngine:
    """
    Core alignment engine that orchestrates the entire alignment pipeline.
    
    Workflow:
    1. Load terms from Layer 1
    2. For each term, search Layer 2/3 for candidates
    3. Run alignment strategies on candidates
    4. Build Knowledge Cells with aligned evidence
    5. Export results and quality report
    """
    
    def __init__(self, config_path: str = None, config: Dict[str, Any] = None):
        """
        Initialize the alignment engine.
        
        Args:
            config_path: Path to YAML configuration file
            config: Direct configuration dict (overrides config_path)
        """
        if config:
            self.config = config
        elif config_path:
            self.config = self._load_config(config_path)
        else:
            self.config = self._default_config()
        
        # Initialize components
        self.data_loader = DataLoader()
        self.aligner = HybridAligner.create_default_ensemble(self.config)
        
        # Runtime state
        self.layer2_paragraphs: List[Layer2Paragraph] = []
        self.layer3_articles: List[Layer3Article] = []
        self.results: List[KnowledgeCell] = []
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "alignment_strategies": {
                "llm_semantic": {
                    "enabled": False,  # Disabled by default (requires API key)
                    "provider": "gemini",
                    "model": "gemini-1.5-flash",
                    "threshold": 0.70,
                    "weight": 0.50
                },
                "vector_similarity": {
                    "enabled": True,
                    "model": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
                    "device": "cpu",
                    "threshold": 0.65,
                    "weight": 0.30
                },
                "keyword_matching": {
                    "enabled": True,
                    "use_fuzzy": True,
                    "threshold": 0.60,
                    "weight": 0.20
                }
            },
            "global": {
                "min_final_score": 0.65,
                "max_policy_evidence": 15,
                "max_sentiment_evidence": 30,
                "sentiment_time_window_days": 90
            },
            "languages": {
                "priority": ["en", "zh", "ja", "ko", "fr", "de", "es", "ru"]
            },
            "output": {
                "format": "jsonl",
                "output_dir": "dataset",
                "include_metadata": True
            }
        }
    
    async def load_source_data(self):
        """Pre-load Layer 2 and Layer 3 data."""
        print("[INFO] Loading source data...")
        
        # Get statistics first
        stats = await self.data_loader.get_statistics()
        print(f"  Layer 1: {stats['layer1']['completed_terms']} terms")
        print(f"  Layer 2: {stats['layer2']['total_paragraphs']} paragraphs")
        print(f"  Layer 3: {stats['layer3']['total_articles']} articles")
        
        # Load Layer 2
        self.layer2_paragraphs = await self.data_loader.load_layer2_paragraphs()
        print(f"[INFO] Loaded {len(self.layer2_paragraphs)} policy paragraphs")
        
        # Load Layer 3
        days = self.config.get("global", {}).get("sentiment_time_window_days", 90)
        self.layer3_articles = await self.data_loader.load_layer3_articles(days_back=days)
        print(f"[INFO] Loaded {len(self.layer3_articles)} news articles")
    
    async def align_term(self, term: Layer1Term) -> KnowledgeCell:
        """
        Align a single term with Layer 2 and Layer 3 data.
        
        Args:
            term: Layer1Term object
            
        Returns:
            Complete KnowledgeCell with aligned evidence
        """
        # Create base cell
        cell = create_empty_cell(term.id, term.term)
        
        # Set concept ID (use Wikidata QID if available)
        if term.wikidata_qid:
            cell.concept_id = term.wikidata_qid
        
        # Extract definitions
        for lang, data in term.translations.items():
            if data.get('summary'):
                cell.definitions[lang] = TermDefinition(
                    language=lang,
                    term=data.get('term', term.term),
                    summary=data['summary'],
                    url=data.get('url', ''),
                    source="Wikipedia"
                )
        
        # Get English definition for alignment
        en_def = term.translations.get('en', {}).get('summary', '')
        if not en_def and term.translations:
            # Use any available definition
            en_def = list(term.translations.values())[0].get('summary', '')
        
        # Extract term variants from all languages
        term_variants = []
        for lang, data in term.translations.items():
            if data.get('term') and data['term'] != term.term:
                term_variants.append(data['term'])
        
        # Search and align Layer 2 (Policy)
        policy_candidates = await self.data_loader.search_paragraphs_for_term(
            term.term, term_variants, limit=50
        )
        
        if policy_candidates:
            policy_evidence = await self._align_policy_candidates(
                term.term, en_def, policy_candidates
            )
            cell.policy_evidence = policy_evidence[:self.config['global']['max_policy_evidence']]
        
        # Search and align Layer 3 (Sentiment)
        sentiment_candidates = await self.data_loader.search_articles_for_term(
            term.term, term_variants, 
            days_back=self.config['global']['sentiment_time_window_days'],
            limit=100
        )
        
        if sentiment_candidates:
            sentiment_evidence = await self._align_sentiment_candidates(
                term.term, en_def, sentiment_candidates
            )
            cell.sentiment_evidence = sentiment_evidence[:self.config['global']['max_sentiment_evidence']]
        
        # Calculate quality metrics
        cell.metadata = CellMetadata(
            quality_metrics=self._calculate_quality_metrics(cell)
        )
        
        return cell
    
    async def _align_policy_candidates(
        self,
        term: str,
        definition: str,
        candidates: List[Layer2Paragraph]
    ) -> List[PolicyEvidence]:
        """Align policy paragraph candidates."""
        
        # Prepare candidates for aligner
        aligner_input = [
            {"id": p.id, "text": p.text}
            for p in candidates
        ]
        
        # Run alignment
        results = await self.aligner.align(term, definition, aligner_input, "policy")
        
        # Filter by threshold
        threshold = self.config['global']['min_final_score']
        results = [r for r in results if r.score >= threshold]
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Build evidence objects
        evidence_list = []
        candidate_map = {p.id: p for p in candidates}
        
        for result in results:
            para = candidate_map.get(result.candidate_id)
            if not para:
                continue
            
            # Extract individual scores
            individual = result.metadata.get("individual_scores", {})
            
            evidence_list.append(PolicyEvidence(
                source=para.source,
                paragraph_id=para.id,
                text=para.text,
                topic=para.topic,
                alignment_scores=AlignmentScores(
                    llm=individual.get("llm"),
                    vector=individual.get("vector"),
                    rule=individual.get("rule"),
                    final=result.score
                ),
                alignment_method=result.method,
                report_metadata=ReportMetadata(
                    title=para.report_title or "Unknown",
                    date=para.report_date or "Unknown",
                    section=para.section_title
                )
            ))
        
        return evidence_list
    
    async def _align_sentiment_candidates(
        self,
        term: str,
        definition: str,
        candidates: List[Layer3Article]
    ) -> List[SentimentEvidence]:
        """Align news article candidates."""
        
        # Prepare candidates
        aligner_input = [
            {
                "id": a.id, 
                "text": a.title,
                "title": a.title,
                "summary": a.summary
            }
            for a in candidates
        ]
        
        # Run alignment
        results = await self.aligner.align(term, definition, aligner_input, "sentiment")
        
        # Filter and sort
        threshold = self.config['global']['min_final_score']
        results = [r for r in results if r.score >= threshold]
        results.sort(key=lambda r: r.score, reverse=True)
        
        # Build evidence objects
        evidence_list = []
        candidate_map = {a.id: a for a in candidates}
        
        for result in results:
            article = candidate_map.get(result.candidate_id)
            if not article:
                continue
            
            individual = result.metadata.get("individual_scores", {})
            
            evidence_list.append(SentimentEvidence(
                article_id=article.id,
                title=article.title,
                source=article.source,
                url=article.url,
                published_date=article.published_date or "Unknown",
                sentiment=SentimentInfo(
                    label=article.sentiment_label or "unknown",
                    confidence=article.sentiment_confidence or 0.0,
                    annotator="layer3"
                ),
                alignment_scores=AlignmentScores(
                    llm=individual.get("llm"),
                    vector=individual.get("vector"),
                    rule=individual.get("rule"),
                    final=result.score
                )
            ))
        
        return evidence_list
    
    def _calculate_quality_metrics(self, cell: KnowledgeCell) -> QualityMetrics:
        """Calculate quality metrics for a Knowledge Cell."""
        
        policy_scores = [e.alignment_scores.final for e in cell.policy_evidence]
        sentiment_scores = [e.alignment_scores.final for e in cell.sentiment_evidence]
        
        avg_policy = sum(policy_scores) / len(policy_scores) if policy_scores else 0.0
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # Overall score: weighted by evidence density
        if policy_scores or sentiment_scores:
            overall = (
                avg_policy * 0.5 + avg_sentiment * 0.5
            ) if policy_scores and sentiment_scores else (
                avg_policy if policy_scores else avg_sentiment
            )
        else:
            overall = 0.0
        
        return QualityMetrics(
            overall_score=round(overall, 3),
            language_coverage=len(cell.definitions),
            policy_evidence_count=len(cell.policy_evidence),
            sentiment_evidence_count=len(cell.sentiment_evidence),
            avg_policy_score=round(avg_policy, 3),
            avg_sentiment_score=round(avg_sentiment, 3)
        )
    
    async def run_full_alignment(self) -> List[KnowledgeCell]:
        """
        Run alignment on all Layer 1 terms.
        
        Returns:
            List of KnowledgeCells
        """
        print("=" * 60)
        print("Layer 4 Alignment Engine v4.0.0")
        print("=" * 60)
        
        # Load source data
        await self.load_source_data()
        
        # Load terms
        terms = await self.data_loader.load_layer1_terms()
        print(f"\n[INFO] Starting alignment for {len(terms)} terms\n")
        
        self.results = []
        
        for i, term in enumerate(terms):
            lang_count = len(term.translations)
            print(f"[{i+1}/{len(terms)}] Aligning term: \"{term.term}\" ({lang_count} languages)")
            
            try:
                cell = await self.align_term(term)
                self.results.append(cell)
                
                # Progress output
                quality = cell.metadata.quality_metrics
                status = "✓" if quality.overall_score >= 0.65 else "○"
                print(f"  └─ {status} Policy: {quality.policy_evidence_count}, "
                      f"Sentiment: {quality.sentiment_evidence_count}, "
                      f"Score: {quality.overall_score:.2f}")
            
            except Exception as e:
                print(f"  └─ ✗ Error: {e}")
                self.results.append(create_empty_cell(term.id, term.term))
        
        print("\n" + "=" * 60)
        print("Alignment Complete!")
        print("=" * 60)
        
        # Summary
        total = len(self.results)
        with_policy = sum(1 for c in self.results if c.policy_evidence)
        with_sentiment = sum(1 for c in self.results if c.sentiment_evidence)
        avg_score = sum(c.metadata.quality_metrics.overall_score for c in self.results) / total if total else 0
        
        print(f"Total Knowledge Cells: {total}")
        print(f"With Policy Evidence: {with_policy} ({with_policy/total*100:.1f}%)")
        print(f"With Sentiment Evidence: {with_sentiment} ({with_sentiment/total*100:.1f}%)")
        print(f"Avg Quality Score: {avg_score:.2f}")
        
        return self.results
    
    def export_jsonl(self, output_path: str = None) -> str:
        """Export results to JSONL format."""
        if not output_path:
            output_dir = Path(self.config['output']['output_dir'])
            output_dir.mkdir(exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            output_path = output_dir / f"aligned_corpus_{date_str}.jsonl"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for cell in self.results:
                f.write(cell.to_jsonl_line() + '\n')
        
        print(f"\n[INFO] Exported to: {output_path}")
        return str(output_path)
    
    def generate_quality_report(self, output_path: str = None) -> str:
        """Generate a quality report in Markdown format."""
        if not output_path:
            output_dir = Path(self.config['output']['output_dir'])
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / "quality_report.md"
        
        output_path = Path(output_path)
        
        total = len(self.results)
        if total == 0:
            return ""
        
        # Calculate statistics
        scores = [c.metadata.quality_metrics.overall_score for c in self.results]
        lang_counts = [c.metadata.quality_metrics.language_coverage for c in self.results]
        policy_counts = [c.metadata.quality_metrics.policy_evidence_count for c in self.results]
        sentiment_counts = [c.metadata.quality_metrics.sentiment_evidence_count for c in self.results]
        
        avg_score = sum(scores) / total
        avg_langs = sum(lang_counts) / total
        avg_policy = sum(policy_counts) / total
        avg_sentiment = sum(sentiment_counts) / total
        
        with_policy = sum(1 for c in policy_counts if c > 0)
        with_sentiment = sum(1 for c in sentiment_counts if c > 0)
        
        # Build report
        report = f"""# Layer 4 Alignment Quality Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary Statistics

| Metric | Value |
|:---|:---:|
| Total Knowledge Cells | {total} |
| Avg Quality Score | {avg_score:.3f} |
| Avg Language Coverage | {avg_langs:.1f} |
| Cells with Policy Evidence | {with_policy} ({with_policy/total*100:.1f}%) |
| Cells with Sentiment Evidence | {with_sentiment} ({with_sentiment/total*100:.1f}%) |
| Avg Policy Evidence per Cell | {avg_policy:.1f} |
| Avg Sentiment Evidence per Cell | {avg_sentiment:.1f} |

## Top 10 Highest Quality Cells

| Rank | Term | Score | Languages | Policy | Sentiment |
|:---:|:---|:---:|:---:|:---:|:---:|
"""
        
        sorted_cells = sorted(self.results, key=lambda c: c.metadata.quality_metrics.overall_score, reverse=True)
        for i, cell in enumerate(sorted_cells[:10], 1):
            q = cell.metadata.quality_metrics
            report += f"| {i} | {cell.primary_term} | {q.overall_score:.2f} | {q.language_coverage} | {q.policy_evidence_count} | {q.sentiment_evidence_count} |\n"
        
        report += """
## Cells Requiring Manual Review (Score < 0.5)

"""
        low_score = [c for c in self.results if c.metadata.quality_metrics.overall_score < 0.5]
        if low_score:
            for cell in low_score[:10]:
                q = cell.metadata.quality_metrics
                report += f"- **{cell.primary_term}**: Score {q.overall_score:.2f}, {q.language_coverage} langs\n"
        else:
            report += "No cells with score below 0.5.\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"[INFO] Quality report saved to: {output_path}")
        return str(output_path)

"""
Quality Reporter

Generates quality assessment reports for aligned datasets.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter

from ..knowledge_cell import KnowledgeCell


class QualityReporter:
    """
    Generates quality reports for Knowledge Cells.
    
    Outputs a Markdown report with:
    - Summary statistics
    - Top quality cells
    - Cells needing review
    - Method performance analysis
    """
    
    def __init__(
        self,
        output_dir: str = "dataset",
        include_top_n: int = 10,
        include_low_score_n: int = 10
    ):
        self.output_dir = Path(output_dir)
        self.include_top_n = include_top_n
        self.include_low_score_n = include_low_score_n
    
    def generate(
        self,
        cells: List[KnowledgeCell],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate quality report.
        
        Args:
            cells: List of KnowledgeCell objects
            output_path: Optional explicit output path
            
        Returns:
            Path to the created report
        """
        if not cells:
            return ""
        
        if output_path:
            filepath = Path(output_path)
        else:
            self.output_dir.mkdir(exist_ok=True, parents=True)
            filepath = self.output_dir / "quality_report.md"
        
        filepath.parent.mkdir(exist_ok=True, parents=True)
        
        report = self._build_report(cells)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(filepath)
    
    def _build_report(self, cells: List[KnowledgeCell]) -> str:
        """Build the complete Markdown report."""
        
        stats = self._calculate_stats(cells)
        
        report = f"""# Layer 4 Alignment Quality Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Alignment Engine Version:** 4.0.0

---

## 📊 Summary Statistics

| Metric | Value |
|:---|---:|
| **Total Knowledge Cells** | {stats['total']} |
| **Average Quality Score** | {stats['avg_score']:.3f} |
| **Average Language Coverage** | {stats['avg_langs']:.1f} |
| **Cells with Policy Evidence** | {stats['with_policy']} ({stats['policy_pct']:.1f}%) |
| **Cells with Sentiment Evidence** | {stats['with_sentiment']} ({stats['sentiment_pct']:.1f}%) |
| **Average Policy Evidence per Cell** | {stats['avg_policy']:.1f} |
| **Average Sentiment Evidence per Cell** | {stats['avg_sentiment']:.1f} |

### Quality Score Distribution

| Range | Count | Percentage |
|:---|---:|---:|
| Excellent (0.9-1.0) | {stats['dist']['excellent']} | {stats['dist']['excellent']/stats['total']*100:.1f}% |
| Good (0.7-0.9) | {stats['dist']['good']} | {stats['dist']['good']/stats['total']*100:.1f}% |
| Fair (0.5-0.7) | {stats['dist']['fair']} | {stats['dist']['fair']/stats['total']*100:.1f}% |
| Poor (0.3-0.5) | {stats['dist']['poor']} | {stats['dist']['poor']/stats['total']*100:.1f}% |
| Very Poor (<0.3) | {stats['dist']['very_poor']} | {stats['dist']['very_poor']/stats['total']*100:.1f}% |

---

## 🏆 Top {self.include_top_n} Highest Quality Cells

| Rank | Term | Score | Languages | Policy | Sentiment |
|:---:|:---|:---:|:---:|:---:|:---:|
"""
        
        sorted_cells = sorted(cells, key=lambda c: c.metadata.quality_metrics.overall_score, reverse=True)
        for i, cell in enumerate(sorted_cells[:self.include_top_n], 1):
            q = cell.metadata.quality_metrics
            report += f"| {i} | {cell.primary_term} | **{q.overall_score:.2f}** | {q.language_coverage} | {q.policy_evidence_count} | {q.sentiment_evidence_count} |\n"
        
        report += f"""
---

## ⚠️ Cells Requiring Review (Score < 0.5)

"""
        
        low_score = [c for c in cells if c.metadata.quality_metrics.overall_score < 0.5]
        if low_score:
            report += "| Term | Score | Issue |\n|:---|:---:|:---|\n"
            for cell in low_score[:self.include_low_score_n]:
                q = cell.metadata.quality_metrics
                issue = self._identify_issue(cell)
                report += f"| {cell.primary_term} | {q.overall_score:.2f} | {issue} |\n"
            
            if len(low_score) > self.include_low_score_n:
                report += f"\n*...and {len(low_score) - self.include_low_score_n} more cells with low scores*\n"
        else:
            report += "✅ No cells with score below 0.5.\n"
        
        report += f"""
---

## 🌐 Language Coverage

| Language | Cells with Definition | Coverage % |
|:---|---:|---:|
"""
        lang_counts = self._count_languages(cells)
        for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            pct = count / stats['total'] * 100
            report += f"| {lang} | {count} | {pct:.1f}% |\n"
        
        report += f"""
---

## 📈 Policy Source Distribution

| Source | Paragraphs Aligned | % of Total |
|:---|---:|---:|
"""
        source_counts = self._count_policy_sources(cells)
        total_policy = sum(source_counts.values())
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / total_policy * 100 if total_policy > 0 else 0
            report += f"| {source.upper()} | {count} | {pct:.1f}% |\n"
        
        report += f"""
---

## 📰 Sentiment Distribution

| Sentiment | Articles | % of Total |
|:---|---:|---:|
"""
        sentiment_counts = self._count_sentiments(cells)
        total_sent = sum(sentiment_counts.values())
        for label, count in sorted(sentiment_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / total_sent * 100 if total_sent > 0 else 0
            emoji = "📈" if label == "bullish" else "📉" if label == "bearish" else "➖"
            report += f"| {emoji} {label} | {count} | {pct:.1f}% |\n"
        
        report += """
---

*Report generated by Layer 4 Alignment Engine*
"""
        
        return report
    
    def _calculate_stats(self, cells: List[KnowledgeCell]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total = len(cells)
        
        scores = [c.metadata.quality_metrics.overall_score for c in cells]
        lang_counts = [c.metadata.quality_metrics.language_coverage for c in cells]
        policy_counts = [c.metadata.quality_metrics.policy_evidence_count for c in cells]
        sentiment_counts = [c.metadata.quality_metrics.sentiment_evidence_count for c in cells]
        
        with_policy = sum(1 for c in policy_counts if c > 0)
        with_sentiment = sum(1 for c in sentiment_counts if c > 0)
        
        # Score distribution
        dist = {
            'excellent': sum(1 for s in scores if s >= 0.9),
            'good': sum(1 for s in scores if 0.7 <= s < 0.9),
            'fair': sum(1 for s in scores if 0.5 <= s < 0.7),
            'poor': sum(1 for s in scores if 0.3 <= s < 0.5),
            'very_poor': sum(1 for s in scores if s < 0.3)
        }
        
        return {
            'total': total,
            'avg_score': sum(scores) / total if total else 0,
            'avg_langs': sum(lang_counts) / total if total else 0,
            'avg_policy': sum(policy_counts) / total if total else 0,
            'avg_sentiment': sum(sentiment_counts) / total if total else 0,
            'with_policy': with_policy,
            'with_sentiment': with_sentiment,
            'policy_pct': with_policy / total * 100 if total else 0,
            'sentiment_pct': with_sentiment / total * 100 if total else 0,
            'dist': dist
        }
    
    def _identify_issue(self, cell: KnowledgeCell) -> str:
        """Identify why a cell has low quality."""
        q = cell.metadata.quality_metrics
        issues = []
        
        if q.language_coverage < 2:
            issues.append("Low language coverage")
        if q.policy_evidence_count == 0:
            issues.append("No policy evidence")
        if q.sentiment_evidence_count == 0:
            issues.append("No sentiment evidence")
        if q.avg_policy_score < 0.6 and q.policy_evidence_count > 0:
            issues.append("Weak policy alignment")
        if q.avg_sentiment_score < 0.6 and q.sentiment_evidence_count > 0:
            issues.append("Weak sentiment alignment")
        
        return "; ".join(issues) if issues else "Unknown"
    
    def _count_languages(self, cells: List[KnowledgeCell]) -> Dict[str, int]:
        """Count cells per language."""
        counts = Counter()
        for cell in cells:
            for lang in cell.definitions.keys():
                counts[lang] += 1
        return dict(counts)
    
    def _count_policy_sources(self, cells: List[KnowledgeCell]) -> Dict[str, int]:
        """Count aligned paragraphs by source."""
        counts = Counter()
        for cell in cells:
            for evidence in cell.policy_evidence:
                counts[evidence.source] += 1
        return dict(counts)
    
    def _count_sentiments(self, cells: List[KnowledgeCell]) -> Dict[str, int]:
        """Count aligned articles by sentiment."""
        counts = Counter()
        for cell in cells:
            for evidence in cell.sentiment_evidence:
                counts[evidence.sentiment.label] += 1
        return dict(counts)

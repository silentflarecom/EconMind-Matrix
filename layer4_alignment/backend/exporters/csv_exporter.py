"""
CSV Exporter

Exports Knowledge Cells to CSV format for spreadsheet analysis.
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from ..knowledge_cell import KnowledgeCell


class CSVExporter:
    """
    Exports Knowledge Cells to CSV format.
    
    Flattens the nested structure for spreadsheet compatibility.
    Includes UTF-8 BOM for Excel support.
    """
    
    def __init__(
        self,
        output_dir: str = "dataset",
        languages: List[str] = None
    ):
        self.output_dir = Path(output_dir)
        self.languages = languages or ["en", "zh", "ja", "ko", "fr", "de"]
    
    def export(
        self,
        cells: List[KnowledgeCell],
        output_path: Optional[str] = None
    ) -> str:
        """
        Export cells to CSV file.
        
        Args:
            cells: List of KnowledgeCell objects
            output_path: Optional explicit output path
            
        Returns:
            Path to the created file
        """
        if output_path:
            filepath = Path(output_path)
        else:
            self.output_dir.mkdir(exist_ok=True, parents=True)
            date_str = datetime.now().strftime("%Y%m%d")
            filepath = self.output_dir / f"aligned_corpus_{date_str}.csv"
        
        filepath.parent.mkdir(exist_ok=True, parents=True)
        
        # Build header
        header = [
            "concept_id",
            "primary_term",
            "quality_score",
            "language_count",
            "policy_count",
            "sentiment_count"
        ]
        
        # Add language columns
        for lang in self.languages:
            header.extend([f"term_{lang}", f"summary_{lang}"])
        
        # Add summary columns
        header.extend([
            "top_policy_source",
            "top_policy_score",
            "dominant_sentiment",
            "sentiment_distribution"
        ])
        
        # Write CSV with BOM
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            
            for cell in cells:
                row = self._cell_to_row(cell)
                writer.writerow(row)
        
        return str(filepath)
    
    def _cell_to_row(self, cell: KnowledgeCell) -> List[str]:
        """Convert a KnowledgeCell to a CSV row."""
        q = cell.metadata.quality_metrics
        
        row = [
            cell.concept_id,
            cell.primary_term,
            f"{q.overall_score:.3f}",
            str(q.language_coverage),
            str(q.policy_evidence_count),
            str(q.sentiment_evidence_count)
        ]
        
        # Language columns
        for lang in self.languages:
            defn = cell.definitions.get(lang)
            if defn:
                row.extend([defn.term, defn.summary[:200] if defn.summary else ""])
            else:
                row.extend(["", ""])
        
        # Top policy
        if cell.policy_evidence:
            top_policy = max(cell.policy_evidence, key=lambda e: e.alignment_scores.final)
            row.extend([top_policy.source, f"{top_policy.alignment_scores.final:.2f}"])
        else:
            row.extend(["", ""])
        
        # Sentiment summary
        if cell.sentiment_evidence:
            sentiments = [e.sentiment.label for e in cell.sentiment_evidence]
            from collections import Counter
            counts = Counter(sentiments)
            dominant = counts.most_common(1)[0][0] if counts else ""
            distribution = ", ".join(f"{k}:{v}" for k, v in counts.items())
            row.extend([dominant, distribution])
        else:
            row.extend(["", ""])
        
        return row

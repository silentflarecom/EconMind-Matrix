"""
Layer 3: Doccano Export/Import Module
Integration with Doccano annotation platform for human-in-the-loop verification.

Supports:
- JSONL export for Doccano Sequence Labeling / Sentiment Analysis
- CSV export for spreadsheet annotation
- Import of verified annotations from Doccano

Usage:
    from doccano_export import DoccanoExporter, DoccanoImporter
    
    # Export for annotation
    exporter = DoccanoExporter(db_path="corpus.db")
    await exporter.export_jsonl("output.jsonl", limit=500)
    
    # Import verified annotations
    importer = DoccanoImporter(db_path="corpus.db")
    await importer.import_jsonl("annotated.jsonl")
"""

import json
import csv
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# Import models and database
try:
    from .models import (
        SentimentLabel, AnnotationSource, SentimentAnnotation,
        NewsArticle
    )
    from .database import SentimentDatabase
except ImportError:
    from models import (
        SentimentLabel, AnnotationSource, SentimentAnnotation,
        NewsArticle
    )
    from database import SentimentDatabase


class DoccanoExporter:
    """
    Exports news articles to Doccano-compatible formats.
    """
    
    # Doccano label configuration
    LABELS = [
        {"id": 1, "text": "bullish", "color": "#00C853"},
        {"id": 2, "text": "bearish", "color": "#FF1744"},
        {"id": 3, "text": "neutral", "color": "#9E9E9E"}
    ]
    
    def __init__(self, db_path: str = "corpus.db"):
        """
        Initialize exporter.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db = SentimentDatabase(db_path)
    
    async def export_jsonl(
        self,
        output_path: str,
        include_preannotations: bool = True,
        only_unannotated: bool = False,
        limit: int = 1000
    ) -> int:
        """
        Export articles to JSONL format for Doccano.
        
        Format: {"id": 1, "text": "...", "meta": {...}, "label": ["bullish"]}
        
        Args:
            output_path: Path to output JSONL file
            include_preannotations: Include LLM/rule-based pre-annotations as labels
            only_unannotated: Only export articles without human annotations
            limit: Maximum number of articles to export
            
        Returns:
            Number of articles exported
        """
        # Get articles
        articles = await self.db.get_annotated_articles_for_doccano(
            include_unannotated=not only_unannotated,
            limit=limit
        )
        
        count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for article in articles:
                entry = {
                    "id": article["id"],
                    "text": article["text"],
                    "meta": article["meta"]
                }
                
                # Add pre-annotation as suggested label
                if include_preannotations and article.get("label"):
                    entry["label"] = [article["label"]]
                    entry["meta"]["pre_confidence"] = article.get("confidence", 0)
                    entry["meta"]["pre_reasoning"] = article.get("reasoning", "")
                else:
                    entry["label"] = []
                
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                count += 1
        
        print(f"✓ Exported {count} articles to {output_path}")
        return count
    
    async def export_csv(
        self,
        output_path: str,
        include_preannotations: bool = True,
        limit: int = 1000
    ) -> int:
        """
        Export articles to CSV format for spreadsheet annotation.
        
        Args:
            output_path: Path to output CSV file
            include_preannotations: Include pre-annotations
            limit: Maximum articles
            
        Returns:
            Number of articles exported
        """
        articles = await self.db.get_annotated_articles_for_doccano(
            include_unannotated=True,
            limit=limit
        )
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            headers = [
                "ID", "Title", "Summary", "Source", "URL", "Date",
                "Pre-Label", "Pre-Confidence", "Human Label", "Notes"
            ]
            writer.writerow(headers)
            
            for article in articles:
                # Parse text to get title and summary
                text_parts = article["text"].split("\n\n", 1)
                title = text_parts[0] if text_parts else ""
                summary = text_parts[1] if len(text_parts) > 1 else ""
                
                row = [
                    article["id"],
                    title,
                    summary,
                    article["meta"].get("source", ""),
                    article["meta"].get("url", ""),
                    article["meta"].get("date", ""),
                    article.get("label", "") if include_preannotations else "",
                    article.get("confidence", "") if include_preannotations else "",
                    "",  # Human label (to be filled)
                    ""   # Notes (to be filled)
                ]
                writer.writerow(row)
        
        print(f"✓ Exported {len(articles)} articles to {output_path}")
        return len(articles)
    
    def export_label_config(self, output_path: str):
        """
        Export label configuration for Doccano project setup.
        
        Args:
            output_path: Path to output JSON file
        """
        config = {
            "labels": self.LABELS,
            "task_type": "DocumentClassification",
            "description": "Sentiment classification for financial news",
            "instructions": """
## Financial News Sentiment Annotation

Classify each news headline/summary into one of three categories:

### Labels

1. **bullish** (🟢): Positive for stock markets
   - Economic growth, strong earnings, accommodative policy
   - Rate cuts, stimulus, positive economic data
   - Examples: "S&P 500 surges", "Fed signals rate cuts"

2. **bearish** (🔴): Negative for stock markets
   - Economic slowdown, weak earnings, tightening policy
   - Rate hikes, inflation concerns, recession signals
   - Examples: "Stocks plunge", "Inflation rises"

3. **neutral** (⚫): No clear market impact
   - Mixed signals, routine updates, no directional bias
   - Examples: "Fed meets Wednesday", "Markets unchanged"

### Tips
- Focus on the likely MARKET IMPACT, not just whether news is "good" or "bad"
- Consider central bank policy implications
- When uncertain, lean toward "neutral"
            """
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported label config to {output_path}")


class DoccanoImporter:
    """
    Imports verified annotations from Doccano.
    """
    
    def __init__(self, db_path: str = "corpus.db"):
        """
        Initialize importer.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db = SentimentDatabase(db_path)
    
    async def import_jsonl(
        self,
        input_path: str,
        override_existing: bool = False
    ) -> Dict[str, int]:
        """
        Import annotations from Doccano JSONL export.
        
        Expected format: {"id": 1, "text": "...", "label": ["bullish"]}
        
        Args:
            input_path: Path to JSONL file from Doccano
            override_existing: Whether to override existing annotations
            
        Returns:
            Dict with import statistics
        """
        stats = {
            "total": 0,
            "imported": 0,
            "skipped_no_label": 0,
            "skipped_existing": 0,
            "errors": 0
        }
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                stats["total"] += 1
                
                try:
                    entry = json.loads(line.strip())
                    article_id = entry.get("id")
                    labels = entry.get("label", [])
                    
                    if not article_id:
                        stats["errors"] += 1
                        continue
                    
                    if not labels:
                        stats["skipped_no_label"] += 1
                        continue
                    
                    # Get the first label (assuming single-label classification)
                    label_text = labels[0] if isinstance(labels, list) else labels
                    
                    # Validate label
                    if label_text not in ["bullish", "bearish", "neutral"]:
                        stats["errors"] += 1
                        continue
                    
                    # Check if annotation already exists
                    existing = await self.db.get_annotations(article_id=article_id, limit=1)
                    
                    if existing and not override_existing:
                        # Check if it's already human-verified
                        if existing[0].verified:
                            stats["skipped_existing"] += 1
                            continue
                        # Update existing annotation
                        await self.db.update_annotation(
                            annotation_id=existing[0].id,
                            sentiment_label=SentimentLabel(label_text),
                            confidence_score=1.0,
                            reasoning="Verified via Doccano"
                        )
                    else:
                        # Create new annotation
                        annotation = SentimentAnnotation(
                            article_id=article_id,
                            sentiment_label=SentimentLabel(label_text),
                            confidence_score=1.0,
                            annotation_source=AnnotationSource.DOCCANO,
                            reasoning="Human annotation via Doccano",
                            verified=True,
                            verified_by="doccano_import"
                        )
                        await self.db.insert_annotation(annotation)
                    
                    stats["imported"] += 1
                    
                except json.JSONDecodeError:
                    stats["errors"] += 1
                except Exception as e:
                    print(f"Error importing entry: {e}")
                    stats["errors"] += 1
        
        print(f"✓ Import complete: {stats}")
        return stats
    
    async def import_csv(
        self,
        input_path: str,
        label_column: str = "Human Label",
        override_existing: bool = False
    ) -> Dict[str, int]:
        """
        Import annotations from CSV file.
        
        Args:
            input_path: Path to CSV file
            label_column: Name of column containing human labels
            override_existing: Whether to override existing annotations
            
        Returns:
            Dict with import statistics
        """
        stats = {
            "total": 0,
            "imported": 0,
            "skipped_no_label": 0,
            "skipped_existing": 0,
            "errors": 0
        }
        
        with open(input_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                stats["total"] += 1
                
                try:
                    article_id = int(row.get("ID", 0))
                    label_text = row.get(label_column, "").strip().lower()
                    notes = row.get("Notes", "")
                    
                    if not article_id:
                        stats["errors"] += 1
                        continue
                    
                    if not label_text or label_text not in ["bullish", "bearish", "neutral"]:
                        stats["skipped_no_label"] += 1
                        continue
                    
                    # Check existing
                    existing = await self.db.get_annotations(article_id=article_id, limit=1)
                    
                    if existing and not override_existing:
                        if existing[0].verified:
                            stats["skipped_existing"] += 1
                            continue
                        await self.db.update_annotation(
                            annotation_id=existing[0].id,
                            sentiment_label=SentimentLabel(label_text),
                            confidence_score=1.0,
                            reasoning=f"Verified via CSV import. {notes}".strip()
                        )
                    else:
                        annotation = SentimentAnnotation(
                            article_id=article_id,
                            sentiment_label=SentimentLabel(label_text),
                            confidence_score=1.0,
                            annotation_source=AnnotationSource.HUMAN,
                            reasoning=f"Human annotation via CSV. {notes}".strip(),
                            verified=True,
                            verified_by="csv_import"
                        )
                        await self.db.insert_annotation(annotation)
                    
                    stats["imported"] += 1
                    
                except Exception as e:
                    print(f"Error importing row: {e}")
                    stats["errors"] += 1
        
        print(f"✓ CSV import complete: {stats}")
        return stats


class AnnotationQualityChecker:
    """
    Checks quality of annotations and identifies disagreements.
    """
    
    def __init__(self, db_path: str = "corpus.db"):
        self.db = SentimentDatabase(db_path)
    
    async def check_agreement(self) -> Dict[str, Any]:
        """
        Check agreement between LLM and human annotations.
        
        Returns:
            Dict with agreement statistics
        """
        # Get all annotations
        all_annotations = await self.db.get_annotations(limit=10000)
        
        # Group by article_id
        by_article = {}
        for annot in all_annotations:
            if annot.article_id not in by_article:
                by_article[annot.article_id] = []
            by_article[annot.article_id].append(annot)
        
        # Find articles with multiple annotations (LLM + human)
        stats = {
            "total_articles": len(by_article),
            "single_annotation": 0,
            "multiple_annotations": 0,
            "agreements": 0,
            "disagreements": 0,
            "disagreement_details": []
        }
        
        for article_id, annotations in by_article.items():
            if len(annotations) == 1:
                stats["single_annotation"] += 1
            else:
                stats["multiple_annotations"] += 1
                
                # Check if LLM and human agree
                llm_annot = None
                human_annot = None
                
                for annot in annotations:
                    if annot.annotation_source in [AnnotationSource.LLM_GEMINI, AnnotationSource.LLM_GPT, AnnotationSource.RULE_BASED]:
                        llm_annot = annot
                    elif annot.annotation_source in [AnnotationSource.HUMAN, AnnotationSource.DOCCANO]:
                        human_annot = annot
                
                if llm_annot and human_annot:
                    if llm_annot.sentiment_label == human_annot.sentiment_label:
                        stats["agreements"] += 1
                    else:
                        stats["disagreements"] += 1
                        stats["disagreement_details"].append({
                            "article_id": article_id,
                            "llm_label": llm_annot.sentiment_label.value,
                            "human_label": human_annot.sentiment_label.value,
                            "title": llm_annot.article_title
                        })
        
        # Calculate agreement rate
        compared = stats["agreements"] + stats["disagreements"]
        stats["agreement_rate"] = stats["agreements"] / compared if compared > 0 else 0
        
        return stats
    
    async def get_low_confidence_articles(
        self,
        threshold: float = 0.6,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get articles with low confidence annotations that need review.
        
        Args:
            threshold: Confidence threshold (articles below this need review)
            limit: Maximum articles to return
            
        Returns:
            List of articles needing review
        """
        annotations = await self.db.get_annotations(verified_only=False, limit=10000)
        
        low_confidence = [
            {
                "article_id": a.article_id,
                "title": a.article_title,
                "current_label": a.sentiment_label.value,
                "confidence": a.confidence_score,
                "source": a.annotation_source.value,
                "reasoning": a.reasoning
            }
            for a in annotations
            if a.confidence_score < threshold and not a.verified
        ]
        
        # Sort by confidence (lowest first)
        low_confidence.sort(key=lambda x: x["confidence"])
        
        return low_confidence[:limit]


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Doccano Export/Import Module")
    print("=" * 60)
    
    async def test_doccano():
        # Test exporter
        exporter = DoccanoExporter("test_layer3.db")
        
        print("\n1. Exporting label config...")
        exporter.export_label_config("test_labels.json")
        
        print("\n2. Testing export formats (requires database with data)...")
        try:
            await exporter.db.initialize()
            count = await exporter.export_jsonl("test_export.jsonl", limit=10)
            print(f"   Exported {count} articles to JSONL")
        except Exception as e:
            print(f"   Export test skipped: {e}")
        
        # Test importer
        print("\n3. Testing import (requires exported file)...")
        try:
            importer = DoccanoImporter("test_layer3.db")
            # Would need actual annotated file
            print("   Import test skipped (no annotated file)")
        except Exception as e:
            print(f"   Import test skipped: {e}")
        
        print("\nTest complete!")
    
    asyncio.run(test_doccano())

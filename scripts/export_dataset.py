"""
Dataset Export Script
Exports all corpus data to various formats for distribution

Usage:
    python scripts/export_dataset.py --format jsonl --output ./dataset/
    python scripts/export_dataset.py --format all --output ./dataset/
"""

import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def export_jsonl(data: list, output_path: str):
    """Export data as JSON Lines (one JSON object per line)."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Exported {len(data)} items to {output_path}")


def export_json(data: list, output_path: str):
    """Export data as standard JSON array."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(data)} items to {output_path}")


def export_csv(data: list, output_path: str, columns: list = None):
    """Export data as CSV."""
    if not data:
        print("No data to export")
        return
    
    if columns is None:
        columns = list(data[0].keys())
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)
    print(f"Exported {len(data)} items to {output_path}")


def export_tmx(data: list, output_path: str, source_lang: str = "en", target_lang: str = "zh"):
    """Export data as TMX (Translation Memory Exchange)."""
    header = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header creationtool="EconMind-Matrix" creationtoolversion="1.0" 
          datatype="plaintext" segtype="sentence" adminlang="en-us"
          srclang="{source_lang}" o-tmf="undefined"/>
  <body>
'''
    footer = '''  </body>
</tmx>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header.format(source_lang=source_lang))
        
        for item in data:
            source_text = item.get(f"{source_lang}_summary", "")
            target_text = item.get(f"{target_lang}_summary", "")
            
            if source_text and target_text:
                # Escape XML special characters
                source_text = source_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                target_text = target_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                f.write(f'''    <tu>
      <tuv xml:lang="{source_lang}">
        <seg>{source_text}</seg>
      </tuv>
      <tuv xml:lang="{target_lang}">
        <seg>{target_text}</seg>
      </tuv>
    </tu>
''')
        
        f.write(footer)
    print(f"Exported TMX to {output_path}")


def generate_statistics(data: list) -> dict:
    """Generate dataset statistics."""
    stats = {
        "export_date": datetime.now().isoformat(),
        "total_terms": len(data),
        "languages": {},
        "terms_with_associations": 0,
        "avg_summary_length": {}
    }
    
    # Count language coverage
    for item in data:
        translations = item.get("translations", {})
        for lang in translations:
            stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
        
        if item.get("related_terms"):
            stats["terms_with_associations"] += 1
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Export EconMind Matrix dataset")
    parser.add_argument("--format", choices=["jsonl", "json", "csv", "tmx", "all"], default="all")
    parser.add_argument("--output", type=str, default="./dataset/")
    parser.add_argument("--db", type=str, default="./backend/corpus.db")
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Exporting dataset from {args.db} to {args.output}")
    print("-" * 60)
    
    # TODO: Load data from database
    # For now, using sample data
    sample_data = [
        {
            "id": 1,
            "term": "Inflation",
            "en_summary": "In economics, inflation is a general increase in the prices of goods and services...",
            "zh_summary": "通货膨胀是指一般物价水平持续上涨的现象...",
            "en_url": "https://en.wikipedia.org/wiki/Inflation",
            "zh_url": "https://zh.wikipedia.org/wiki/通货膨胀",
            "related_terms": ["Deflation", "CPI", "Monetary Policy"],
            "categories": ["Macroeconomics"],
            "translations": {
                "en": {"summary": "...", "url": "..."},
                "zh": {"summary": "...", "url": "..."}
            }
        }
    ]
    
    print("Note: Using sample data. Connect to database for full export.")
    print()
    
    # Export in requested format(s)
    formats = ["jsonl", "json", "csv", "tmx"] if args.format == "all" else [args.format]
    
    for fmt in formats:
        if fmt == "jsonl":
            export_jsonl(sample_data, output_dir / "terminology.jsonl")
        elif fmt == "json":
            export_json(sample_data, output_dir / "terminology.json")
        elif fmt == "csv":
            csv_data = [
                {
                    "id": d["id"],
                    "term": d["term"],
                    "en_summary": d["en_summary"],
                    "zh_summary": d["zh_summary"],
                    "en_url": d["en_url"],
                    "zh_url": d["zh_url"]
                }
                for d in sample_data
            ]
            export_csv(csv_data, output_dir / "terminology.csv")
        elif fmt == "tmx":
            export_tmx(sample_data, output_dir / "terminology.tmx")
    
    # Generate and save statistics
    stats = generate_statistics(sample_data)
    with open(output_dir / "statistics.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"Statistics saved to {output_dir / 'statistics.json'}")
    
    print()
    print("Export complete!")


if __name__ == "__main__":
    main()

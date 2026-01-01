"""
Dataset Export Script with Full Database Integration
Exports all corpus data to various formats for distribution

Usage:
    python scripts/export_dataset.py --format jsonl --output ./dataset/
    python scripts/export_dataset.py --format all --output ./dataset/
    python scripts/export_dataset.py --report  # Generate statistics only
"""

import json
import csv
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Create database connection with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# Layer 1: Terminology Export
# ============================================================================

def export_layer1_terms(conn: sqlite3.Connection) -> List[Dict]:
    """Export all completed terms from Layer 1."""
    cursor = conn.execute("""
        SELECT t.*, 
               GROUP_CONCAT(ta.target_term || ':' || ta.association_type, '|') as associations
        FROM terms t
        LEFT JOIN term_associations ta ON t.id = ta.source_term_id
        WHERE t.status = 'completed'
        GROUP BY t.id
        ORDER BY t.term
    """)
    
    terms = []
    for row in cursor.fetchall():
        term_data = dict(row)
        
        # Parse translations JSON
        translations = {}
        if term_data.get('translations'):
            try:
                translations = json.loads(term_data['translations'])
            except json.JSONDecodeError:
                pass
        
        # Fallback to legacy columns
        if not translations:
            if term_data.get('en_summary'):
                translations['en'] = {
                    'summary': term_data['en_summary'],
                    'url': term_data.get('en_url')
                }
            if term_data.get('zh_summary'):
                translations['zh'] = {
                    'summary': term_data['zh_summary'],
                    'url': term_data.get('zh_url')
                }
        
        # Parse associations
        related_terms = []
        if term_data.get('associations'):
            for assoc in term_data['associations'].split('|'):
                if ':' in assoc:
                    target, _ = assoc.split(':', 1)
                    if target and target not in related_terms:
                        related_terms.append(target)
        
        terms.append({
            'id': term_data['id'],
            'term': term_data['term'],
            'translations': translations,
            'related_terms': related_terms,
            'depth_level': term_data.get('depth_level', 0),
            'created_at': term_data.get('created_at'),
        })
    
    return terms


# ============================================================================
# Layer 2: Policy Export
# ============================================================================

def export_layer2_reports(conn: sqlite3.Connection) -> List[Dict]:
    """Export all policy reports with paragraphs."""
    try:
        cursor = conn.execute("""
            SELECT * FROM policy_reports ORDER BY report_date DESC
        """)
        reports = [dict(row) for row in cursor.fetchall()]
        
        for report in reports:
            # Get paragraphs for each report
            para_cursor = conn.execute("""
                SELECT id, paragraph_index, text, topic, section_title
                FROM policy_paragraphs WHERE report_id = ?
                ORDER BY paragraph_index
            """, (report['id'],))
            report['paragraphs'] = [dict(row) for row in para_cursor.fetchall()]
        
        return reports
    except sqlite3.OperationalError:
        print("  Warning: Layer 2 tables not found")
        return []


def export_layer2_alignments(conn: sqlite3.Connection) -> List[Dict]:
    """Export policy alignments."""
    try:
        cursor = conn.execute("""
            SELECT pa.*,
                   sp.text as source_text,
                   tp.text as target_text,
                   sr.title as source_report,
                   tr.title as target_report
            FROM policy_alignments pa
            JOIN policy_paragraphs sp ON pa.source_paragraph_id = sp.id
            JOIN policy_paragraphs tp ON pa.target_paragraph_id = tp.id
            JOIN policy_reports sr ON sp.report_id = sr.id
            JOIN policy_reports tr ON tp.report_id = tr.id
            WHERE pa.similarity_score >= 0.5
            ORDER BY pa.similarity_score DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        print("  Warning: Layer 2 alignment tables not found")
        return []


# ============================================================================
# Layer 3: Sentiment Export
# ============================================================================

def export_layer3_articles(conn: sqlite3.Connection) -> List[Dict]:
    """Export news articles with sentiment annotations."""
    try:
        cursor = conn.execute("""
            SELECT na.*,
                   sa.sentiment_label,
                   sa.confidence_score,
                   sa.annotation_source,
                   sa.reasoning
            FROM news_articles na
            LEFT JOIN sentiment_annotations sa ON na.id = sa.article_id
            ORDER BY na.published_date DESC
        """)
        
        articles = []
        for row in cursor.fetchall():
            article = dict(row)
            # Parse related_terms JSON
            if article.get('related_terms'):
                try:
                    article['related_terms'] = json.loads(article['related_terms'])
                except json.JSONDecodeError:
                    article['related_terms'] = []
            articles.append(article)
        
        return articles
    except sqlite3.OperationalError:
        print("  Warning: Layer 3 tables not found")
        return []


# ============================================================================
# Export Functions
# ============================================================================

def export_jsonl(data: list, output_path: str):
    """Export data as JSON Lines."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
    print(f"  ✓ Exported {len(data)} items to {output_path}")


def export_json(data: list, output_path: str):
    """Export data as standard JSON array."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"  ✓ Exported {len(data)} items to {output_path}")


def export_csv(data: list, output_path: str, columns: list = None):
    """Export data as CSV."""
    if not data:
        print(f"  ⚠ No data to export to {output_path}")
        return
    
    if columns is None:
        columns = list(data[0].keys())
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for row in data:
            # Convert non-string values to strings for CSV
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, (list, dict)):
                    cleaned_row[k] = json.dumps(v, ensure_ascii=False)
                else:
                    cleaned_row[k] = v
            writer.writerow(cleaned_row)
    print(f"  ✓ Exported {len(data)} items to {output_path}")


def export_tmx(data: list, output_path: str, source_lang: str = "en", target_lang: str = "zh"):
    """Export Layer 1 data as TMX (Translation Memory Exchange)."""
    header = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header creationtool="EconMind-Matrix" creationtoolversion="1.0" 
          datatype="plaintext" segtype="sentence" adminlang="en-us"
          srclang="{source_lang}" o-tmf="undefined"/>
  <body>
'''
    footer = '''  </body>
</tmx>'''

    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        
        for item in data:
            translations = item.get('translations', {})
            source_text = translations.get(source_lang, {}).get('summary', '')
            target_text = translations.get(target_lang, {}).get('summary', '')
            
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
                count += 1
        
        f.write(footer)
    print(f"  ✓ Exported {count} translation pairs to {output_path}")


# ============================================================================
# Statistics Report
# ============================================================================

def generate_statistics_report(conn: sqlite3.Connection, output_path: str) -> dict:
    """Generate comprehensive statistics report."""
    stats = {
        "export_date": datetime.now().isoformat(),
        "export_version": "1.0",
        "layer1": {},
        "layer2": {},
        "layer3": {},
        "summary": {}
    }
    
    # Layer 1 Statistics
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM terms WHERE status = 'completed'")
        stats["layer1"]["total_terms"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT task_id) FROM terms")
        stats["layer1"]["total_tasks"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM term_associations")
        stats["layer1"]["total_associations"] = cursor.fetchone()[0]
        
        # Language coverage
        cursor = conn.execute("""
            SELECT translations FROM terms 
            WHERE status = 'completed' AND translations IS NOT NULL
        """)
        lang_counts = {}
        for row in cursor.fetchall():
            try:
                trans = json.loads(row[0])
                for lang in trans.keys():
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
            except:
                pass
        stats["layer1"]["language_coverage"] = lang_counts
        
    except sqlite3.OperationalError:
        stats["layer1"]["error"] = "Tables not found"
    
    # Layer 2 Statistics
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM policy_reports")
        stats["layer2"]["total_reports"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM policy_paragraphs")
        stats["layer2"]["total_paragraphs"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM policy_alignments WHERE similarity_score >= 0.5")
        stats["layer2"]["total_alignments"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT source, COUNT(*) FROM policy_reports GROUP BY source")
        stats["layer2"]["reports_by_source"] = {row[0]: row[1] for row in cursor.fetchall()}
        
    except sqlite3.OperationalError:
        stats["layer2"]["error"] = "Tables not found"
    
    # Layer 3 Statistics
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM news_articles")
        stats["layer3"]["total_articles"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM sentiment_annotations")
        stats["layer3"]["total_annotations"] = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT sentiment_label, COUNT(*) 
            FROM sentiment_annotations 
            GROUP BY sentiment_label
        """)
        stats["layer3"]["sentiment_distribution"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor = conn.execute("""
            SELECT source, COUNT(*) 
            FROM news_articles 
            GROUP BY source
        """)
        stats["layer3"]["articles_by_source"] = {row[0]: row[1] for row in cursor.fetchall()}
        
    except sqlite3.OperationalError:
        stats["layer3"]["error"] = "Tables not found"
    
    # Summary
    stats["summary"] = {
        "total_layer1_terms": stats["layer1"].get("total_terms", 0),
        "total_layer2_reports": stats["layer2"].get("total_reports", 0),
        "total_layer3_articles": stats["layer3"].get("total_articles", 0),
    }
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    return stats


def print_statistics(stats: dict):
    """Print statistics to console."""
    print("\n" + "=" * 60)
    print("📊 EconMind-Matrix Dataset Statistics")
    print("=" * 60)
    
    print("\n📚 Layer 1: Terminology Knowledge Base")
    l1 = stats.get("layer1", {})
    print(f"   Terms: {l1.get('total_terms', 0)}")
    print(f"   Associations: {l1.get('total_associations', 0)}")
    if l1.get('language_coverage'):
        langs = ", ".join([f"{k}:{v}" for k, v in l1['language_coverage'].items()])
        print(f"   Languages: {langs}")
    
    print("\n📊 Layer 2: Policy Parallel Corpus")
    l2 = stats.get("layer2", {})
    print(f"   Reports: {l2.get('total_reports', 0)}")
    print(f"   Paragraphs: {l2.get('total_paragraphs', 0)}")
    print(f"   Alignments: {l2.get('total_alignments', 0)}")
    
    print("\n📰 Layer 3: Sentiment & Trend Corpus")
    l3 = stats.get("layer3", {})
    print(f"   Articles: {l3.get('total_articles', 0)}")
    print(f"   Annotations: {l3.get('total_annotations', 0)}")
    if l3.get('sentiment_distribution'):
        dist = l3['sentiment_distribution']
        print(f"   Sentiment: bullish={dist.get('bullish', 0)}, bearish={dist.get('bearish', 0)}, neutral={dist.get('neutral', 0)}")
    
    print("\n" + "=" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Export EconMind Matrix dataset")
    parser.add_argument("--format", choices=["jsonl", "json", "csv", "tmx", "all"], default="all")
    parser.add_argument("--output", type=str, default="./dataset/")
    parser.add_argument("--db", type=str, default=None)
    parser.add_argument("--report", action="store_true", help="Generate statistics report only")
    parser.add_argument("--layer", choices=["1", "2", "3", "all"], default="all", help="Export specific layer")
    args = parser.parse_args()
    
    # Find database
    db_paths = [
        args.db,
        "./corpus.db",
        "./backend/corpus.db",
        "../corpus.db"
    ]
    db_path = None
    for p in db_paths:
        if p and Path(p).exists():
            db_path = p
            break
    
    if not db_path:
        print("❌ Error: corpus.db not found. Please specify with --db")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 EconMind-Matrix Dataset Export")
    print(f"   Database: {db_path}")
    print(f"   Output: {args.output}")
    print("-" * 60)
    
    conn = get_db_connection(db_path)
    
    # Generate statistics report
    stats = generate_statistics_report(conn, output_dir / "statistics.json")
    print_statistics(stats)
    
    if args.report:
        print("\n✓ Statistics report saved to statistics.json")
        conn.close()
        return
    
    # Export data
    formats = ["jsonl", "json", "csv", "tmx"] if args.format == "all" else [args.format]
    layers = ["1", "2", "3"] if args.layer == "all" else [args.layer]
    
    # Layer 1 Export
    if "1" in layers:
        print("\n📚 Exporting Layer 1: Terminology...")
        terms = export_layer1_terms(conn)
        
        for fmt in formats:
            if fmt == "jsonl":
                export_jsonl(terms, output_dir / "layer1_terminology.jsonl")
            elif fmt == "json":
                export_json(terms, output_dir / "layer1_terminology.json")
            elif fmt == "csv":
                csv_data = []
                for t in terms:
                    trans = t.get('translations', {})
                    csv_data.append({
                        'id': t['id'],
                        'term': t['term'],
                        'en_summary': trans.get('en', {}).get('summary', ''),
                        'zh_summary': trans.get('zh', {}).get('summary', ''),
                        'related_terms': ', '.join(t.get('related_terms', [])),
                        'depth_level': t.get('depth_level', 0)
                    })
                export_csv(csv_data, output_dir / "layer1_terminology.csv")
            elif fmt == "tmx":
                export_tmx(terms, output_dir / "layer1_terminology.tmx")
    
    # Layer 2 Export
    if "2" in layers:
        print("\n📊 Exporting Layer 2: Policy...")
        reports = export_layer2_reports(conn)
        alignments = export_layer2_alignments(conn)
        
        for fmt in formats:
            if fmt == "jsonl":
                export_jsonl(reports, output_dir / "layer2_reports.jsonl")
                export_jsonl(alignments, output_dir / "layer2_alignments.jsonl")
            elif fmt == "json":
                export_json(reports, output_dir / "layer2_reports.json")
                export_json(alignments, output_dir / "layer2_alignments.json")
    
    # Layer 3 Export
    if "3" in layers:
        print("\n📰 Exporting Layer 3: Sentiment...")
        articles = export_layer3_articles(conn)
        
        for fmt in formats:
            if fmt == "jsonl":
                export_jsonl(articles, output_dir / "layer3_articles.jsonl")
            elif fmt == "json":
                export_json(articles, output_dir / "layer3_articles.json")
    
    conn.close()
    print("\n✅ Export complete!")


if __name__ == "__main__":
    main()

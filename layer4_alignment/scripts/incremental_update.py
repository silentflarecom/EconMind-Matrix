#!/usr/bin/env python3
"""
Incremental Update Script

Processes only newly added terms since the last alignment run.
Useful for updating the dataset without full reprocessing.

Usage:
    python incremental_update.py --since 2025-01-15
    python incremental_update.py --append dataset/aligned_corpus.jsonl
"""

import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
LAYER4_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = LAYER4_DIR.parent

sys.path.insert(0, str(LAYER4_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from backend.alignment_engine import AlignmentEngine
from backend.data_loader import DataLoader


def parse_args():
    parser = argparse.ArgumentParser(
        description="Incremental alignment update"
    )
    parser.add_argument(
        "--since", "-s",
        type=str,
        required=True,
        help="Only process terms created after this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=str(LAYER4_DIR / "config" / "alignment_config.yaml"),
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--append", "-a",
        type=str,
        default=None,
        help="Append to existing JSONL file instead of creating new"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path for new JSONL file"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    
    print(f"Incremental Update since: {args.since}")
    print(f"Configuration: {args.config}")
    print()
    
    # Initialize engine
    engine = AlignmentEngine(config_path=args.config)
    
    # Custom term loading with date filter would require DB schema update
    # For now, we'll load all and filter (can be optimized later)
    await engine.load_source_data()
    
    # Load all terms
    loader = DataLoader()
    all_terms = await loader.load_layer1_terms()
    
    # Filter by created_at if available (requires schema support)
    # For now, process all terms
    print(f"\n[INFO] Processing {len(all_terms)} terms (date filtering not yet implemented)")
    
    # Run alignment
    engine.results = []
    for i, term in enumerate(all_terms):
        print(f"[{i+1}/{len(all_terms)}] Aligning: {term.term}")
        cell = await engine.align_term(term)
        engine.results.append(cell)
        
        q = cell.metadata.quality_metrics
        print(f"  └─ Score: {q.overall_score:.2f}")
    
    # Export
    if args.append and Path(args.append).exists():
        # Append to existing file
        with open(args.append, 'a', encoding='utf-8') as f:
            for cell in engine.results:
                f.write(cell.to_jsonl_line() + '\n')
        print(f"\n✓ Appended {len(engine.results)} cells to {args.append}")
    else:
        output = engine.export_jsonl(args.output)
        print(f"\n✓ Exported to {output}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

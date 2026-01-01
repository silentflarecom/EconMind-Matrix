#!/usr/bin/env python3
"""
Full Alignment Runner

Executes the complete Layer 4 alignment pipeline, processing all terms
from Layer 1 and generating aligned Knowledge Cells.

Usage:
    python run_full_alignment.py
    python run_full_alignment.py --config custom_config.yaml
    python run_full_alignment.py --output dataset/my_corpus.jsonl
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Add parent paths for imports
SCRIPT_DIR = Path(__file__).parent
LAYER4_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = LAYER4_DIR.parent

sys.path.insert(0, str(LAYER4_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from backend.alignment_engine import AlignmentEngine


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Layer 4 alignment pipeline"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=str(LAYER4_DIR / "config" / "alignment_config.yaml"),
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path for JSONL file (default: dataset/aligned_corpus_YYYYMMDD.jsonl)"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip quality report generation"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    
    print(f"Configuration: {args.config}")
    print()
    
    # Initialize engine
    engine = AlignmentEngine(config_path=args.config)
    
    # Run alignment
    cells = await engine.run_full_alignment()
    
    if not cells:
        print("\n[WARN] No Knowledge Cells generated. Check if Layer 1 has data.")
        return 1
    
    # Export results
    output_path = engine.export_jsonl(args.output)
    
    # Generate quality report
    if not args.no_report:
        engine.generate_quality_report()
    
    print(f"\n✓ Successfully generated {len(cells)} Knowledge Cells")
    print(f"✓ Output: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Output Validator

Validates the generated JSONL dataset for schema compliance and data quality.

Usage:
    python validate_output.py dataset/aligned_corpus.jsonl
    python validate_output.py dataset/aligned_corpus.jsonl --strict
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).parent
LAYER4_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(LAYER4_DIR))

from backend.knowledge_cell import KnowledgeCell


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate alignment output"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to JSONL file to validate"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any validation error"
    )
    return parser.parse_args()


def validate_file(filepath: str, strict: bool = False) -> Tuple[int, int, List[str]]:
    """
    Validate a JSONL file.
    
    Returns:
        Tuple of (valid_count, error_count, error_messages)
    """
    valid = 0
    errors = 0
    messages = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Parse JSON
                data = json.loads(line)
                
                # Validate against Pydantic model
                cell = KnowledgeCell(**data)
                
                # Additional checks
                if not cell.primary_term:
                    raise ValueError("primary_term is empty")
                
                if not cell.concept_id:
                    raise ValueError("concept_id is empty")
                
                valid += 1
                
            except json.JSONDecodeError as e:
                errors += 1
                msg = f"Line {line_num}: JSON parse error - {e}"
                messages.append(msg)
                if strict:
                    break
                    
            except Exception as e:
                errors += 1
                msg = f"Line {line_num}: Validation error - {e}"
                messages.append(msg)
                if strict:
                    break
    
    return valid, errors, messages


def main():
    args = parse_args()
    
    filepath = Path(args.input_file)
    
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        return 1
    
    print(f"Validating: {filepath}")
    print()
    
    valid, errors, messages = validate_file(str(filepath), args.strict)
    
    # Print results
    total = valid + errors
    
    print(f"Total lines: {total}")
    print(f"Valid cells: {valid}")
    print(f"Errors: {errors}")
    
    if messages:
        print("\nError details:")
        for msg in messages[:20]:  # Limit output
            print(f"  - {msg}")
        if len(messages) > 20:
            print(f"  ... and {len(messages) - 20} more errors")
    
    if errors == 0:
        print("\n✓ Validation passed!")
        return 0
    else:
        print(f"\n✗ Validation failed with {errors} errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Layer 4: Offline Multi-Dimensional Semantic Alignment Pipeline

This module processes completed data from Layers 1-3 and generates publication-ready aligned datasets.

## Overview

Layer 4 is **NOT a user interface** - it is an offline batch processing engine that:

1. **Enumerates** all terms from Layer 1 (Terminology Knowledge Base)
2. **Searches** Layer 2/3 for related content
3. **Aligns** using multiple strategies (LLM, vectors, rules)
4. **Exports** structured Knowledge Cells in JSONL format

## Quick Start

```bash
# Navigate to layer4_alignment directory
cd layer4_alignment

# Run full alignment (uses default config)
python scripts/run_full_alignment.py

# With custom config
python scripts/run_full_alignment.py --config config/alignment_config.yaml

# Validate output
python scripts/validate_output.py dataset/aligned_corpus_YYYYMMDD.jsonl
```

## Directory Structure

```
layer4_alignment/
├── backend/
│   ├── __init__.py
│   ├── alignment_engine.py    # Core orchestration
│   ├── data_loader.py         # Load data from layers
│   ├── knowledge_cell.py      # Data model (Pydantic)
│   └── aligners/              # Alignment strategies
│       ├── base_aligner.py    # Abstract base class
│       ├── llm_aligner.py     # Gemini/GPT-4
│       ├── vector_aligner.py  # Sentence-BERT
│       ├── rule_aligner.py    # Keywords/TF-IDF
│       └── hybrid_aligner.py  # Ensemble
├── config/
│   └── alignment_config.yaml  # Configuration
├── scripts/
│   ├── run_full_alignment.py  # Main runner
│   ├── incremental_update.py  # Partial updates
│   └── validate_output.py     # Validation
└── README.md
```

## Configuration

Edit `config/alignment_config.yaml` to customize:

### Alignment Strategies

```yaml
alignment_strategies:
  llm_semantic:
    enabled: true              # Enable LLM alignment
    provider: "gemini"         # gemini, openai, deepseek
    model: "gemini-1.5-flash"
    threshold: 0.70
    weight: 0.50
    
  vector_similarity:
    enabled: true
    model: "sentence-transformers/..."
    threshold: 0.65
    weight: 0.30
    
  keyword_matching:
    enabled: true
    threshold: 0.60
    weight: 0.20
```

### Global Settings

```yaml
global:
  min_final_score: 0.65        # Filter threshold
  max_policy_evidence: 15       # Max per term
  max_sentiment_evidence: 30
  sentiment_time_window_days: 90
```

## Output Format

Each line in the JSONL output is a Knowledge Cell:

```json
{
  "concept_id": "Q17127698",
  "primary_term": "Inflation",
  "definitions": {
    "en": {"language": "en", "term": "Inflation", "summary": "...", "url": "..."},
    "zh": {"language": "zh", "term": "通货膨胀", "summary": "...", "url": "..."}
  },
  "policy_evidence": [...],
  "sentiment_evidence": [...],
  "metadata": {
    "created_at": "2025-01-15T10:30:00",
    "quality_metrics": {
      "overall_score": 0.87,
      "language_coverage": 8,
      "policy_evidence_count": 12,
      "sentiment_evidence_count": 25
    }
  }
}
```

## Dependencies

```txt
pydantic>=2.5.0
pyyaml>=6.0
aiosqlite>=0.19.0
sentence-transformers>=2.2.0  # For vector alignment
google-generativeai>=0.3.0    # For LLM alignment (optional)
```

Install:
```bash
pip install pydantic pyyaml aiosqlite sentence-transformers
```

## Environment Variables

For LLM alignment, set your API key:

```bash
# Gemini
export GEMINI_API_KEY="your-api-key"

# OpenAI
export OPENAI_API_KEY="your-api-key"
```

## Quality Report

After alignment, a quality report is generated at `dataset/quality_report.md`:

- Overall statistics (coverage, avg scores)
- Top 10 highest quality cells
- Cells requiring manual review
- Method performance comparison

## Extending

### Adding a New Aligner

1. Create `backend/aligners/my_aligner.py`
2. Inherit from `BaseAligner`
3. Implement the `align()` method
4. Register in `hybrid_aligner.py`

```python
from .base_aligner import BaseAligner, AlignmentResult

class MyAligner(BaseAligner):
    async def align(self, term, definition, candidates, layer):
        results = []
        for c in candidates:
            score = my_scoring_function(c)
            results.append(AlignmentResult(
                candidate_id=c['id'],
                score=score,
                method="my_method"
            ))
        return results
```

## License

MIT License - see project root LICENSE file.

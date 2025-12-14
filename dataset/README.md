# EconMind Matrix - Dataset README

This directory contains the exported corpus data from EconMind Matrix.

## File Formats

| File | Format | Description |
|:---|:---|:---|
| `terminology.jsonl` | JSON Lines | Main terminology data (ML-friendly) |
| `terminology.json` | JSON | Same data as array format |
| `terminology.csv` | CSV | Tabular format (Excel-compatible) |
| `terminology.tmx` | TMX | Translation Memory (CAT tools) |
| `policy_alignment.jsonl` | JSON Lines | Policy report alignments (Layer 2) |
| `news_sentiment.jsonl` | JSON Lines | News with sentiment labels (Layer 3) |
| `statistics.json` | JSON | Dataset statistics |

## Data Schema

### Terminology (Layer 1)

```json
{
  "id": 1,
  "term": "Inflation",
  "definitions": {
    "en": {
      "summary": "In economics, inflation is...",
      "url": "https://en.wikipedia.org/wiki/Inflation"
    },
    "zh": {
      "summary": "通货膨胀是指...",
      "url": "https://zh.wikipedia.org/wiki/通货膨胀"
    }
  },
  "related_terms": ["Deflation", "CPI", "Monetary_Policy"],
  "categories": ["Macroeconomics"]
}
```

### Policy Alignment (Layer 2)

```json
{
  "id": 1,
  "term": "Inflation",
  "pboc": {
    "source": "2024Q3 Monetary Policy Report",
    "text": "当前通胀水平保持温和..."
  },
  "fed": {
    "source": "December 2024 Beige Book",
    "text": "Prices continued to rise modestly..."
  },
  "similarity": 0.85
}
```

### News Sentiment (Layer 3)

```json
{
  "id": 1,
  "title": "Fed signals slower pace of rate cuts",
  "source": "Bloomberg",
  "date": "2024-12-13",
  "url": "https://...",
  "related_terms": ["Inflation", "Interest_Rate"],
  "sentiment": {
    "label": "bearish",
    "score": 0.82,
    "annotator": "llm",
    "verified": true
  }
}
```

## Usage Examples

### Python (pandas)

```python
import pandas as pd

# Load terminology
df = pd.read_json('terminology.jsonl', lines=True)
print(f"Total terms: {len(df)}")

# Search for a term
inflation = df[df['term'] == 'Inflation'].iloc[0]
print(inflation['definitions']['en']['summary'])
```

### Python (raw)

```python
import json

# Load line by line (memory efficient)
with open('terminology.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        term = json.loads(line)
        print(term['term'])
```

### CAT Tools (TMX)

Import `terminology.tmx` directly into:
- SDL Trados Studio
- memoQ
- OmegaT
- Memsource

## License

This dataset is released under the MIT License for academic and research use.

## Citation

If you use this dataset in your research, please cite:

```
@misc{econmind-matrix,
  title={EconMind Matrix: A Multi-Granularity Bilingual Corpus for Economic Analysis},
  author={...},
  year={2024},
  url={https://github.com/.../EconMind-Matrix}
}
```

## Contact

For questions about this dataset, please open an issue on GitHub.

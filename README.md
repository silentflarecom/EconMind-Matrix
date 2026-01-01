# EconMind Matrix

> **A Multi-Granularity Bilingual Corpus System for Economic Analysis**  
> An intelligent corpus platform integrating terminology, policy documents, and market sentiment

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org)
[![Status](https://img.shields.io/badge/status-active--development-orange.svg)](#-development-roadmap)

---

## 🎯 Project Overview

**EconMind Matrix** is an innovative multilingual corpus platform for economics, integrating three dimensions of data:

| Layer | Name | Content | Data Source |
|:---:|:---|:---|:---|
| **Layer 1** | Terminology Knowledge Base | 20+ language economic term definitions + Knowledge Graph | Wikipedia |
| **Layer 2** | Policy Parallel Corpus | Central bank report alignment (PBOC vs Fed) | Official Reports |
| **Layer 3** | Sentiment & Trend Corpus | Financial news + Sentiment labels + Time series | News Media |

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Sentiment & Trend Corpus                          │
│  📰 Financial News + Sentiment Labels + Term Trend Charts   │
└──────────────────────┬──────────────────────────────────────┘
                       │ Time Series Correlation
┌──────────────────────▼──────────────────────────────────────┐
│  Layer 2: Policy & Comparable Corpus                        │
│  📊 Central Bank Report Alignment (PBOC vs Fed)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Term Linking
┌──────────────────────▼──────────────────────────────────────┐
│  Layer 1: Terminology Knowledge Base                        │
│  📚 20+ Language Definitions + Knowledge Graph              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Core Features

### 🔍 Three-Layer Integrated Search
Search for "Inflation" and get:
- **Terminology Layer**: 20+ language professional definitions + related concept knowledge graph
- **Policy Layer**: PBOC vs Federal Reserve related paragraph comparison
- **Sentiment Layer**: Last 30 days news headlines + sentiment trend chart

### 📊 Intelligent Data Processing
- **Multilingual Support**: Covers 20+ languages including English, Chinese, Japanese, Korean, French, German, Russian
- **Chinese Conversion**: Automatic Traditional to Simplified Chinese conversion
- **Knowledge Graph**: D3.js visualization of term relationship networks

### 🤖 AI-Driven Annotation
- **LLM Pre-annotation**: Using Gemini/GPT for sentiment analysis and entity extraction
- **Human-in-the-Loop**: Doccano platform for expert verification
- **Quality Control**: Hybrid annotation accuracy > 90%

### 💾 Professional Export Formats
- **JSONL**: Machine learning training format
- **TMX**: Translation Memory (CAT tool compatible)
- **CSV/TSV**: Excel/Pandas friendly
- **TXT**: Human readable format

---

## 📁 Project Structure

```
EconMind-Matrix/
│
├── 📂 backend/                   # Layer 1: Terminology Backend (Complete)
│   ├── main.py                   # FastAPI server
│   ├── database.py               # Database operations
│   ├── models.py                 # Data models
│   ├── .env.example              # Environment configuration template
│   └── output/                   # Crawl results (Markdown)
│
├── 📂 frontend/                  # Layer 1: Vue.js Frontend (Complete)
│   ├── src/
│   │   ├── App.vue               # Main component
│   │   ├── components/           # UI components
│   │   └── services/api.js       # Centralized API service
│   ├── .env.development          # Dev environment config
│   ├── .env.production           # Prod environment config
│   └── package.json
│
├── 📂 shared/                    # Shared Utilities (NEW)
│   ├── __init__.py               # Package exports
│   ├── utils.py                  # Text utilities (clean_text)
│   ├── schema.py                 # Centralized DB schemas (11 tables)
│   ├── errors.py                 # Standardized error classes
│   ├── config.py                 # Configuration constants
│   └── README.md                 # Module documentation
│
├── 📂 layer2_policy/             # Layer 2: Policy Module (Complete)
│   ├── backend/
│   │   ├── api.py                # Policy API endpoints
│   │   ├── pdf_parser.py         # Marker PDF parsing
│   │   ├── alignment.py          # Sentence-BERT paragraph alignment
│   │   └── models.py             # Policy data models
│   └── data/
│       ├── pboc/                 # PBOC reports
│       └── fed/                  # Federal Reserve reports
│
├── 📂 layer3_sentiment/          # Layer 3: Sentiment Module (Complete)
│   ├── backend/
│   │   ├── api.py                # FastAPI sentiment endpoints
│   │   ├── database.py           # Sentiment database operations
│   │   └── models.py             # News & sentiment data models
│   ├── crawler/                  # News crawler
│   │   └── news_crawler.py       # RSS feed crawler (Bloomberg, Reuters, etc.)
│   ├── annotation/               # LLM annotation + Doccano integration
│   │   ├── llm_annotator.py      # Gemini API sentiment analysis
│   │   └── doccano_export.py     # Doccano import/export scripts
│   └── analysis/                 # Trend analysis
│       └── trend_analysis.py     # Time series analysis module
│
├── 📂 dataset/                   # Dataset export directory
│   ├── terminology.jsonl         # Layer 1 data
│   ├── policy_alignment.jsonl    # Layer 2 data
│   └── news_sentiment.jsonl      # Layer 3 data
│
├── 📂 scripts/                   # Automation scripts
│   ├── export_dataset.py         # Dataset export
│   └── crawl_all.py              # Batch crawling
│
├── 📂 docs/                      # Project documentation
│   ├── proposal.md               # Project proposal
│   ├── architecture.md           # Technical architecture
│   └── api.md                    # API documentation
│
├── pyproject.toml                # Python package configuration
├── README.md                     # This file
├── SETUP.md                      # Installation guide
└── LICENSE                       # MIT License
```

---

## 🚀 Quick Start

### Requirements
- Python 3.9+
- Node.js 16+
- Git

### Installation

```bash
# 1. Clone repository
git clone https://github.com/[your-username]/EconMind-Matrix.git
cd EconMind-Matrix

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Install frontend dependencies
cd ../frontend
npm install

# 4. Start backend server
cd ../backend
python main.py  # Runs on http://localhost:8000

# 5. Start frontend dev server
cd ../frontend
npm run dev  # Runs on http://localhost:5173
```

### ⚠️ Important Configuration
Visit the **Manage** page in the web interface to configure your User-Agent (required by Wikipedia API).  
See [SETUP.md](SETUP.md) for details.

---

## 📈 Development Roadmap

### ✅ Phase 1: Terminology Knowledge Base (Complete)
> Based on TermCorpusGenerator project

- [x] Wikipedia multilingual term crawling
- [x] 20+ language support (including Traditional/Simplified Chinese conversion)
- [x] Batch import and automated crawling
- [x] Intelligent association crawling (See Also, link analysis)
- [x] D3.js knowledge graph visualization
- [x] Multi-format export (JSON, JSONL, CSV, TSV, TMX, TXT)
- [x] Data quality analysis and cleaning tools
- [x] Database backup/restore functionality

### 🔄 Phase 2: Policy Parallel Corpus (Feature Complete & Tested)
> Target: Mid December 2025

**✅ Code Implementation Completed (2024-12-14):**

- [x] **Data Models** (`layer2-policy/backend/models.py`)
  - [x] PolicyReport, PolicyParagraph, PolicyAlignment dataclasses
  - [x] Database schema for Layer 2 tables
  - [x] 8 policy topics with bilingual keywords (inflation, employment, etc.)
  - [x] Topic detection via keyword matching

- [x] **PDF Parsing Module** (`layer2-policy/backend/pdf_parser.py`)
  - [x] Marker integration for AI-powered PDF→Markdown conversion
  - [x] PyPDF2 fallback for basic text extraction
  - [x] Automatic title and date extraction
  - [x] Paragraph splitting with topic detection
  - [x] Section-aware parsing for PBOC and Fed reports

- [x] **Paragraph Alignment Module** (`layer2-policy/backend/alignment.py`)
  - [x] Sentence-BERT semantic similarity (multilingual)
  - [x] Topic-based alignment fallback
  - [x] Keyword overlap fallback
  - [x] Embedding caching for performance
  - [x] Alignment History tracking
  - [x] Custom Topic Pool (User defined topics)

- [x] **Database Operations** (`layer2-policy/backend/database.py`)
  - [x] Async CRUD for reports, paragraphs, alignments
  - [x] Statistics endpoint
  - [x] Term search across policy paragraphs
  - [x] Quality score calculation with language breakdown

- [x] **API Endpoints** (`layer2-policy/backend/api.py`)
  - [x] POST `/upload` - Upload and parse PDF
  - [x] POST `/upload-text` - Upload text (testing)
  - [x] GET `/reports` - List reports
  - [x] POST `/align` - Run alignment
  - [x] GET `/alignments` - Query alignments
  - [x] GET `/topics` - List and manage topics
  - [x] GET `/stats` - Layer 2 statistics
  - [x] GET `/export/*` - Export Alignments (JSONL), Reports (JSONL), Parallel Corpus (TSV)

**✅ Completed Testing & Environment:**
- [x] Install dependencies: `torch`, `sentence-transformers` (Successfully installed)
- [x] Test PDF parsing with Marker
- [x] Test alignment with Sentence-BERT (High quality semantic matching enabled)
- [x] Integrate Layer 2 router into main.py
- [x] Frontend Component: PolicyCompare.vue with Topics, History, and Exports

### ✅ Phase 3: Sentiment & Trend Corpus (Complete)
> Completed: December 2025

**✅ Full Implementation Completed (2025-12-16):**

- [x] **Data Models** (`layer3-sentiment/backend/models.py`)
  - [x] NewsArticle, SentimentAnnotation, MarketContext dataclasses
  - [x] Database schema for Layer 3 tables
  - [x] Economic term variants (EN/ZH) for news filtering
  - [x] Sentiment labels: Bullish, Bearish, Neutral

- [x] **News Crawler** (`layer3-sentiment/crawler/news_crawler.py`)
  - [x] RSS feed integration (Bloomberg, Reuters, WSJ, FT, Xinhua, 21 sources)
  - [x] Async crawling with feedparser
  - [x] Term-based news filtering
  - [x] Automatic term detection from article content
  - [x] **User-Agent rotation pool** (8 browser UAs)
  - [x] **Proxy pool support** (http/https/socks5)
  - [x] **Concurrency control** (1-10 concurrent requests)
  - [x] **Custom delay** (0.5-10 seconds between requests)
  - [x] **Manual start/stop** control with verification

- [x] **LLM Sentiment Annotator** (`layer3-sentiment/annotation/llm_annotator.py`)
  - [x] Gemini API integration for sentiment analysis
  - [x] Bilingual prompt templates (EN/ZH)
  - [x] Rule-based fallback annotator (no API required)
  - [x] Hybrid annotator (optimizes API usage)
  - [x] Batch annotation with rate limiting

- [x] **Doccano Integration** (`layer3-sentiment/annotation/doccano_export.py`)
  - [x] JSONL export for Doccano platform
  - [x] CSV export for spreadsheet annotation
  - [x] Import verified annotations back to database
  - [x] Annotation quality checking

- [x] **Trend Analysis** (`layer3-sentiment/analysis/trend_analysis.py`)
  - [x] Daily term frequency calculation
  - [x] Sentiment distribution over time
  - [x] Trend direction detection (increasing/decreasing/stable)
  - [x] Market correlation analysis (optional)
  - [x] ECharts-compatible data generation

- [x] **API Endpoints** (`layer3-sentiment/backend/api.py`)
  - [x] POST `/crawl` - Crawl news from sources
  - [x] GET `/articles` - List articles
  - [x] POST `/annotate` - Run sentiment annotation
  - [x] GET `/trend/{term}` - Get term trend analysis
  - [x] GET `/trends/hot` - Get hot terms
  - [x] GET `/export/doccano` - Export for Doccano

- [x] **Frontend Component** (`frontend/src/components/SentimentAnalysis.vue`)
  - [x] Dashboard with sentiment statistics
  - [x] News crawling interface with advanced options
  - [x] Articles list with sentiment labels (search, filter, group by source)
  - [x] Trend analysis visualization
  - [x] Export options (JSON, JSONL, CSV, Doccano)
  - [x] **Running crawler detection** on page load
  - [x] **Force stop** with verification polling
  - [x] **Proxy pool configuration UI**

### 🎯 Phase 4: Offline Multi-Dimensional Semantic Alignment Pipeline (January-February 2026)

> **Critical Distinction**: Layer 4 is **NOT a user interface** - it is an **offline batch processing engine** that consumes completed data from Layers 1-3 and produces publication-ready aligned datasets.

---

#### 🏭 Architectural Role: The "Alignment Factory"

**Input → Process → Output Model:**
```
Layer 1 Data (corpus.db)  ──┐
Layer 2 Data (corpus.db)  ──┼──→ Alignment Engine ──→ Unified Dataset File
Layer 3 Data (corpus.db)  ──┘   (Batch Pipeline)       (aligned_corpus.jsonl)
```

**What Layer 4 Does:**
1. **Enumerates** all successfully crawled terms from Layer 1
2. **Searches** Layer 2/3 for content related to each term (across ALL supported languages)
3. **Aligns** using multiple strategies (LLM, vectors, rules) to determine semantic relevance
4. **Aggregates** aligned evidence into structured "Knowledge Cells"
5. **Exports** publication-ready datasets in standardized formats (JSONL, CSV, etc.)
6. **Reports** data quality metrics (coverage, alignment scores, language distribution)

**What Layer 4 Does NOT Do:**
- ❌ Provide real-time user search interfaces (that's the frontend's job)
- ❌ Store data in its own database (reads from Layer 1-3 databases)
- ❌ Crawl or collect raw data (Layers 1-3 handle this)

---

#### 🗂️ Module Structure

```
layer4_alignment/
├── backend/
│   ├── alignment_engine.py       # Core orchestration logic
│   ├── data_loader.py             # Load data from Layer 1-3 databases
│   ├── knowledge_cell.py          # Knowledge Cell data model (Pydantic)
│   ├── aligners/                  # Pluggable alignment strategies
│   │   ├── llm_aligner.py         # Gemini/GPT-4 semantic judgment
│   │   ├── vector_aligner.py      # Sentence-BERT cosine similarity
│   │   ├── rule_aligner.py        # Keyword + TF-IDF matching
│   │   └── hybrid_aligner.py      # Weighted ensemble of above methods
│   ├── exporters/
│   │   ├── jsonl_exporter.py      # JSONL dataset export
│   │   ├── csv_exporter.py        # Spreadsheet-friendly export
│   │   └── quality_reporter.py    # Statistics and quality metrics
│   └── utils/
│       ├── wikidata_client.py     # Fetch Wikidata QIDs for terms
│       └── text_processor.py      # Multilingual text normalization
├── config/
│   ├── alignment_config.yaml      # Alignment strategy settings
│   └── language_support.yaml      # Language priority and mappings
├── scripts/
│   ├── run_full_alignment.py      # Batch process all terms
│   ├── incremental_update.py      # Process newly added terms only
│   └── validate_output.py         # Verify dataset integrity
└── README.md
```

---

#### ⚙️ Alignment Strategies (Multi-Method Ensemble)

Layer 4 employs **4 complementary alignment methods** to maximize accuracy:

##### 1. **LLM Semantic Alignment** (Primary, Weight: 50%)
- **Model**: Gemini 1.5 Pro / GPT-4 Turbo
- **Method**: Present term definition + candidate texts to LLM, ask for relevance scoring (0-1)
- **Prompt Example**:
  ```
  Term: "Inflation" (Definition: In economics, inflation is a general rise in prices...)
  
  Rate each policy paragraph's relevance to this concept (0-1 scale):
  [0] "Current inflation remains moderate, CPI rose 0.4% YoY..."  → Score: ?
  [1] "Export growth accelerated in Q3..."                        → Score: ?
  ```
- **Advantages**: Understands context, handles paraphrasing, detects conceptual matches
- **Limitations**: API costs, rate limits, requires careful prompt engineering

##### 2. **Vector Similarity Alignment** (Secondary, Weight: 30%)
- **Model**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- **Method**: 
  1. Encode term definition into 768-dim vector
  2. Encode each candidate paragraph/article into vectors
  3. Calculate cosine similarity
  4. Accept matches above threshold (e.g., >0.65)
- **Advantages**: Fast, free, works offline, multilingual support
- **Limitations**: May miss conceptual matches if wording differs significantly

##### 3. **Rule-Based Keyword Matching** (Fallback, Weight: 15%)
- **Method**:
  1. Extract keywords from term (+ synonyms from Layer 1's `related_terms`)
  2. Calculate TF-IDF scores in candidate texts
  3. Fuzzy matching for inflected forms (e.g., "inflate" → "inflation")
- **Advantages**: Explainable, deterministic, no API dependencies
- **Limitations**: Purely lexical, misses semantic equivalents

##### 4. **Hybrid Ensemble** (Weight: 5% as tie-breaker)
- **Method**: Weighted vote of above 3 methods
- **Formula**: `Final_Score = 0.50×LLM + 0.30×Vector + 0.15×Rule + 0.05×Ensemble_Bonus`
- **Ensemble Bonus**: +0.05 if all 3 methods agree (high confidence indicator)

**Filtering Threshold**: Only matches with `Final_Score ≥ 0.65` are included in the Knowledge Cell.

---

#### 📐 Knowledge Cell Data Model

Each term produces **one Knowledge Cell**, which is the atomic unit of the aligned dataset:

```json
{
  "concept_id": "Q17127698",                    // Wikidata QID (or TERM_<id> if unavailable)
  "primary_term": "Inflation",                  // English canonical term
  
  "definitions": {                              // Layer 1: Multilingual definitions
    "en": {
      "term": "Inflation",
      "summary": "In economics, inflation is a general rise in the price level...",
      "url": "https://en.wikipedia.org/wiki/Inflation",
      "source": "Wikipedia"
    },
    "zh": {
      "term": "通货膨胀",
      "summary": "通货膨胀是指一般物价水平在一定时期内持续上涨...",
      "url": "https://zh.wikipedia.org/wiki/通货膨胀",
      "source": "Wikipedia"
    },
    "ja": {...},
    "ko": {...}
    // All languages supported by Layer 1
  },
  
  "policy_evidence": [                          // Layer 2: Aligned policy paragraphs
    {
      "source": "pboc",
      "paragraph_id": 42,
      "text": "当前通胀保持温和，CPI同比上涨0.4%，核心CPI上涨0.3%...",
      "topic": "price_stability",
      "alignment_scores": {
        "llm": 0.92,
        "vector": 0.78,
        "rule": 0.85,
        "final": 0.88
      },
      "alignment_method": "hybrid_ensemble",
      "report_metadata": {
        "title": "2024年第三季度中国货币政策执行报告",
        "date": "2024-11-08",
        "section": "Part II: Monetary Policy Operations"
      }
    },
    {
      "source": "fed",
      "paragraph_id": 156,
      "text": "Prices continued to rise modestly across most districts. Retail prices increased...",
      "topic": "inflation",
      "alignment_scores": {...},
      "report_metadata": {...}
    }
  ],
  
  "sentiment_evidence": [                       // Layer 3: Aligned news articles
    {
      "article_id": 1523,
      "title": "Fed signals slower pace of rate cuts amid sticky inflation",
      "source": "Bloomberg",
      "url": "https://www.bloomberg.com/...",
      "published_date": "2024-12-13",
      "sentiment": {
        "label": "bearish",
        "confidence": 0.82,
        "annotator": "gemini-1.5-flash"
      },
      "alignment_scores": {
        "llm": 0.95,
        "vector": 0.89,
        "rule": 0.72,
        "final": 0.91
      }
    },
    {...}
  ],
  
  "metadata": {
    "created_at": "2025-01-15T10:23:45Z",
    "alignment_engine_version": "4.0.0",
    "quality_metrics": {
      "overall_score": 0.87,              // Weighted avg of all alignment scores
      "language_coverage": 8,              // Number of languages with definitions
      "policy_evidence_count": 12,         // PBOC + Fed paragraphs aligned
      "sentiment_evidence_count": 25,      // News articles aligned (last 90 days)
      "avg_policy_score": 0.84,
      "avg_sentiment_score": 0.89
    }
  }
}
```

---

#### 🔧 Configuration System

**File**: `layer4_alignment/config/alignment_config.yaml`

```yaml
# Alignment Strategy Settings
alignment_strategies:
  llm_semantic:
    enabled: true
    provider: "gemini"              # or "openai", "deepseek"
    model: "gemini-1.5-pro"
    api_key_env: "GEMINI_API_KEY"
    temperature: 0.1
    max_tokens: 500
    batch_size: 10                  # Process 10 candidates per LLM call
    threshold: 0.70
    weight: 0.50
    
  vector_similarity:
    enabled: true
    model: "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    device: "cuda"                  # or "cpu"
    threshold: 0.65
    weight: 0.30
    
  keyword_matching:
    enabled: true
    use_fuzzy: true
    fuzzy_threshold: 0.85
    tfidf_top_k: 20
    threshold: 0.60
    weight: 0.15

# Global Settings
global:
  min_final_score: 0.65             # Discard alignments below this
  max_policy_evidence: 15           # Top N policy paragraphs per term
  max_sentiment_evidence: 30        # Top N news articles per term
  sentiment_time_window_days: 90    # Only recent news
  
# Language Support (inherits from Layer 1)
languages:
  priority: ["en", "zh", "ja", "ko", "fr", "de", "es", "ru"]
  fallback_language: "en"

# Output Settings
output:
  format: "jsonl"                   # or "json", "csv"
  output_dir: "dataset"
  filename_template: "aligned_corpus_v{version}_{date}.jsonl"
  include_metadata: true
  compress: false                   # Set true to generate .jsonl.gz

# Quality Reporting
quality_report:
  enabled: true
  output_path: "dataset/quality_report.md"
  visualizations: true              # Generate charts if matplotlib available
```

---

#### 🚀 Execution Workflow

**Full Alignment Run** (one-time or periodic):
```bash
cd layer4_alignment
python scripts/run_full_alignment.py --config config/alignment_config.yaml
```

**Console Output Example**:
```
========================================
Layer 4 Alignment Engine v4.0.0
========================================
[INFO] Loading configuration from alignment_config.yaml
[INFO] Initializing aligners: LLM (Gemini) + Vector (SBERT) + Rule
[INFO] Loading Layer 1 terms from corpus.db... Found 287 terms
[INFO] Loading Layer 2 policy corpus... 1,234 paragraphs (PBOC: 623, Fed: 611)
[INFO] Loading Layer 3 news articles... 4,567 articles (last 90 days)

[1/287] Aligning term: "Inflation" (8 languages)
  ├─ Layer 2: Found 45 candidate paragraphs
  │   ├─ LLM filtering: 12 relevant (scores 0.70-0.95)
  │   ├─ Vector filtering: 18 relevant (scores 0.65-0.88)
  │   └─ Ensemble: 14 final matches (avg score 0.84)
  ├─ Layer 3: Found 128 candidate articles
  │   └─ Ensemble: 27 final matches (avg score 0.87)
  └─ Knowledge Cell quality: 0.86 ✓

[2/287] Aligning term: "GDP" (7 languages)
  ...

[287/287] Aligning term: "Quantitative Easing" (5 languages)
  └─ Knowledge Cell quality: 0.79 ✓

========================================
Alignment Complete!
========================================
Output: dataset/aligned_corpus_v1_2025-01-15.jsonl
Total Knowledge Cells: 287
Avg Quality Score: 0.82
Time Elapsed: 2h 34m

Generating quality report... ✓
Report saved to: dataset/quality_report.md
```

**Incremental Update** (for newly added terms):
```bash
python scripts/incremental_update.py --since "2025-01-15"
```

---

#### 📊 Output Dataset Formats

##### Format 1: JSONL (Primary, ML-Ready)
- **File**: `aligned_corpus_v1_2025-01-15.jsonl`
- **Structure**: One Knowledge Cell per line (newline-delimited JSON)
- **Size**: ~500 KB per 100 terms (uncompressed)
- **Use Case**: LLM fine-tuning, batch processing, streaming ingestion

##### Format 2: CSV (Analysis-Friendly)
- **File**: `aligned_corpus_v1_2025-01-15.csv`
- **Columns**:
  ```
  concept_id, term_en, term_zh, term_ja, ..., 
  policy_count, sentiment_count, quality_score, 
  top_policy_source, top_sentiment_label
  ```
- **Use Case**: Excel analysis, Pandas dataframes, visualization

##### Format 3: Quality Report (Markdown)
- **File**: `quality_report.md`
- **Contents**:
  - Overall statistics (total cells, avg scores, language distribution)
  - Top 10 highest quality cells
  - Bottom 10 cells requiring manual review
  - Alignment method performance comparison
  - Visualizations (if enabled): bar charts, heatmaps

---

#### 📈 Success Metrics

| Metric | Target | Description |
|:---|:---:|:---|
| **Coverage Rate** | ≥ 80% | % of Layer 1 terms with aligned Layer 2+3 data |
| **Avg Alignment Score** | ≥ 0.75 | Mean of all `final_score` values |
| **Language Completeness** | ≥ 5 langs/term | Average languages with definitions per cell |
| **Policy Evidence Density** | ≥ 3 paragraphs/term | Avg aligned policy paragraphs per cell |
| **Sentiment Evidence Density** | ≥ 10 articles/term | Avg aligned news articles per cell |
| **Processing Speed** | ≤ 30s/term | Time to align one term (all layers) |

---

#### 🔄 Integration with Other Phases

**Inputs from Previous Phases:**
- **Layer 1** → Provides canonical terms + multilingual definitions + Wikidata QIDs
- **Layer 2** → Provides policy paragraphs tagged with topics
- **Layer 3** → Provides sentiment-annotated news + trend data

**Outputs for Next Phase:**
- **Phase 5** → Publication-ready datasets for competition submission
- **Frontend** → (Optional) Pre-computed aligned data for fast UI loading
- **External Users** → High-quality training data for domain-specific LLMs

---

#### 🛠️ Technical Requirements

**Dependencies:**
```txt
# Core
pydantic>=2.5.0
pyyaml>=6.0
aiosqlite>=0.19.0

# Alignment Methods
google-generativeai>=0.3.0      # Gemini API
openai>=1.6.0                   # GPT-4 API (optional)
sentence-transformers>=2.2.0    # Vector embeddings
scikit-learn>=1.3.0             # TF-IDF, cosine similarity

# Utilities
requests>=2.31.0                # Wikidata API
tqdm>=4.66.0                    # Progress bars
pandas>=2.0.0                   # Data export
```

**Hardware Recommendations:**
- **CPU**: 4+ cores (for parallel processing)
- **RAM**: 8GB+ (for embedding model caching)
- **GPU**: Optional but recommended for vector embeddings (CUDA-compatible)
- **Storage**: 2GB for models + 500MB for output datasets

---

#### 🎯 Deliverables (Phase 4 Completion Checklist)

- [ ] **Core Engine**
  - [ ] `AlignmentEngine` class with multi-strategy support
  - [ ] `KnowledgeCell` Pydantic model with full schema
  - [ ] Database loaders for Layer 1/2/3
  - [ ] Wikidata QID fetcher and cacher

- [ ] **Alignment Strategies**
  - [ ] LLM aligner (Gemini + fallback to GPT-4)
  - [ ] Vector aligner (Sentence-BERT)
  - [ ] Rule-based aligner (keyword + TF-IDF)
  - [ ] Hybrid ensemble aggregator

- [ ] **Export System**
  - [ ] JSONL exporter with compression support
  - [ ] CSV exporter with multilingual handling
  - [ ] Quality report generator (Markdown + charts)

- [ ] **Scripts & Tools**
  - [ ] Full alignment runner (`run_full_alignment.py`)
  - [ ] Incremental updater (`incremental_update.py`)
  - [ ] Output validator (`validate_output.py`)
  - [ ] Configuration validator

- [ ] **Documentation**
  - [ ] README.md with usage examples
  - [ ] Configuration guide (YAML options explained)
  - [ ] Alignment strategy comparison table
  - [ ] Troubleshooting guide

- [ ] **Testing & Validation**
  - [ ] Unit tests for each aligner
  - [ ] Integration test with sample data
  - [ ] Performance benchmarks
  - [ ] Output schema validation

### 🏆 Phase 5: Competition Submission (March 2026)

- [ ] **Documentation**
  - [x] Technical architecture (`docs/architecture.md`)
  - [x] API documentation (`docs/api.md`)
  - [ ] Full technical solution document (30-50 pages)
  - [ ] Dataset description document

- [ ] **Demo Preparation**
  - [ ] Online demo deployment (Vercel + Railway)
  - [ ] Demo video production (5-10 min)
  - [ ] PPT presentation materials

- [ ] **Data Scale Targets**
  - [ ] 500+ economic terms × 20 languages
  - [ ] 10+ policy report alignments
  - [ ] 5000+ news sentiment annotations

---

## 📋 Current Development Status

**Last Updated:** 2024-12-16 23:00

### What's Completed

| Component | Status | Files |
|:----------|:------:|:------|
| Layer 1 Backend | ✅ Complete | `backend/main.py`, `database.py`, etc. |
| Layer 1 Frontend | ✅ Complete | `frontend/src/` (6 components) |
| Layer 2 Models | ✅ Complete | `layer2-policy/backend/models.py` |
| Layer 2 PDF Parser | ✅ Complete | `layer2-policy/backend/pdf_parser.py` |
| Layer 2 Alignment | ✅ Complete | `layer2-policy/backend/alignment.py` |
| Layer 2 Database | ✅ Complete | `layer2-policy/backend/database.py` |
| Layer 2 API | ✅ Complete | `layer2-policy/backend/api.py` |
| Layer 2 Frontend | ✅ Complete | `frontend/src/components/PolicyCompare.vue` |
| Layer 3 Models | ✅ Complete | `layer3_sentiment/backend/models.py` |
| Layer 3 Database | ✅ Complete | `layer3_sentiment/backend/database.py` |
| Layer 3 Crawler | ✅ Complete | `layer3_sentiment/crawler/news_crawler.py` |
| Layer 3 Annotator | ✅ Complete | `layer3_sentiment/annotation/llm_annotator.py` |
| Layer 3 Doccano | ✅ Complete | `layer3_sentiment/annotation/doccano_export.py` |
| Layer 3 Trends | ✅ Complete | `layer3_sentiment/analysis/trend_analysis.py` |
| Layer 3 API | ✅ Complete | `layer3_sentiment/backend/api.py` |
| Layer 3 Frontend | ✅ Complete | `frontend/src/components/SentimentAnalysis.vue` |
| Export Scripts | 🔧 Framework | `scripts/export_dataset.py` |
| Documentation | ✅ Complete | `docs/architecture.md`, `docs/api.md` |

### Latest Updates (2024-12-29)

**🔧 Technical Debt Remediation Complete:**
- ✅ Created `shared/` module with centralized utilities
- ✅ Centralized database schemas (11 tables in `shared/schema.py`)
- ✅ Standardized error handling (`shared/errors.py`)
- ✅ Replaced all hardcoded API URLs with environment-aware configuration
- ✅ Added type hints to core functions
- ✅ Environment-aware CORS configuration
- ✅ Centralized configuration constants (`shared/config.py`)

**📁 New `shared/` Module:**
```python
from shared.utils import clean_text
from shared.schema import LAYER1_SQL_SCHEMA, ALL_TABLES
from shared.errors import NotFoundError, ValidationError
from shared.config import DEFAULT_CRAWL_INTERVAL, SUPPORTED_LANGUAGES
```

**🌐 Frontend API Configuration:**
```javascript
// frontend/src/services/api.js
import { API_BASE } from './services/api'
// Uses VITE_API_BASE_URL from .env.development or .env.production
```

### Previous Updates (2024-12-16)

**🔧 Crawler Enhancements:**
- User-Agent rotation pool (8 realistic browser UAs)
- Proxy pool support (http/https/socks5 protocols)
- Concurrency control (1-10 parallel requests)
- Custom delay settings (0.5-10 seconds)
- Manual start/stop with verification polling
- Running crawler detection on page load

**🛡️ System Page Improvements:**
- Three-layer statistics display (Layer 1, 2, 3)
- Separate backup buttons for each layer's database
- All-layers reset functionality
- Enhanced reset confirmation with layer breakdown

**📊 Backup Endpoints:**
- `GET /api/system/backup` - Layer 1 (corpus.db)
- `GET /api/policy/backup` - Layer 2 (policy_corpus.db)
- `GET /api/sentiment/backup` - Layer 3 (sentiment_corpus.db)

### Next Actions

1. **Phase 4 Integration**
   - Unified Search across all 3 layers
   - Integrated Dashboard/Knowledge Graph
   - Cross-layer term linking


---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|:---|:---|
| **FastAPI** | Web framework |
| **SQLite + aiosqlite** | Async database |
| **Wikipedia-API** | Term crawling |
| **zhconv** | Chinese conversion |
| **Marker** | PDF parsing (Layer 2) |
| **Sentence-BERT** | Semantic alignment (Layer 2) |
| **Gemini API** | Sentiment annotation (Layer 3) |

### Frontend
| Technology | Purpose |
|:---|:---|
| **Vue 3 + Vite** | Frontend framework |
| **TailwindCSS** | UI styling |
| **D3.js** | Knowledge graph visualization |
| **ECharts** | Trend charts (Layer 3) |
| **Axios** | HTTP client |

### Data Formats
| Format | Purpose |
|:---|:---|
| **JSONL** | Primary data format (ML friendly) |
| **TMX** | Translation Memory (CAT tools) |
| **CSV/TSV** | General tables (Excel) |

---

## 📊 Dataset Preview

### Layer 1: Terminology Data Sample
```json
{
  "id": 1,
  "term": "Inflation",
  "definitions": {
    "en": {"summary": "In economics, inflation is...", "url": "https://..."},
    "zh": {"summary": "通货膨胀是指...", "url": "https://..."},
    "ja": {"summary": "インフレーションとは...", "url": "https://..."}
  },
  "related_terms": ["Deflation", "CPI", "Monetary_Policy"],
  "categories": ["Macroeconomics"]
}
```

### Layer 2: Policy Alignment Data Sample
```json
{
  "term": "Inflation",
  "pboc": {
    "source": "2024Q3 Monetary Policy Report",
    "text": "Current inflation remains moderate, CPI rose 0.4% YoY..."
  },
  "fed": {
    "source": "2024 December Beige Book",
    "text": "Prices continued to rise modestly across most districts..."
  },
  "similarity": 0.85
}
```

### Layer 3: News Sentiment Data Sample
```json
{
  "id": 1,
  "title": "Fed signals slower pace of rate cuts amid sticky inflation",
  "source": "Bloomberg",
  "date": "2024-12-13",
  "related_terms": ["Inflation", "Interest_Rate"],
  "sentiment": {"label": "bearish", "score": 0.82},
  "market_context": {"sp500_change": -0.54}
}
```

---

## 🌟 Innovation Highlights

### 1. Three-Layer Vertical Architecture
- Breaking the single-dimension limitation of traditional corpora
- Full chain tracking from "term definition → policy application → market reaction"

### 2. AI-Driven Efficiency Boost
- Marker solves PDF table/formula parsing challenges
- LLM pre-annotation + human verification, 10x efficiency improvement

### 3. Time Series Economic Insights
- Term frequency overlaid with market index analysis
- Corpus with economic forecasting potential

### 4. Multi-Scenario Applications
- **Researchers**: Policy comparison + trend analysis
- **Translators**: TMX translation memory
- **Analysts**: Sentiment monitoring dashboard

---

## ⚖️ Data Compliance

- ✅ Only collecting public data (government reports, Wikipedia)
- ✅ News stores only summaries/headlines + original links
- ✅ Compliant with Wikipedia API User-Agent Policy
- ✅ Non-commercial academic research project

---

## 🤝 Contributing

We welcome contributors with the following backgrounds:
- **Economics/Trade**: Term selection, policy interpretation
- **Languages/Translation**: Doccano annotation verification
- **Computer Science**: Algorithm optimization, visualization

### Contribution Process
1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push branch (`git push origin feature/AmazingFeature`)
5. Create Pull Request

---

## 📚 Documentation

- [Installation Guide](SETUP.md)
- [Project Proposal](docs/proposal.md)
- [Technical Architecture](docs/architecture.md)
- [API Documentation](docs/api.md)

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **PDF Parsing**: [Marker](https://github.com/VikParuchuri/marker)
- **Annotation Platform**: [Doccano](https://github.com/doccano/doccano)
- **Semantic Model**: [Sentence-BERT](https://www.sbert.net/)
- **Base Project**: [TermCorpusGenerator](https://github.com/silentflarecom/TermCorpusGenerator)

---

<p align="center">
  <b>⭐ If this project helps you, please give us a Star!</b>
</p>

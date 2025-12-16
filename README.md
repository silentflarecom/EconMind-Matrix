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
│   └── output/                   # Crawl results (Markdown)
│
├── 📂 frontend/                  # Layer 1: Vue.js Frontend (Complete)
│   ├── src/
│   │   ├── App.vue               # Main component
│   │   └── components/           # UI components
│   └── package.json
│
├── 📂 layer2-policy/             # Layer 2: Policy Module (In Development)
│   ├── backend/
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

### 🎯 Phase 4: Three-Layer Integration (February 2026)

- [ ] **Unified API**
  - [ ] `/api/v1/search/{term}` → Returns three-layer data
  - [ ] `/api/v1/trend/{term}` → Returns time series data
  - [ ] Layer 2 `/policy/search/{term}` already implemented

- [ ] **Integrated Interface**
  - [ ] Three-column layout (Definition | Policy | Sentiment)
  - [ ] Interactive knowledge graph with policy links
  - [ ] Trend chart visualization

- [ ] **Dataset Export**
  - [x] Export script structure (`scripts/export_dataset.py`)
  - [ ] Complete dataset packaging
  - [ ] Statistics report generation

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

### Latest Updates (2024-12-16)

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

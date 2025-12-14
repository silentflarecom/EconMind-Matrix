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
├── 📂 layer3-sentiment/          # Layer 3: Sentiment Module (Planned)
│   ├── crawler/                  # News crawler
│   ├── annotation/               # LLM annotation + Doccano integration
│   └── analysis/                 # Trend analysis
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

### 🔄 Phase 2: Policy Parallel Corpus (In Progress)
> Target: End of December 2025

- [ ] **PDF Parsing Module**
  - [ ] Install and configure Marker (AI PDF → Markdown)
  - [ ] Parse PBOC "Monetary Policy Implementation Report"
  - [ ] Parse Fed Beige Book / FOMC Minutes
  
- [ ] **Paragraph Alignment Module**
  - [ ] Sentence-BERT semantic similarity calculation
  - [ ] Topic-level alignment (inflation, employment, interest rates, etc.)
  - [ ] Alignment result storage and export

- [ ] **Frontend Display**
  - [ ] Policy comparison view component
  - [ ] Side-by-side dual column display

### 📅 Phase 3: Sentiment & Trend Corpus (January 2026)

- [ ] **News Crawler**
  - [ ] RSS Feed parsing (Bloomberg, Reuters)
  - [ ] Chinese financial news sources (Caixin, Yicai)
  - [ ] Rate limiting and compliance handling

- [ ] **Sentiment Annotation**
  - [ ] Gemini API pre-annotation (bullish/bearish/neutral)
  - [ ] Doccano platform deployment
  - [ ] Human-in-the-loop verification workflow

- [ ] **Trend Analysis**
  - [ ] Term frequency time series
  - [ ] Market index overlay (S&P500, Shanghai Composite)
  - [ ] ECharts visualization

### 🎯 Phase 4: Three-Layer Integration (February 2026)

- [ ] **Unified API**
  - [ ] `/search/{term}` → Returns three-layer data
  - [ ] `/trend/{term}` → Returns time series data
  - [ ] `/compare` → Policy comparison endpoint

- [ ] **Integrated Interface**
  - [ ] Three-column layout (Definition | Policy | Sentiment)
  - [ ] Interactive knowledge graph
  - [ ] Trend chart visualization

- [ ] **Dataset Export**
  - [ ] Complete dataset packaging
  - [ ] Statistics report generation
  - [ ] Quality validation tools

### 🏆 Phase 5: Competition Submission (March 2026)

- [ ] **Documentation**
  - [ ] Technical solution document (30-50 pages)
  - [ ] Dataset description document
  - [ ] API usage documentation

- [ ] **Demo Preparation**
  - [ ] Online demo deployment
  - [ ] Demo video production
  - [ ] PPT presentation materials

- [ ] **Data Scale Targets**
  - [ ] 500+ economic terms × 20 languages
  - [ ] 10+ policy report alignments
  - [ ] 5000+ news sentiment annotations

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

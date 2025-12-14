# EconMind Matrix - Technical Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EconMind Matrix System                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Layer 1   │  │   Layer 2   │  │   Layer 3   │         │
│  │ Terminology │  │   Policy    │  │  Sentiment  │         │
│  │ (Complete)  │  │(In Progress)│  │  (Planned)  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                   ┌──────▼──────┐                           │
│                   │ Unified API │                           │
│                   │  (FastAPI)  │                           │
│                   └──────┬──────┘                           │
│                          │                                  │
│                   ┌──────▼──────┐                           │
│                   │ SQLite DB   │                           │
│                   └─────────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                   ┌──────▼──────┐
                   │ Vue.js UI   │
                   │ + D3.js     │
                   │ + ECharts   │
                   └─────────────┘
```

---

## Layer 1: Terminology Knowledge Base

### Data Flow

```
Wikipedia → wikipedia-api → Cleaning/Transform → SQLite → API → Frontend
                                   ↓
                          zhconv (Chinese conversion)
```

### Technology Stack

| Component | Technology | Description |
|:---|:---|:---|
| Data Collection | wikipedia-api | Official MediaWiki API wrapper |
| Chinese Processing | zhconv | Traditional→Simplified conversion |
| Data Storage | SQLite | Lightweight local database |
| API Framework | FastAPI | Async high-performance web framework |
| Visualization | D3.js | Knowledge graph force-directed layout |

### Database Schema

```sql
-- Batch tasks
CREATE TABLE batch_tasks (
    id INTEGER PRIMARY KEY,
    status TEXT,
    total_terms INTEGER,
    completed_terms INTEGER,
    max_depth INTEGER DEFAULT 1,
    target_languages TEXT DEFAULT 'en,zh'
);

-- Terms table
CREATE TABLE terms (
    id INTEGER PRIMARY KEY,
    term TEXT NOT NULL,
    status TEXT,
    translations TEXT,  -- JSON: {"lang": {"summary": "...", "url": "..."}}
    depth_level INTEGER DEFAULT 0,
    source_term_id INTEGER
);

-- Term associations
CREATE TABLE term_associations (
    id INTEGER PRIMARY KEY,
    source_term_id INTEGER,
    target_term TEXT,
    association_type TEXT,
    weight REAL DEFAULT 1.0
);
```

### API Endpoints (Layer 1)

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/term/{term}` | Get single term data |
| POST | `/api/batch` | Start batch crawl task |
| GET | `/api/tasks` | List all tasks |
| GET | `/api/tasks/{id}` | Get task details |
| GET | `/api/tasks/{id}/results` | Get task results |
| GET | `/api/export/{format}` | Export data (json/csv/tmx) |
| GET | `/api/graph/{task_id}` | Get knowledge graph data |

---

## Layer 2: Policy Parallel Corpus

### Data Flow

```
PDF Reports → Marker → Markdown → Paragraph Split → Sentence-BERT → Alignment → SQLite
     ↓                                   ↓
   PBOC                                 Fed
```

### Technology Stack

| Component | Technology | Description |
|:---|:---|:---|
| PDF Parsing | Marker | AI-driven PDF→Markdown conversion |
| Semantic Alignment | Sentence-BERT | Multilingual semantic similarity |
| Topic Extraction | BERTopic | Topic clustering analysis |

### Database Schema (Extension)

```sql
-- Policy reports
CREATE TABLE policy_reports (
    id INTEGER PRIMARY KEY,
    source TEXT,           -- 'pboc' or 'fed'
    title TEXT,
    report_date DATE,
    raw_text TEXT,
    parsed_markdown TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Report paragraphs
CREATE TABLE policy_paragraphs (
    id INTEGER PRIMARY KEY,
    report_id INTEGER,
    paragraph_index INTEGER,
    paragraph_text TEXT,
    topic TEXT,            -- Topic label: inflation, employment, etc.
    embedding BLOB,        -- Sentence-BERT embedding vector
    FOREIGN KEY (report_id) REFERENCES policy_reports(id)
);

-- Paragraph alignments
CREATE TABLE policy_alignments (
    id INTEGER PRIMARY KEY,
    pboc_paragraph_id INTEGER,
    fed_paragraph_id INTEGER,
    similarity_score REAL,
    alignment_method TEXT,  -- 'sentence-bert' or 'topic'
    term_id INTEGER,        -- Related terminology term
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pboc_paragraph_id) REFERENCES policy_paragraphs(id),
    FOREIGN KEY (fed_paragraph_id) REFERENCES policy_paragraphs(id),
    FOREIGN KEY (term_id) REFERENCES terms(id)
);
```

### API Endpoints (Layer 2)

| Method | Endpoint | Description |
|:---|:---|:---|
| POST | `/api/policy/upload` | Upload PDF report |
| GET | `/api/policy/reports` | List all reports |
| GET | `/api/policy/paragraphs/{report_id}` | Get paragraphs |
| GET | `/api/policy/align/{term}` | Get alignments for term |
| POST | `/api/policy/align` | Run alignment process |

---

## Layer 3: Sentiment & Trend Corpus

### Data Flow

```
News Sources (RSS) → Crawler → Gemini Pre-annotation → Doccano Review → SQLite → Trend Analysis
                                                                           ↓
                                                              Market Data API (Stock Index)
```

### Technology Stack

| Component | Technology | Description |
|:---|:---|:---|
| News Collection | feedparser | RSS parsing |
| Sentiment Analysis | Gemini API | LLM pre-annotation |
| Human Review | Doccano | Annotation platform |
| Trend Visualization | ECharts | Time series charts |

### Database Schema (Extension)

```sql
-- News items
CREATE TABLE news_items (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT,           -- 'bloomberg', 'reuters', 'caixin'
    url TEXT,
    published_date DATE,
    summary TEXT,
    full_text TEXT,        -- Optional, for fair use compliance
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sentiment annotations
CREATE TABLE news_sentiment (
    id INTEGER PRIMARY KEY,
    news_id INTEGER,
    sentiment_label TEXT,   -- 'bullish', 'bearish', 'neutral'
    sentiment_score REAL,   -- Confidence score 0-1
    annotator TEXT,         -- 'llm' or 'human'
    annotator_id TEXT,      -- Specific model or user
    verified BOOLEAN DEFAULT FALSE,
    verified_by TEXT,
    verified_at DATETIME,
    FOREIGN KEY (news_id) REFERENCES news_items(id)
);

-- News-term links
CREATE TABLE news_term_links (
    id INTEGER PRIMARY KEY,
    news_id INTEGER,
    term_id INTEGER,
    relevance_score REAL,
    FOREIGN KEY (news_id) REFERENCES news_items(id),
    FOREIGN KEY (term_id) REFERENCES terms(id)
);

-- Market data
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE,
    sp500_open REAL,
    sp500_close REAL,
    sp500_change REAL,
    shanghai_open REAL,
    shanghai_close REAL,
    shanghai_change REAL
);

-- Term trends (aggregated)
CREATE TABLE term_trends (
    id INTEGER PRIMARY KEY,
    term_id INTEGER,
    date DATE,
    news_count INTEGER,
    avg_sentiment REAL,
    FOREIGN KEY (term_id) REFERENCES terms(id),
    UNIQUE(term_id, date)
);
```

### API Endpoints (Layer 3)

| Method | Endpoint | Description |
|:---|:---|:---|
| POST | `/api/news/crawl` | Start news crawl |
| GET | `/api/news/list` | List news items |
| POST | `/api/news/annotate` | Run LLM annotation |
| GET | `/api/news/sentiment/{news_id}` | Get sentiment |
| GET | `/api/trend/{term}` | Get term trend data |
| GET | `/api/market/{date}` | Get market data |

---

## Unified API Design

### Three-Layer Search Endpoint

```
GET /api/v1/search/{term}
```

**Response Structure:**

```json
{
  "term": "Inflation",
  "layer1": {
    "definitions": {
      "en": {"summary": "...", "url": "..."},
      "zh": {"summary": "...", "url": "..."}
    },
    "related_terms": ["Deflation", "CPI"],
    "categories": ["Macroeconomics"],
    "knowledge_graph": {
      "nodes": [...],
      "edges": [...]
    }
  },
  "layer2": {
    "alignments": [
      {
        "pboc": {"text": "...", "source": "...", "date": "..."},
        "fed": {"text": "...", "source": "...", "date": "..."},
        "similarity": 0.85,
        "topic": "inflation_outlook"
      }
    ],
    "total_alignments": 5
  },
  "layer3": {
    "recent_news": [
      {
        "title": "...",
        "source": "...",
        "date": "...",
        "sentiment": {"label": "bearish", "score": 0.82}
      }
    ],
    "sentiment_trend": [
      {"date": "2024-12-01", "avg_sentiment": -0.3, "news_count": 15},
      {"date": "2024-12-08", "avg_sentiment": -0.1, "news_count": 12}
    ],
    "market_correlation": {
      "sentiment_vs_sp500": 0.54,
      "news_count_vs_sp500": -0.32
    }
  },
  "meta": {
    "queried_at": "2024-12-14T20:30:00Z",
    "version": "1.0"
  }
}
```

---

## Frontend Architecture

### Component Structure

```
src/
├── App.vue                    # Main application
├── router/
│   └── index.js               # Vue Router configuration
├── views/
│   ├── HomeView.vue           # Home/Search page
│   ├── TerminologyView.vue    # Term details (Layer 1)
│   ├── PolicyView.vue         # Policy comparison (Layer 2)
│   ├── SentimentView.vue      # Sentiment analysis (Layer 3)
│   ├── BatchView.vue          # Batch import
│   └── ManageView.vue         # Admin/Settings
├── components/
│   ├── SearchBox.vue          # Search input
│   ├── TermCard.vue           # Term result card
│   ├── KnowledgeGraph.vue     # D3.js knowledge graph
│   ├── PolicyCompare.vue      # Side-by-side policy view
│   ├── TrendChart.vue         # ECharts trend visualization
│   ├── NewsTimeline.vue       # News list with sentiment
│   └── ExportPanel.vue        # Export options
├── stores/
│   └── corpus.js              # Pinia state management
└── utils/
    ├── api.js                 # Axios API client
    └── formatters.js          # Data formatting helpers
```

### State Management (Pinia)

```javascript
// stores/corpus.js
export const useCorpusStore = defineStore('corpus', {
  state: () => ({
    currentTerm: null,
    searchResults: {
      layer1: null,
      layer2: null,
      layer3: null
    },
    isLoading: false,
    selectedLanguages: ['en', 'zh'],
    config: {
      userAgent: '',
      crawlDelay: 3000
    }
  }),
  
  actions: {
    async searchTerm(term) { ... },
    async fetchPolicyAlignments(term) { ... },
    async fetchSentimentTrend(term) { ... }
  }
})
```

---

## Deployment Architecture

### Development Environment

```
Local Development:
├── Backend: http://localhost:8000 (uvicorn --reload)
├── Frontend: http://localhost:5173 (vite dev)
└── Database: ./backend/corpus.db (SQLite)
```

### Production Environment (Planned)

```
Cloud Deployment:
├── Backend: Railway / Render (FastAPI + Gunicorn)
├── Frontend: Vercel / Netlify (Vue.js static)
├── Database: SQLite (embedded) or PostgreSQL (scaled)
└── Domain: econmind-matrix.example.com
```

### Docker Configuration (Future)

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///data/corpus.db
      
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

---

## Data Export Formats

### JSONL (Machine Learning Ready)

```jsonl
{"id":1,"term":"Inflation","en_summary":"...","zh_summary":"...","related":["Deflation"]}
{"id":2,"term":"GDP","en_summary":"...","zh_summary":"...","related":["GNP"]}
```

### TMX (Translation Memory)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <body>
    <tu>
      <tuv xml:lang="en"><seg>Inflation is...</seg></tuv>
      <tuv xml:lang="zh"><seg>通货膨胀是...</seg></tuv>
    </tu>
  </body>
</tmx>
```

### CSV (Excel Compatible)

```csv
id,term,en_summary,zh_summary,ja_summary
1,Inflation,"In economics...","通货膨胀是...","インフレーションとは..."
```

---

## Quality Assurance

### Data Validation

- **Completeness Check**: Verify all required fields are present
- **Language Coverage**: Ensure target languages have content
- **URL Validation**: Confirm Wikipedia URLs are valid
- **Duplicate Detection**: Prevent redundant term entries

### Annotation Quality

- **Inter-Annotator Agreement**: Track human verification rates
- **Confidence Thresholds**: Flag low-confidence LLM predictions
- **Audit Trail**: Log all annotation changes

### Performance Metrics

- **API Response Time**: Target < 200ms for single term queries
- **Crawl Rate**: Respect Wikipedia rate limits (3s delay)
- **Export Speed**: Handle 10,000+ terms efficiently

---

## Changelog

- **2024-12-14**: Initial architecture document
- **TODO**: Layer 2 implementation details
- **TODO**: Layer 3 implementation details
- **TODO**: Performance optimization guide

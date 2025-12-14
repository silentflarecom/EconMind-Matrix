# EconMind Matrix - API Documentation

## Base URL

```
Development: http://localhost:8000
Production: https://api.econmind-matrix.example.com
```

---

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

> **Note**: For production deployment, consider adding API key authentication.

---

## Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "error": null
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "error": {
    "code": "ERROR_CODE",
    "details": "..."
  }
}
```

---

## Layer 1: Terminology Endpoints

### Search Term

Search for a single term across all configured languages.

```
GET /api/term/{term}
```

**Parameters:**

| Name | Type | Required | Description |
|:---|:---|:---|:---|
| term | string | Yes | Term to search (URL encoded) |
| languages | string | No | Comma-separated language codes (default: en,zh) |

**Example Request:**

```bash
curl "http://localhost:8000/api/term/Inflation?languages=en,zh,ja"
```

**Example Response:**

```json
{
  "success": true,
  "data": {
    "term": "Inflation",
    "translations": {
      "en": {
        "summary": "In economics, inflation is a general increase in the prices...",
        "url": "https://en.wikipedia.org/wiki/Inflation"
      },
      "zh": {
        "summary": "通货膨胀是指一般物价水平持续上涨的现象...",
        "url": "https://zh.wikipedia.org/wiki/通货膨胀"
      },
      "ja": {
        "summary": "インフレーション（英: inflation）とは...",
        "url": "https://ja.wikipedia.org/wiki/インフレーション"
      }
    }
  }
}
```

---

### Create Batch Task

Start a batch crawling task for multiple terms.

```
POST /api/batch
```

**Request Body:**

```json
{
  "terms": ["Inflation", "GDP", "Monetary Policy"],
  "languages": ["en", "zh", "ja"],
  "max_depth": 1,
  "crawl_associations": true
}
```

**Parameters:**

| Name | Type | Required | Description |
|:---|:---|:---|:---|
| terms | array | Yes | List of terms to crawl |
| languages | array | No | Target languages (default: ["en", "zh"]) |
| max_depth | integer | No | Association crawl depth 1-3 (default: 1) |
| crawl_associations | boolean | No | Whether to crawl related terms (default: false) |

**Example Response:**

```json
{
  "success": true,
  "data": {
    "task_id": 123,
    "status": "pending",
    "total_terms": 3,
    "created_at": "2024-12-14T20:30:00Z"
  }
}
```

---

### Get Task Status

```
GET /api/tasks/{task_id}
```

**Example Response:**

```json
{
  "success": true,
  "data": {
    "id": 123,
    "status": "running",
    "total_terms": 3,
    "completed_terms": 2,
    "failed_terms": 0,
    "progress": 66.67,
    "created_at": "2024-12-14T20:30:00Z",
    "updated_at": "2024-12-14T20:31:00Z"
  }
}
```

**Status Values:**

| Status | Description |
|:---|:---|
| pending | Task created, not started |
| running | Currently processing |
| completed | All terms processed |
| failed | Task encountered fatal error |
| cancelled | Task was cancelled by user |

---

### Get Task Results

```
GET /api/tasks/{task_id}/results
```

**Query Parameters:**

| Name | Type | Description |
|:---|:---|:---|
| page | integer | Page number (default: 1) |
| per_page | integer | Results per page (default: 50) |
| status | string | Filter by term status: success, failed, pending |

**Example Response:**

```json
{
  "success": true,
  "data": {
    "task_id": 123,
    "results": [
      {
        "id": 1,
        "term": "Inflation",
        "status": "success",
        "translations": { ... },
        "associations": ["Deflation", "CPI"],
        "depth_level": 0
      },
      {
        "id": 2,
        "term": "GDP",
        "status": "success",
        "translations": { ... },
        "associations": ["GNP", "Economic_growth"],
        "depth_level": 0
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 2,
      "pages": 1
    }
  }
}
```

---

### Export Data

```
GET /api/export/{format}
```

**Path Parameters:**

| Name | Values | Description |
|:---|:---|:---|
| format | json, jsonl, csv, tsv, tmx, txt | Export format |

**Query Parameters:**

| Name | Type | Description |
|:---|:---|:---|
| task_id | integer | Export specific task (optional) |
| languages | string | Comma-separated language codes |

**Example:**

```bash
# Export all data as JSONL
curl "http://localhost:8000/api/export/jsonl" -o terminology.jsonl

# Export specific task as CSV
curl "http://localhost:8000/api/export/csv?task_id=123" -o export.csv
```

---

### Get Knowledge Graph

```
GET /api/graph/{task_id}
```

**Example Response:**

```json
{
  "success": true,
  "data": {
    "nodes": [
      {"id": "Inflation", "group": 0, "depth": 0},
      {"id": "Deflation", "group": 1, "depth": 1},
      {"id": "CPI", "group": 1, "depth": 1}
    ],
    "links": [
      {"source": "Inflation", "target": "Deflation", "type": "see_also"},
      {"source": "Inflation", "target": "CPI", "type": "link"}
    ]
  }
}
```

---

## Layer 2: Policy Endpoints (Planned)

### Upload Policy Report

```
POST /api/policy/upload
Content-Type: multipart/form-data
```

**Form Parameters:**

| Name | Type | Required | Description |
|:---|:---|:---|:---|
| file | file | Yes | PDF file to upload |
| source | string | Yes | Source identifier: "pboc" or "fed" |
| title | string | No | Report title |
| report_date | string | No | Report date (YYYY-MM-DD) |

---

### List Policy Reports

```
GET /api/policy/reports
```

**Query Parameters:**

| Name | Type | Description |
|:---|:---|:---|
| source | string | Filter by source: pboc, fed |
| from_date | string | Start date filter |
| to_date | string | End date filter |

---

### Get Policy Alignments

```
GET /api/policy/align/{term}
```

**Example Response:**

```json
{
  "success": true,
  "data": {
    "term": "Inflation",
    "alignments": [
      {
        "id": 1,
        "pboc": {
          "paragraph_id": 45,
          "text": "当前通胀水平保持温和...",
          "report": "2024Q3 Monetary Policy Report",
          "date": "2024-11-15"
        },
        "fed": {
          "paragraph_id": 78,
          "text": "Prices continued to rise modestly...",
          "report": "December 2024 Beige Book",
          "date": "2024-12-04"
        },
        "similarity": 0.85,
        "topic": "inflation_current"
      }
    ],
    "total": 5
  }
}
```

---

## Layer 3: Sentiment Endpoints (Planned)

### Start News Crawl

```
POST /api/news/crawl
```

**Request Body:**

```json
{
  "sources": ["bloomberg", "reuters"],
  "keywords": ["inflation", "federal reserve"],
  "days_back": 30
}
```

---

### List News Items

```
GET /api/news/list
```

**Query Parameters:**

| Name | Type | Description |
|:---|:---|:---|
| source | string | Filter by source |
| from_date | string | Start date |
| to_date | string | End date |
| term | string | Filter by related term |
| sentiment | string | Filter by sentiment: bullish, bearish, neutral |
| page | integer | Page number |
| per_page | integer | Items per page |

---

### Get Sentiment for News

```
GET /api/news/sentiment/{news_id}
```

**Example Response:**

```json
{
  "success": true,
  "data": {
    "news_id": 456,
    "title": "Fed signals slower pace of rate cuts",
    "sentiment": {
      "label": "bearish",
      "score": 0.82,
      "annotator": "llm",
      "model": "gemini-1.5-pro",
      "verified": true,
      "verified_by": "user123"
    }
  }
}
```

---

### Get Term Trend

```
GET /api/trend/{term}
```

**Query Parameters:**

| Name | Type | Description |
|:---|:---|:---|
| days | integer | Number of days to include (default: 30) |
| include_market | boolean | Include market data (default: true) |

**Example Response:**

```json
{
  "success": true,
  "data": {
    "term": "Inflation",
    "trend": [
      {
        "date": "2024-12-01",
        "news_count": 15,
        "avg_sentiment": -0.32,
        "sp500_close": 4514.02,
        "sp500_change": -0.54
      },
      {
        "date": "2024-12-02",
        "news_count": 12,
        "avg_sentiment": -0.18,
        "sp500_close": 4525.50,
        "sp500_change": 0.25
      }
    ],
    "correlation": {
      "sentiment_vs_sp500": 0.54,
      "news_count_vs_sp500": -0.32
    }
  }
}
```

---

## Unified Search Endpoint

### Three-Layer Search

```
GET /api/v1/search/{term}
```

This endpoint returns combined data from all three layers.

**Query Parameters:**

| Name | Type | Description |
|:---|:---|:---|
| languages | string | Comma-separated language codes |
| include_policy | boolean | Include Layer 2 data (default: true) |
| include_sentiment | boolean | Include Layer 3 data (default: true) |
| news_days | integer | Days of news to include (default: 30) |

**Example Response:**

See [Architecture Documentation](architecture.md#three-layer-search-endpoint) for full response structure.

---

## System Endpoints

### Health Check

```
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "uptime": 3600
}
```

---

### Get/Update Settings

```
GET /api/settings
PUT /api/settings
```

**Settings Object:**

```json
{
  "user_agent": "EconMind-Matrix/1.0 (contact@example.com)",
  "crawl_delay_ms": 3000,
  "default_languages": ["en", "zh"]
}
```

---

### Database Backup

```
GET /api/backup
```

Returns the SQLite database file as a download.

---

### Database Restore

```
POST /api/restore
Content-Type: multipart/form-data
```

**Form Parameters:**

| Name | Type | Required | Description |
|:---|:---|:---|:---|
| file | file | Yes | SQLite database file (.db) |

---

## Error Codes

| Code | Description |
|:---|:---|
| TERM_NOT_FOUND | Wikipedia article not found |
| RATE_LIMITED | Too many requests, please wait |
| INVALID_LANGUAGE | Unsupported language code |
| TASK_NOT_FOUND | Batch task ID not found |
| EXPORT_FAILED | Export generation failed |
| DATABASE_ERROR | Database operation failed |
| INVALID_FORMAT | Unsupported export format |
| FILE_TOO_LARGE | Uploaded file exceeds limit |

---

## Rate Limiting

To comply with Wikipedia API policy:

- Single term requests: No limit
- Batch crawling: 3 second delay between Wikipedia requests
- Export requests: No limit

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Search single term
response = requests.get(f"{BASE_URL}/api/term/Inflation")
data = response.json()
print(data['data']['translations']['zh']['summary'])

# Start batch task
response = requests.post(f"{BASE_URL}/api/batch", json={
    "terms": ["Inflation", "GDP", "Recession"],
    "languages": ["en", "zh", "ja"]
})
task = response.json()['data']
print(f"Task ID: {task['task_id']}")
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000';

// Search single term
async function searchTerm(term) {
  const response = await fetch(`${BASE_URL}/api/term/${encodeURIComponent(term)}`);
  const data = await response.json();
  return data.data;
}

// Start batch task
async function startBatch(terms, languages) {
  const response = await fetch(`${BASE_URL}/api/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ terms, languages })
  });
  return await response.json();
}
```

---

## Changelog

- **v1.0.0**: Initial API with Layer 1 endpoints
- **v1.1.0** (planned): Layer 2 policy endpoints
- **v1.2.0** (planned): Layer 3 sentiment endpoints
- **v2.0.0** (planned): Unified search endpoint

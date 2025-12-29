# Shared Module

This module contains shared utilities used across all layers of EconMind-Matrix.

## Modules

| Module | Purpose |
|:-------|:--------|
| `utils.py` | Text processing utilities (`clean_text`) |
| `schema.py` | Database schema definitions |
| `errors.py` | Standardized error handling |
| `config.py` | Configuration constants |

## Quick Usage

```python
# Text utilities
from shared.utils import clean_text
cleaned = clean_text("Text with\nnewlines")

# Database schemas
from shared.schema import LAYER1_SQL_SCHEMA, ALL_TABLES

# Error handling
from shared.errors import NotFoundError, ValidationError
raise NotFoundError("Task", task_id)

# Configuration
from shared.config import DEFAULT_CRAWL_INTERVAL, SUPPORTED_LANGUAGES
```

## Error Classes

| Class | HTTP Code | Use Case |
|:------|:---------:|:---------|
| `NotFoundError` | 404 | Resource not found |
| `ValidationError` | 400 | Invalid input |
| `ConflictError` | 409 | Resource conflict |
| `ProcessingError` | 500 | Server error |

## Configuration Constants

See `config.py` for all available constants including:
- Crawl settings (`DEFAULT_CRAWL_INTERVAL`, `MAX_CRAWL_DEPTH`)
- API limits (`MAX_PAGE_SIZE`, `MAX_EXPORT_RECORDS`)
- Language codes (`SUPPORTED_LANGUAGES`, `UN_LANGUAGES`)

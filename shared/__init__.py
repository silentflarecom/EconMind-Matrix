"""
Shared utilities package for EconMind-Matrix.

This package contains common utility functions used across all layers:
- Layer 1: Terminology Corpus (backend/)
- Layer 2: Policy Parallel Corpus (layer2_policy/)  
- Layer 3: Sentiment Corpus (layer3_sentiment/)

Modules:
- utils: Text processing utilities (clean_text)
- schema: Database schema definitions
- errors: Standardized error handling
- config: Configuration constants

Usage:
    from shared.utils import clean_text
    from shared.schema import LAYER1_SQL_SCHEMA
    from shared.errors import NotFoundError
    from shared.config import DEFAULT_CRAWL_INTERVAL
"""

from .utils import clean_text, clean_export_text
from .schema import (
    LAYER1_SQL_SCHEMA, LAYER2_SQL_SCHEMA, LAYER3_SQL_SCHEMA,
    ALL_SCHEMAS, ALL_TABLES, LAYER1_TABLES, LAYER2_TABLES, LAYER3_TABLES,
    LAYER1_DEFAULTS, get_all_table_drop_statements, get_schema_version
)
from .errors import (
    APIError, NotFoundError, ValidationError, ConflictError,
    ProcessingError, UnauthorizedError, ForbiddenError,
    error_response, success_response
)
from .config import (
    DEFAULT_CRAWL_INTERVAL, DEFAULT_MAX_DEPTH, MAX_CRAWL_DEPTH,
    MIN_SUMMARY_LENGTH, MAX_SUMMARY_LENGTH, DEFAULT_TARGET_LANGUAGES,
    SUPPORTED_LANGUAGES, UN_LANGUAGES, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
)

__all__ = [
    # Utils
    'clean_text', 'clean_export_text',
    # Schema
    'LAYER1_SQL_SCHEMA', 'LAYER2_SQL_SCHEMA', 'LAYER3_SQL_SCHEMA',
    'ALL_SCHEMAS', 'ALL_TABLES',
    # Errors
    'APIError', 'NotFoundError', 'ValidationError', 'ConflictError',
    'ProcessingError', 'error_response', 'success_response',
    # Config
    'DEFAULT_CRAWL_INTERVAL', 'DEFAULT_MAX_DEPTH', 'SUPPORTED_LANGUAGES',
    'MIN_SUMMARY_LENGTH', 'DEFAULT_PAGE_SIZE', 'MAX_PAGE_SIZE'
]

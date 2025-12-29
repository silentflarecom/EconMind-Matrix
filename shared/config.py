"""
Configuration Constants for EconMind-Matrix

This module centralizes magic numbers and hardcoded values.
Created as part of Technical Debt Issue #11 fix.

Usage:
    from shared.config import DEFAULT_CRAWL_INTERVAL, MAX_TERMS_PER_BATCH
"""

from typing import List

# =============================================================================
# General Settings
# =============================================================================

# Database
DATABASE_FILE = "corpus.db"
DATABASE_BACKUP_DIR = "./backups"

# API Server
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# =============================================================================
# Layer 1: Terminology Corpus
# =============================================================================

# Batch task defaults
DEFAULT_CRAWL_INTERVAL = 3  # seconds between Wikipedia API calls
DEFAULT_MAX_DEPTH = 1  # default association crawl depth
MAX_CRAWL_DEPTH = 5  # maximum allowed crawl depth
MAX_TERMS_PER_BATCH = 1000  # maximum terms in a single batch

# Wikipedia API
WIKIPEDIA_USER_AGENT = "TermCorpusBot/1.0 (Educational Project)"
WIKIPEDIA_RATE_LIMIT = 0.5  # minimum seconds between requests

# Summary lengths
MIN_SUMMARY_LENGTH = 50  # minimum characters for valid summary
MAX_SUMMARY_LENGTH = 5000  # maximum characters to store

# Default target languages
DEFAULT_TARGET_LANGUAGES = ["en", "zh"]

# =============================================================================
# Layer 2: Policy Parallel Corpus
# =============================================================================

# Alignment thresholds
DEFAULT_ALIGNMENT_THRESHOLD = 0.5  # minimum similarity for alignment
HIGH_QUALITY_ALIGNMENT_THRESHOLD = 0.75

# Report parsing
MAX_REPORT_SIZE_MB = 50  # maximum PDF size in megabytes
PARAGRAPH_MIN_WORDS = 10  # minimum words for valid paragraph

# =============================================================================
# Layer 3: Sentiment Corpus
# =============================================================================

# News crawling
DEFAULT_DAYS_BACK = 7  # default days of news to fetch
MAX_DAYS_BACK = 365  # maximum days to look back

# Sentiment thresholds
BULLISH_THRESHOLD = 0.6
BEARISH_THRESHOLD = -0.6
HIGH_CONFIDENCE_THRESHOLD = 0.8

# Rate limiting
DEFAULT_REQUEST_DELAY = 1.0  # seconds between requests
MAX_CONCURRENT_REQUESTS = 5

# =============================================================================
# API Limits
# =============================================================================

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MIN_PAGE_SIZE = 1

# Export limits
MAX_EXPORT_RECORDS = 10000

# =============================================================================
# Supported Languages (ISO 639-1 codes)
# =============================================================================

SUPPORTED_LANGUAGES: List[str] = [
    "en",      # English
    "zh",      # Simplified Chinese
    "zh-tw",   # Traditional Chinese
    "ja",      # Japanese
    "ko",      # Korean
    "es",      # Spanish
    "fr",      # French
    "de",      # German
    "ru",      # Russian
    "pt",      # Portuguese
    "it",      # Italian
    "ar",      # Arabic
    "hi",      # Hindi
    "vi",      # Vietnamese
    "th",      # Thai
    "id",      # Indonesian
    "tr",      # Turkish
    "pl",      # Polish
    "nl",      # Dutch
    "sv",      # Swedish
    "uk",      # Ukrainian
]

# UN Official Languages
UN_LANGUAGES = ["en", "zh", "ar", "es", "fr", "ru"]

"""
Layer 3: Sentiment & Trend Corpus Module

This module provides sentiment analysis for financial news, integrated with Layer 1 terminology
and Layer 2 policy corpus for comprehensive economic analysis.

Components:
- models.py: Data models for news articles and sentiment annotations
- database.py: Database operations for Layer 3 tables
- api.py: FastAPI router with sentiment endpoints
- news_crawler.py: RSS feed news crawler
- llm_annotator.py: LLM-based sentiment annotation (Gemini API)
- trend_analysis.py: Time series analysis and trend detection
- doccano_export.py: Doccano platform integration for human-in-the-loop

Usage:
    from layer3-sentiment.backend.api import sentiment_router
    
    app.include_router(sentiment_router, prefix="/api/sentiment", tags=["sentiment"])
"""

from pathlib import Path
import sys

# Ensure parent path is in sys.path for imports
parent_path = Path(__file__).parent.parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

__version__ = "1.0.0"
__author__ = "EconMind Matrix Team"

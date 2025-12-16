"""
Layer 3: Sentiment API Endpoints
FastAPI router for sentiment analysis and news operations.

Integrates with Layer 1 terminology and Layer 2 policy modules.

Usage:
    from layer3_api import sentiment_router
    
    app.include_router(sentiment_router, prefix="/api/sentiment", tags=["sentiment"])
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, date, timedelta

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse

# Import Layer 3 modules
try:
    from .database import SentimentDatabase
    from .models import (
        NewsArticle, SentimentAnnotation, SentimentLabel, AnnotationSource, NewsSource,
        detect_related_terms
    )
except ImportError:
    from database import SentimentDatabase
    from models import (
        NewsArticle, SentimentAnnotation, SentimentLabel, AnnotationSource, NewsSource,
        detect_related_terms
    )

# Import crawler and annotator
try:
    from ..crawler.news_crawler import NewsCrawler, NEWS_SOURCES
except ImportError:
    try:
        from crawler.news_crawler import NewsCrawler, NEWS_SOURCES
    except ImportError:
        NewsCrawler = None
        NEWS_SOURCES = {}

try:
    from ..annotation.llm_annotator import SentimentAnnotator, RuleBasedAnnotator, HybridAnnotator
except ImportError:
    try:
        from annotation.llm_annotator import SentimentAnnotator, RuleBasedAnnotator, HybridAnnotator
    except ImportError:
        SentimentAnnotator = None
        RuleBasedAnnotator = None
        HybridAnnotator = None

# Import trend analyzer
try:
    from ..analysis.trend_analysis import TrendAnalyzer
except ImportError:
    try:
        from analysis.trend_analysis import TrendAnalyzer
    except ImportError:
        TrendAnalyzer = None


# Initialize router
sentiment_router = APIRouter()

# Configuration
DB_PATH = Path("./corpus.db")

# Initialize components
db = SentimentDatabase(str(DB_PATH))

# Global crawler instance for start/stop control
active_crawler = None

# Crawl status tracking (for progress monitoring)
crawl_status = {
    "is_crawling": False,
    "current_source": None,
    "total_sources": 0,
    "completed_sources": 0,
    "articles_found": 0,
    "articles_inserted": 0,
    "started_at": None,
    "message": "Idle"
}


# ==================== Initialization ====================

@sentiment_router.on_event("startup")
async def startup():
    """Initialize Layer 3 database tables on startup."""
    await db.initialize()


# ==================== News Crawling Endpoints ====================

@sentiment_router.get("/sources")
async def list_news_sources():
    """List available news sources for crawling."""
    sources = []
    for key, info in NEWS_SOURCES.items():
        sources.append({
            "key": key,
            "name": info.get("name", key),
            "language": info.get("language", "en"),
            "has_rss": bool(info.get("rss_urls"))
        })
    return {
        "success": True,
        "sources": sources,
        "total": len(sources)
    }


@sentiment_router.get("/crawl/status")
async def get_crawl_status():
    """Get current crawl status for progress monitoring."""
    progress = 0
    if crawl_status["total_sources"] > 0:
        progress = int((crawl_status["completed_sources"] / crawl_status["total_sources"]) * 100)
    
    return {
        "success": True,
        "status": crawl_status,
        "progress": progress
    }


@sentiment_router.post("/crawl")
async def crawl_news(
    background_tasks: BackgroundTasks,
    sources: List[str] = Query(default=["reuters", "wsj"]),
    days_back: int = Query(default=7, ge=1, le=30),
    keywords: Optional[List[str]] = Query(default=None),
    max_concurrent: int = Query(default=3, ge=1, le=10),
    delay_seconds: float = Query(default=1.0, ge=0.5, le=10),
    rotate_ua: bool = Query(default=True)
):
    """
    Start crawling news from specified sources.
    
    New options:
    - max_concurrent: Maximum concurrent requests (1-10)
    - delay_seconds: Delay between requests (0.5-10 seconds)
    - rotate_ua: Whether to rotate User-Agent for each request
    
    Use POST /crawl/stop to stop the crawl.
    Use GET /crawl/status to monitor progress.
    """
    global crawl_status, active_crawler
    
    if NewsCrawler is None:
        raise HTTPException(500, "News crawler not available. Check dependencies.")
    
    # Check if already crawling
    if crawl_status["is_crawling"]:
        return {
            "success": False,
            "message": "A crawl is already in progress. Use /crawl/stop to stop it first.",
            "status": crawl_status
        }
    
    # Validate sources
    valid_sources = [s for s in sources if s in NEWS_SOURCES]
    if not valid_sources:
        raise HTTPException(400, f"No valid sources. Available: {list(NEWS_SOURCES.keys())}")
    
    # Initialize status
    from datetime import datetime
    crawl_status.update({
        "is_crawling": True,
        "current_source": None,
        "total_sources": len(valid_sources),
        "completed_sources": 0,
        "articles_found": 0,
        "articles_inserted": 0,
        "started_at": datetime.now().isoformat(),
        "message": "Starting crawl..."
    })
    
    async def do_crawl():
        global crawl_status, active_crawler
        
        # Create crawler with new options
        active_crawler = NewsCrawler(
            sources=valid_sources,
            max_concurrent=max_concurrent,
            delay_seconds=delay_seconds,
            rotate_user_agent=rotate_ua
        )
        
        try:
            for i, source_key in enumerate(valid_sources):
                # Check if stop was requested
                if active_crawler._should_stop:
                    crawl_status["message"] = f"Stopped by user after {i} sources"
                    break
                    
                crawl_status["current_source"] = source_key
                crawl_status["message"] = f"Crawling {NEWS_SOURCES.get(source_key, {}).get('name', source_key)}..."
                
                print(f"📰 Crawling {source_key}...")
                
                articles = await active_crawler.crawl_rss(source_key)
                
                # Filter by date
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(days=days_back)
                articles = [a for a in articles if not a.published_date or a.published_date >= cutoff]
                
                # Filter by keywords
                if keywords:
                    keywords_lower = [k.lower() for k in keywords]
                    articles = [a for a in articles if any(
                        kw in (a.title or '').lower() or kw in (a.summary or '').lower()
                        for kw in keywords_lower
                    )]
                
                # Insert to DB immediately (incremental)
                if articles:
                    inserted_ids = await db.insert_articles_batch(articles)
                    crawl_status["articles_found"] += len(articles)
                    crawl_status["articles_inserted"] += len(inserted_ids)
                    print(f"  ✓ Found {len(articles)} articles, inserted {len(inserted_ids)} new")
                
                crawl_status["completed_sources"] = i + 1
            
            if not active_crawler._should_stop:
                crawl_status["message"] = f"Completed! {crawl_status['articles_found']} articles, {crawl_status['articles_inserted']} new"
            
        except Exception as e:
            crawl_status["message"] = f"Error: {str(e)}"
            print(f"✗ Crawl error: {e}")
        finally:
            if active_crawler:
                await active_crawler.close()
            active_crawler = None
            crawl_status["is_crawling"] = False
            crawl_status["current_source"] = None
    
    background_tasks.add_task(do_crawl)
    
    return {
        "success": True,
        "message": f"Crawl started for {len(valid_sources)} sources",
        "config": {
            "sources": len(valid_sources),
            "days_back": days_back,
            "max_concurrent": max_concurrent,
            "delay_seconds": delay_seconds,
            "rotate_ua": rotate_ua
        }
    }


@sentiment_router.post("/crawl/stop")
async def stop_crawl():
    """
    Stop the currently running crawl.
    
    The crawl will stop after completing the current source.
    """
    global crawl_status, active_crawler
    
    if not crawl_status["is_crawling"]:
        return {
            "success": False,
            "message": "No crawl is currently running"
        }
    
    if active_crawler:
        active_crawler.stop()
        crawl_status["message"] = "Stop requested, finishing current source..."
        return {
            "success": True,
            "message": "Stop signal sent. Crawl will stop after current source completes."
        }
    
    return {
        "success": False,
        "message": "Crawler instance not found"
    }


@sentiment_router.post("/crawl-term/{term}")
async def crawl_for_term(
    term: str,
    background_tasks: BackgroundTasks,
    days_back: int = Query(default=30, ge=1, le=90)
):
    """
    Crawl news specifically related to an economic term.
    
    Links to Layer 1 terminology for integrated search.
    """
    if NewsCrawler is None:
        raise HTTPException(500, "News crawler not available")
    
    async def do_crawl():
        crawler = NewsCrawler()
        try:
            articles = await crawler.crawl_for_term(term, days_back=days_back)
            inserted_ids = await db.insert_articles_batch(articles)
            print(f"✓ Crawled {len(articles)} articles for '{term}', inserted {len(inserted_ids)} new")
        finally:
            await crawler.close()
    
    background_tasks.add_task(do_crawl)
    
    return {
        "success": True,
        "message": f"Crawl started for term '{term}' (last {days_back} days)",
        "term": term
    }


# ==================== Article Endpoints ====================

@sentiment_router.get("/articles")
async def list_articles(
    source: str = Query(None, description="Filter by source"),
    language: str = Query(None, description="Filter by language (en, zh)"),
    days_back: int = Query(7, ge=1, le=365),
    only_unannotated: bool = Query(False),
    limit: int = Query(50, ge=1, le=500)
):
    """Get news articles with optional filtering."""
    articles = await db.get_articles(
        source=source,
        language=language,
        days_back=days_back,
        limit=limit,
        only_unannotated=only_unannotated
    )
    return {
        "success": True,
        "total": len(articles),
        "articles": [a.to_dict() for a in articles]
    }


@sentiment_router.get("/articles/{article_id}")
async def get_article(article_id: int):
    """Get a specific article by ID with its annotation."""
    article = await db.get_article(article_id)
    if not article:
        raise HTTPException(404, f"Article {article_id} not found")
    
    # Get annotation if exists
    annotations = await db.get_annotations(article_id=article_id, limit=1)
    
    result = article.to_dict()
    if annotations:
        result["annotation"] = annotations[0].to_dict()
    
    return {
        "success": True,
        "article": result
    }


@sentiment_router.get("/search/{term}")
async def search_articles(
    term: str,
    days_back: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search articles mentioning a specific term.
    
    Links to Layer 1 terminology for integrated search.
    """
    articles = await db.search_articles(term, days_back=days_back, limit=limit)
    
    return {
        "success": True,
        "term": term,
        "total": len(articles),
        "articles": [a.to_dict() for a in articles]
    }


@sentiment_router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    """Delete an article and its annotations."""
    await db.delete_article(article_id)
    return {
        "success": True,
        "message": f"Article {article_id} deleted"
    }


# ==================== Annotation Endpoints ====================

@sentiment_router.post("/annotate")
async def annotate_articles(
    background_tasks: BackgroundTasks,
    method: str = Query("auto", description="Method: auto, llm, rule_based, hybrid"),
    limit: int = Query(50, ge=1, le=500),
    force_reannotate: bool = Query(False)
):
    """
    Annotate unannotated articles with sentiment labels.
    
    Methods:
    - auto: Uses LLM if available, falls back to rule-based
    - llm: Uses Gemini API (requires GEMINI_API_KEY)
    - rule_based: Uses keyword matching (no API required)
    - hybrid: Uses rule-based first, LLM for uncertain cases
    """
    # Get unannotated articles
    articles = await db.get_articles(only_unannotated=True, limit=limit, days_back=365)
    
    if not articles:
        return {
            "success": True,
            "message": "No unannotated articles found",
            "annotated_count": 0
        }
    
    async def do_annotate():
        # Choose annotator
        if method == "llm" and SentimentAnnotator:
            annotator = SentimentAnnotator()
        elif method == "hybrid" and HybridAnnotator:
            annotator = HybridAnnotator()
        elif method == "rule_based" or not SentimentAnnotator:
            annotator = RuleBasedAnnotator()
        else:
            # Auto: try LLM, fall back to rule-based
            try:
                annotator = SentimentAnnotator()
            except:
                annotator = RuleBasedAnnotator()
        
        # Annotate
        annotated_count = 0
        for article in articles:
            try:
                if hasattr(annotator, 'annotate') and asyncio.iscoroutinefunction(annotator.annotate):
                    result = await annotator.annotate(
                        title=article.title,
                        summary=article.summary,
                        language=article.language
                    )
                else:
                    result = annotator.annotate(article.title, article.summary)
                
                # Save annotation
                annotation = result.to_annotation(article.id)
                await db.insert_annotation(annotation)
                annotated_count += 1
                
            except Exception as e:
                print(f"✗ Error annotating article {article.id}: {e}")
        
        print(f"✓ Annotated {annotated_count} articles")
    
    import asyncio
    background_tasks.add_task(do_annotate)
    
    return {
        "success": True,
        "message": f"Annotation started for {len(articles)} articles using {method} method",
        "articles_to_annotate": len(articles)
    }


@sentiment_router.post("/annotate/{article_id}")
async def annotate_single_article(
    article_id: int,
    method: str = Query("auto")
):
    """Annotate a single article with sentiment."""
    article = await db.get_article(article_id)
    if not article:
        raise HTTPException(404, f"Article {article_id} not found")
    
    # Choose annotator
    if method == "llm" and SentimentAnnotator:
        annotator = SentimentAnnotator()
        result = await annotator.annotate(article.title, article.summary, article.language)
    elif method == "rule_based" or not SentimentAnnotator:
        annotator = RuleBasedAnnotator()
        result = annotator.annotate(article.title, article.summary)
    else:
        # Auto
        try:
            annotator = SentimentAnnotator()
            result = await annotator.annotate(article.title, article.summary, article.language)
        except:
            annotator = RuleBasedAnnotator()
            result = annotator.annotate(article.title, article.summary)
    
    # Save annotation
    annotation = result.to_annotation(article_id)
    annotation_id = await db.insert_annotation(annotation)
    
    return {
        "success": True,
        "article_id": article_id,
        "annotation_id": annotation_id,
        "sentiment": result.to_dict()
    }


@sentiment_router.get("/annotations")
async def list_annotations(
    sentiment_label: str = Query(None, description="Filter: bullish, bearish, neutral"),
    annotation_source: str = Query(None, description="Filter by source"),
    verified_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=500)
):
    """Get sentiment annotations with optional filtering."""
    annotations = await db.get_annotations(
        sentiment_label=sentiment_label,
        annotation_source=annotation_source,
        verified_only=verified_only,
        limit=limit
    )
    return {
        "success": True,
        "total": len(annotations),
        "annotations": [a.to_dict() for a in annotations]
    }


@sentiment_router.put("/annotations/{annotation_id}/verify")
async def verify_annotation(
    annotation_id: int,
    verified_by: str = Query("human")
):
    """Mark an annotation as verified."""
    await db.verify_annotation(annotation_id, verified_by)
    return {
        "success": True,
        "message": f"Annotation {annotation_id} verified"
    }


@sentiment_router.put("/annotations/{annotation_id}")
async def update_annotation(
    annotation_id: int,
    sentiment_label: str = Query(..., description="New label: bullish, bearish, neutral"),
    reasoning: str = Query(None)
):
    """Update an annotation (human correction)."""
    if sentiment_label not in ["bullish", "bearish", "neutral"]:
        raise HTTPException(400, "Invalid sentiment_label")
    
    await db.update_annotation(
        annotation_id=annotation_id,
        sentiment_label=SentimentLabel(sentiment_label),
        confidence_score=1.0,
        reasoning=reasoning
    )
    
    return {
        "success": True,
        "message": f"Annotation {annotation_id} updated"
    }


# ==================== Trend Analysis Endpoints ====================

@sentiment_router.get("/trend/{term}")
async def get_term_trend(
    term: str,
    days_back: int = Query(30, ge=7, le=365),
    include_market: bool = Query(True)
):
    """
    Get trend analysis for a specific economic term.
    
    Returns daily mention counts, sentiment breakdown, and trend direction.
    Links to Layer 1 terminology for integrated analysis.
    """
    if TrendAnalyzer is None:
        raise HTTPException(500, "Trend analyzer not available")
    
    analyzer = TrendAnalyzer(str(DB_PATH))
    
    # Get trend summary
    summary = await analyzer.analyze_term_trend(
        term,
        days_back=days_back,
        include_market_correlation=include_market
    )
    
    # Get daily data for chart
    trend_data = await analyzer.get_trend_data(term, days_back=days_back)
    chart_data = analyzer.generate_chart_data(trend_data)
    
    return {
        "success": True,
        "term": term,
        "summary": summary.to_dict(),
        "chart_data": chart_data,
        "daily_data": [dp.to_dict() for dp in trend_data]
    }


@sentiment_router.get("/trends/hot")
async def get_hot_terms(
    days_back: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50)
):
    """Get the most mentioned economic terms in recent news."""
    if TrendAnalyzer is None:
        raise HTTPException(500, "Trend analyzer not available")
    
    analyzer = TrendAnalyzer(str(DB_PATH))
    hot_terms = await analyzer.get_hot_terms(days_back=days_back, limit=limit)
    
    return {
        "success": True,
        "days_back": days_back,
        "hot_terms": [
            {"term": term, "mentions": count, "avg_sentiment": round(sentiment, 4)}
            for term, count, sentiment in hot_terms
        ]
    }


@sentiment_router.post("/trends/compare")
async def compare_terms(
    terms: List[str] = Query(..., description="Terms to compare"),
    days_back: int = Query(30, ge=7, le=365)
):
    """Compare trend metrics across multiple terms."""
    if TrendAnalyzer is None:
        raise HTTPException(500, "Trend analyzer not available")
    
    if len(terms) > 10:
        raise HTTPException(400, "Maximum 10 terms for comparison")
    
    analyzer = TrendAnalyzer(str(DB_PATH))
    results = await analyzer.compare_terms(terms, days_back=days_back)
    
    return {
        "success": True,
        "terms_compared": len(terms),
        "comparison": {term: summary.to_dict() for term, summary in results.items()}
    }


# ==================== Statistics ====================

@sentiment_router.get("/stats")
async def get_statistics():
    """Get Layer 3 Sentiment statistics."""
    stats = await db.get_statistics()
    return {
        "success": True,
        "layer": 3,
        "name": "Sentiment & Trend Corpus",
        "statistics": stats
    }


# ==================== Export ====================

@sentiment_router.get("/export/articles")
async def export_articles(
    format: str = Query("jsonl", description="Format: json, jsonl"),
    days_back: int = Query(30, ge=1, le=365)
):
    """Export articles with annotations."""
    articles = await db.get_all_articles()
    
    # Get annotations for each
    export_data = []
    for article in articles:
        annotations = await db.get_annotations(article_id=article.id, limit=1)
        item = article.to_dict()
        if annotations:
            item["annotation"] = annotations[0].to_dict()
        export_data.append(item)
    
    if format == "json":
        content = json.dumps({
            "total": len(export_data),
            "articles": export_data
        }, indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=layer3_articles.json"}
        )
    else:  # jsonl
        def generate():
            for item in export_data:
                yield json.dumps(item, ensure_ascii=False) + "\n"
        
        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=layer3_articles.jsonl"}
        )


@sentiment_router.get("/export/sentiment")
async def export_sentiment_data(
    format: str = Query("jsonl", description="Format: json, jsonl, csv")
):
    """Export sentiment annotations for training datasets."""
    annotations = await db.get_all_annotations_with_articles()
    
    if format == "csv":
        import io
        import csv as csv_module
        
        output = io.BytesIO()
        output.write(b'\xef\xbb\xbf')  # UTF-8 BOM
        
        csv_content = io.StringIO()
        writer = csv_module.writer(csv_content)
        writer.writerow(["ID", "Title", "Source", "Sentiment", "Confidence", "Reasoning", "Verified"])
        
        for a in annotations:
            writer.writerow([
                a.article_id,
                a.article_title or "",
                a.article_source or "",
                a.sentiment_label.value,
                round(a.confidence_score, 4),
                a.reasoning or "",
                a.verified
            ])
        
        output.write(csv_content.getvalue().encode('utf-8'))
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=layer3_sentiment.csv"}
        )
    
    export_data = [a.to_dict() for a in annotations]
    
    if format == "json":
        content = json.dumps({
            "total": len(export_data),
            "annotations": export_data
        }, indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=layer3_sentiment.json"}
        )
    else:  # jsonl
        def generate():
            for item in export_data:
                yield json.dumps(item, ensure_ascii=False) + "\n"
        
        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=layer3_sentiment.jsonl"}
        )


@sentiment_router.get("/export/doccano")
async def export_for_doccano(
    include_preannotations: bool = Query(True),
    limit: int = Query(1000, ge=1, le=10000)
):
    """Export articles in Doccano-compatible JSONL format."""
    articles = await db.get_annotated_articles_for_doccano(
        include_unannotated=True,
        limit=limit
    )
    
    def generate():
        for article in articles:
            entry = {
                "id": article["id"],
                "text": article["text"],
                "meta": article["meta"]
            }
            if include_preannotations and article.get("label"):
                entry["label"] = [article["label"]]
            else:
                entry["label"] = []
            yield json.dumps(entry, ensure_ascii=False) + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=doccano_export.jsonl"}
    )


# ==================== Integration with Layer 1 & 2 ====================

@sentiment_router.get("/term/{term}/full")
async def get_term_full_analysis(
    term: str,
    days_back: int = Query(30, ge=1, le=365)
):
    """
    Get comprehensive analysis for a term across all layers.
    
    This is the main integration endpoint linking:
    - Layer 1: Term definitions
    - Layer 2: Policy mentions
    - Layer 3: News sentiment and trends
    """
    # Layer 3: Sentiment analysis
    articles = await db.search_articles(term, days_back=days_back, limit=20)
    
    # Get annotations
    annotated_articles = []
    for article in articles[:10]:
        annotations = await db.get_annotations(article_id=article.id, limit=1)
        item = {
            "id": article.id,
            "title": article.title,
            "source": article.source.value,
            "date": article.published_date.isoformat() if article.published_date else None,
            "url": article.url
        }
        if annotations:
            item["sentiment"] = {
                "label": annotations[0].sentiment_label.value,
                "score": annotations[0].confidence_score
            }
        annotated_articles.append(item)
    
    # Get trend summary if available
    trend_summary = None
    if TrendAnalyzer:
        try:
            analyzer = TrendAnalyzer(str(DB_PATH))
            summary = await analyzer.analyze_term_trend(term, days_back=days_back)
            trend_summary = summary.to_dict()
        except:
            pass
    
    return {
        "success": True,
        "term": term,
        "layer3_sentiment": {
            "total_articles": len(articles),
            "recent_articles": annotated_articles,
            "trend": trend_summary
        },
        "integration_note": "Use /api/search/{term} for Layer 1 definitions, /api/policy/search/{term} for Layer 2 policy"
    }


# ==================== Health Check ====================

@sentiment_router.get("/health")
async def health_check():
    """Health check for Layer 3 API."""
    stats = await db.get_statistics()
    return {
        "status": "healthy",
        "layer": 3,
        "name": "Sentiment & Trend Corpus",
        "articles": stats.get("total_articles", 0),
        "annotations": stats.get("total_annotations", 0),
        "crawler_available": NewsCrawler is not None,
        "annotator_available": SentimentAnnotator is not None or RuleBasedAnnotator is not None,
        "trend_analyzer_available": TrendAnalyzer is not None
    }


# Create FastAPI application for standalone testing
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(
        title="EconMind Matrix - Layer 3 API",
        description="Sentiment & Trend Corpus API",
        version="1.0.0"
    )
    
    app.include_router(sentiment_router, prefix="/api/sentiment", tags=["sentiment"])
    
    @app.get("/")
    async def root():
        return {"message": "Layer 3 Sentiment API", "docs": "/docs"}
    
    uvicorn.run(app, host="0.0.0.0", port=8002)

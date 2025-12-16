"""
Layer 3: Database Operations
Extends the Layer 1 database with news sentiment tables.

Usage:
    from database import SentimentDatabase
    
    db = SentimentDatabase("corpus.db")
    await db.initialize()
    article_id = await db.insert_article(article)
"""

import json
import aiosqlite
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

# Import local models
try:
    from .models import (
        NewsArticle, SentimentAnnotation, MarketContext, TrendDataPoint,
        NewsSource, SentimentLabel, AnnotationSource,
        LAYER3_SQL_SCHEMA
    )
except ImportError:
    from models import (
        NewsArticle, SentimentAnnotation, MarketContext, TrendDataPoint,
        NewsSource, SentimentLabel, AnnotationSource,
        LAYER3_SQL_SCHEMA
    )


class SentimentDatabase:
    """
    Async database operations for Layer 3 sentiment data.
    Extends the existing Layer 1 corpus.db with sentiment tables.
    """
    
    def __init__(self, db_path: str = "corpus.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
    
    async def initialize(self):
        """Create Layer 3 tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(LAYER3_SQL_SCHEMA)
            await db.commit()
        print(f"Layer 3 database tables initialized in {self.db_path}")
    
    # ==================== Article Operations ====================
    
    async def insert_article(self, article: NewsArticle) -> int:
        """
        Insert a new news article.
        
        Args:
            article: NewsArticle object
            
        Returns:
            Inserted article ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO news_articles 
                       (source, title, url, published_date, summary, full_text, language, related_terms)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        article.source.value,
                        article.title,
                        article.url,
                        article.published_date.isoformat() if article.published_date else None,
                        article.summary,
                        article.full_text,
                        article.language,
                        json.dumps(article.related_terms, ensure_ascii=False)
                    )
                )
                await db.commit()
                return cursor.lastrowid
            except aiosqlite.IntegrityError:
                # URL already exists, return existing article ID
                async with db.execute(
                    "SELECT id FROM news_articles WHERE url = ?",
                    (article.url,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else -1
    
    async def insert_articles_batch(self, articles: List[NewsArticle]) -> List[int]:
        """
        Insert multiple articles, skipping duplicates.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            List of inserted article IDs
        """
        ids = []
        for article in articles:
            article_id = await self.insert_article(article)
            if article_id > 0:
                ids.append(article_id)
        return ids
    
    async def get_article(self, article_id: int) -> Optional[NewsArticle]:
        """Get an article by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM news_articles WHERE id = ?",
                (article_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_article(row)
        return None
    
    async def get_articles(
        self,
        source: str = None,
        language: str = None,
        days_back: int = 7,
        limit: int = 100,
        only_unannotated: bool = False
    ) -> List[NewsArticle]:
        """
        Get articles with optional filtering.
        
        Args:
            source: Filter by source
            language: Filter by language
            days_back: Only include articles from last N days
            limit: Maximum results
            only_unannotated: Only return articles without annotations
            
        Returns:
            List of NewsArticle objects
        """
        conditions = []
        params = []
        
        if source:
            conditions.append("source = ?")
            params.append(source)
        if language:
            conditions.append("language = ?")
            params.append(language)
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        conditions.append("published_date >= ?")
        params.append(cutoff_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        if only_unannotated:
            query = f"""
                SELECT a.* FROM news_articles a
                LEFT JOIN sentiment_annotations sa ON a.id = sa.article_id
                WHERE {where_clause} AND sa.id IS NULL
                ORDER BY a.published_date DESC
                LIMIT ?
            """
        else:
            query = f"""
                SELECT * FROM news_articles 
                WHERE {where_clause}
                ORDER BY published_date DESC
                LIMIT ?
            """
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, (*params, limit)) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_article(row) for row in rows]
    
    async def search_articles(
        self,
        term: str,
        days_back: int = 30,
        limit: int = 50
    ) -> List[NewsArticle]:
        """
        Search articles mentioning a specific term.
        
        Args:
            term: Term to search for
            days_back: Days of articles to search
            limit: Maximum results
            
        Returns:
            List of matching NewsArticle objects
        """
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        search_term = f"%{term}%"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM news_articles 
                   WHERE (title LIKE ? OR summary LIKE ? OR related_terms LIKE ?)
                   AND published_date >= ?
                   ORDER BY published_date DESC
                   LIMIT ?""",
                (search_term, search_term, search_term, cutoff_date, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_article(row) for row in rows]
    
    async def delete_article(self, article_id: int) -> bool:
        """Delete an article and its annotations (cascade)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute(
                "DELETE FROM news_articles WHERE id = ?",
                (article_id,)
            )
            await db.commit()
            return True
    
    def _row_to_article(self, row: aiosqlite.Row) -> NewsArticle:
        """Convert database row to NewsArticle object."""
        row_dict = dict(row)
        
        published_date = None
        if row_dict.get('published_date'):
            try:
                published_date = datetime.fromisoformat(row_dict['published_date'])
            except:
                pass
        
        related_terms = []
        if row_dict.get('related_terms'):
            try:
                related_terms = json.loads(row_dict['related_terms'])
            except:
                pass
        
        return NewsArticle(
            id=row_dict.get('id'),
            source=NewsSource(row_dict.get('source', 'custom')),
            title=row_dict.get('title', ''),
            url=row_dict.get('url', ''),
            published_date=published_date,
            summary=row_dict.get('summary'),
            full_text=row_dict.get('full_text'),
            language=row_dict.get('language', 'en'),
            related_terms=related_terms,
            created_at=datetime.fromisoformat(row_dict['created_at']) if row_dict.get('created_at') else None
        )
    
    # ==================== Annotation Operations ====================
    
    async def insert_annotation(self, annotation: SentimentAnnotation) -> int:
        """
        Insert a new sentiment annotation.
        
        Args:
            annotation: SentimentAnnotation object
            
        Returns:
            Inserted annotation ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO sentiment_annotations 
                   (article_id, sentiment_label, confidence_score, annotation_source,
                    reasoning, detected_entities, verified, verified_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    annotation.article_id,
                    annotation.sentiment_label.value,
                    annotation.confidence_score,
                    annotation.annotation_source.value,
                    annotation.reasoning,
                    json.dumps(annotation.detected_entities, ensure_ascii=False),
                    annotation.verified,
                    annotation.verified_by
                )
            )
            await db.commit()
            return cursor.lastrowid
    
    async def insert_annotations_batch(self, annotations: List[SentimentAnnotation]) -> List[int]:
        """Insert multiple annotations."""
        ids = []
        for annotation in annotations:
            annotation_id = await self.insert_annotation(annotation)
            ids.append(annotation_id)
        return ids
    
    async def get_annotations(
        self,
        article_id: int = None,
        sentiment_label: str = None,
        annotation_source: str = None,
        verified_only: bool = False,
        limit: int = 100
    ) -> List[SentimentAnnotation]:
        """
        Get annotations with optional filtering.
        
        Args:
            article_id: Filter by specific article
            sentiment_label: Filter by sentiment (bullish, bearish, neutral)
            annotation_source: Filter by annotation source
            verified_only: Only return verified annotations
            limit: Maximum results
            
        Returns:
            List of SentimentAnnotation objects with article info
        """
        conditions = []
        params = []
        
        if article_id:
            conditions.append("sa.article_id = ?")
            params.append(article_id)
        if sentiment_label:
            conditions.append("sa.sentiment_label = ?")
            params.append(sentiment_label)
        if annotation_source:
            conditions.append("sa.annotation_source = ?")
            params.append(annotation_source)
        if verified_only:
            conditions.append("sa.verified = 1")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                sa.*,
                a.title as article_title,
                a.url as article_url,
                a.source as article_source
            FROM sentiment_annotations sa
            JOIN news_articles a ON sa.article_id = a.id
            WHERE {where_clause}
            ORDER BY sa.created_at DESC
            LIMIT ?
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, (*params, limit)) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_annotation(row) for row in rows]
    
    async def verify_annotation(self, annotation_id: int, verified_by: str = "human") -> bool:
        """Mark an annotation as verified."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sentiment_annotations SET verified = 1, verified_by = ? WHERE id = ?",
                (verified_by, annotation_id)
            )
            await db.commit()
            return True
    
    async def update_annotation(
        self,
        annotation_id: int,
        sentiment_label: SentimentLabel,
        confidence_score: float = None,
        reasoning: str = None
    ) -> bool:
        """Update an annotation (for human corrections)."""
        async with aiosqlite.connect(self.db_path) as db:
            if confidence_score is not None:
                await db.execute(
                    """UPDATE sentiment_annotations 
                       SET sentiment_label = ?, confidence_score = ?, reasoning = ?,
                           verified = 1, verified_by = 'human_correction'
                       WHERE id = ?""",
                    (sentiment_label.value, confidence_score, reasoning, annotation_id)
                )
            else:
                await db.execute(
                    """UPDATE sentiment_annotations 
                       SET sentiment_label = ?, reasoning = ?,
                           verified = 1, verified_by = 'human_correction'
                       WHERE id = ?""",
                    (sentiment_label.value, reasoning, annotation_id)
                )
            await db.commit()
            return True
    
    def _row_to_annotation(self, row: aiosqlite.Row) -> SentimentAnnotation:
        """Convert database row to SentimentAnnotation object."""
        row_dict = dict(row)
        
        detected_entities = []
        if row_dict.get('detected_entities'):
            try:
                detected_entities = json.loads(row_dict['detected_entities'])
            except:
                pass
        
        return SentimentAnnotation(
            id=row_dict.get('id'),
            article_id=row_dict.get('article_id', 0),
            sentiment_label=SentimentLabel(row_dict.get('sentiment_label', 'neutral')),
            confidence_score=row_dict.get('confidence_score', 0.0),
            annotation_source=AnnotationSource(row_dict.get('annotation_source', 'rule_based')),
            reasoning=row_dict.get('reasoning'),
            detected_entities=detected_entities,
            verified=bool(row_dict.get('verified')),
            verified_by=row_dict.get('verified_by'),
            article_title=row_dict.get('article_title'),
            article_url=row_dict.get('article_url'),
            article_source=row_dict.get('article_source'),
            created_at=datetime.fromisoformat(row_dict['created_at']) if row_dict.get('created_at') else None
        )
    
    # ==================== Market Context Operations ====================
    
    async def insert_market_context(self, context: MarketContext) -> int:
        """Insert or update market context for a date."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO market_context 
                       (context_date, sp500_close, sp500_change_pct, nasdaq_close, nasdaq_change_pct,
                        vix_close, us_10y_yield, dxy_close, sse_close, sse_change_pct)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        context.context_date.isoformat() if context.context_date else None,
                        context.sp500_close,
                        context.sp500_change_pct,
                        context.nasdaq_close,
                        context.nasdaq_change_pct,
                        context.vix_close,
                        context.us_10y_yield,
                        context.dxy_close,
                        context.sse_close,
                        context.sse_change_pct
                    )
                )
                await db.commit()
                return cursor.lastrowid
            except aiosqlite.IntegrityError:
                # Date already exists, update
                await db.execute(
                    """UPDATE market_context SET
                       sp500_close = ?, sp500_change_pct = ?, nasdaq_close = ?, nasdaq_change_pct = ?,
                       vix_close = ?, us_10y_yield = ?, dxy_close = ?, sse_close = ?, sse_change_pct = ?
                       WHERE context_date = ?""",
                    (
                        context.sp500_close, context.sp500_change_pct,
                        context.nasdaq_close, context.nasdaq_change_pct,
                        context.vix_close, context.us_10y_yield, context.dxy_close,
                        context.sse_close, context.sse_change_pct,
                        context.context_date.isoformat()
                    )
                )
                await db.commit()
                return -1
    
    async def get_market_context(self, context_date: date) -> Optional[MarketContext]:
        """Get market context for a specific date."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM market_context WHERE context_date = ?",
                (context_date.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_market_context(row)
        return None
    
    async def get_market_context_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[MarketContext]:
        """Get market context for a date range."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM market_context 
                   WHERE context_date >= ? AND context_date <= ?
                   ORDER BY context_date""",
                (start_date.isoformat(), end_date.isoformat())
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_market_context(row) for row in rows]
    
    def _row_to_market_context(self, row: aiosqlite.Row) -> MarketContext:
        """Convert database row to MarketContext object."""
        row_dict = dict(row)
        
        context_date = None
        if row_dict.get('context_date'):
            try:
                context_date = date.fromisoformat(row_dict['context_date'])
            except:
                pass
        
        return MarketContext(
            id=row_dict.get('id'),
            context_date=context_date,
            sp500_close=row_dict.get('sp500_close'),
            sp500_change_pct=row_dict.get('sp500_change_pct'),
            nasdaq_close=row_dict.get('nasdaq_close'),
            nasdaq_change_pct=row_dict.get('nasdaq_change_pct'),
            vix_close=row_dict.get('vix_close'),
            us_10y_yield=row_dict.get('us_10y_yield'),
            dxy_close=row_dict.get('dxy_close'),
            sse_close=row_dict.get('sse_close'),
            sse_change_pct=row_dict.get('sse_change_pct'),
            created_at=datetime.fromisoformat(row_dict['created_at']) if row_dict.get('created_at') else None
        )
    
    # ==================== Trend Analysis Operations ====================
    
    async def update_term_frequency(
        self,
        term: str,
        frequency_date: date,
        mention_count: int,
        bullish_count: int,
        bearish_count: int,
        neutral_count: int
    ) -> int:
        """Insert or update term frequency for trend analysis."""
        avg_sentiment = 0.0
        total = bullish_count + bearish_count + neutral_count
        if total > 0:
            avg_sentiment = (bullish_count - bearish_count) / total
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    """INSERT INTO term_frequency 
                       (term, frequency_date, mention_count, bullish_count, bearish_count, neutral_count, avg_sentiment)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (term, frequency_date.isoformat(), mention_count, bullish_count, bearish_count, neutral_count, avg_sentiment)
                )
                await db.commit()
                return cursor.lastrowid
            except aiosqlite.IntegrityError:
                # Already exists, update
                await db.execute(
                    """UPDATE term_frequency SET
                       mention_count = ?, bullish_count = ?, bearish_count = ?, neutral_count = ?, avg_sentiment = ?
                       WHERE term = ? AND frequency_date = ?""",
                    (mention_count, bullish_count, bearish_count, neutral_count, avg_sentiment, term, frequency_date.isoformat())
                )
                await db.commit()
                return -1
    
    async def get_term_trend(
        self,
        term: str,
        days_back: int = 30
    ) -> List[TrendDataPoint]:
        """
        Get trend data for a specific term.
        
        Args:
            term: Term to analyze
            days_back: Days of data to retrieve
            
        Returns:
            List of TrendDataPoint objects ordered by date
        """
        start_date = (date.today() - timedelta(days=days_back)).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT tf.*, mc.sp500_change_pct, mc.nasdaq_change_pct
                   FROM term_frequency tf
                   LEFT JOIN market_context mc ON tf.frequency_date = mc.context_date
                   WHERE tf.term = ? AND tf.frequency_date >= ?
                   ORDER BY tf.frequency_date""",
                (term, start_date)
            ) as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    row_dict = dict(row)
                    market_ctx = MarketContext(
                        context_date=date.fromisoformat(row_dict['frequency_date']),
                        sp500_change_pct=row_dict.get('sp500_change_pct'),
                        nasdaq_change_pct=row_dict.get('nasdaq_change_pct')
                    ) if row_dict.get('sp500_change_pct') is not None else None
                    
                    result.append(TrendDataPoint(
                        date=date.fromisoformat(row_dict['frequency_date']),
                        term=row_dict['term'],
                        mention_count=row_dict.get('mention_count', 0),
                        avg_sentiment=row_dict.get('avg_sentiment', 0.0),
                        bullish_count=row_dict.get('bullish_count', 0),
                        bearish_count=row_dict.get('bearish_count', 0),
                        neutral_count=row_dict.get('neutral_count', 0),
                        market_context=market_ctx
                    ))
                return result
    
    # ==================== Statistics ====================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get Layer 3 statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Article counts by source
            async with db.execute(
                "SELECT source, COUNT(*) FROM news_articles GROUP BY source"
            ) as cursor:
                rows = await cursor.fetchall()
                stats["articles_by_source"] = {row[0]: row[1] for row in rows}
            
            # Total articles
            async with db.execute(
                "SELECT COUNT(*) FROM news_articles"
            ) as cursor:
                stats["total_articles"] = (await cursor.fetchone())[0]
            
            # Total annotations
            async with db.execute(
                "SELECT COUNT(*) FROM sentiment_annotations"
            ) as cursor:
                stats["total_annotations"] = (await cursor.fetchone())[0]
            
            # Annotations by sentiment
            async with db.execute(
                "SELECT sentiment_label, COUNT(*) FROM sentiment_annotations GROUP BY sentiment_label"
            ) as cursor:
                rows = await cursor.fetchall()
                stats["annotations_by_sentiment"] = {row[0]: row[1] for row in rows}
            
            # Verified vs unverified
            async with db.execute(
                "SELECT verified, COUNT(*) FROM sentiment_annotations GROUP BY verified"
            ) as cursor:
                rows = await cursor.fetchall()
                verified_counts = {int(row[0]): row[1] for row in rows}
                stats["verified_annotations"] = verified_counts.get(1, 0)
                stats["unverified_annotations"] = verified_counts.get(0, 0)
            
            # Annotation sources
            async with db.execute(
                "SELECT annotation_source, COUNT(*) FROM sentiment_annotations GROUP BY annotation_source"
            ) as cursor:
                rows = await cursor.fetchall()
                stats["annotations_by_source"] = {row[0]: row[1] for row in rows}
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            async with db.execute(
                "SELECT COUNT(*) FROM news_articles WHERE created_at >= ?",
                (week_ago,)
            ) as cursor:
                stats["articles_last_7_days"] = (await cursor.fetchone())[0]
            
            return stats
    
    # ==================== Export Helpers ====================
    
    async def get_all_articles(self) -> List[NewsArticle]:
        """Get all articles for export."""
        return await self.get_articles(days_back=365, limit=100000)
    
    async def get_all_annotations_with_articles(self) -> List[SentimentAnnotation]:
        """Get all annotations with article info for export."""
        return await self.get_annotations(limit=100000)
    
    async def get_annotated_articles_for_doccano(
        self,
        include_unannotated: bool = False,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get articles formatted for Doccano export.
        
        Returns:
            List of dicts with article text and labels
        """
        query = """
            SELECT 
                a.id, a.title, a.summary, a.source, a.url, a.published_date,
                sa.sentiment_label, sa.confidence_score, sa.reasoning
            FROM news_articles a
        """
        
        if include_unannotated:
            query += " LEFT JOIN sentiment_annotations sa ON a.id = sa.article_id"
        else:
            query += " JOIN sentiment_annotations sa ON a.id = sa.article_id"
        
        query += f" ORDER BY a.published_date DESC LIMIT {limit}"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    row_dict = dict(row)
                    result.append({
                        "id": row_dict['id'],
                        "text": f"{row_dict['title']}\n\n{row_dict.get('summary', '')}",
                        "meta": {
                            "source": row_dict['source'],
                            "url": row_dict['url'],
                            "date": row_dict['published_date']
                        },
                        "label": row_dict.get('sentiment_label'),
                        "confidence": row_dict.get('confidence_score'),
                        "reasoning": row_dict.get('reasoning')
                    })
                return result


# Convenience function for quick database initialization
async def init_layer3_database(db_path: str = "corpus.db"):
    """Initialize Layer 3 database tables."""
    db = SentimentDatabase(db_path)
    await db.initialize()
    return db


if __name__ == "__main__":
    import asyncio
    
    async def test_database():
        print("Testing Layer 3 Database")
        print("=" * 60)
        
        # Initialize database
        db = SentimentDatabase("test_layer3.db")
        await db.initialize()
        print("Database initialized.")
        
        # Create test article
        article = NewsArticle(
            source=NewsSource.BLOOMBERG,
            title="Fed signals slower pace of rate cuts amid sticky inflation",
            url="https://example.com/test-article-1",
            published_date=datetime.now(),
            summary="The Federal Reserve signaled it may slow the pace of interest rate cuts...",
            language="en",
            related_terms=["interest_rate", "inflation"]
        )
        
        # Insert article
        article_id = await db.insert_article(article)
        print(f"Inserted article ID: {article_id}")
        
        # Insert annotation
        annotation = SentimentAnnotation(
            article_id=article_id,
            sentiment_label=SentimentLabel.BEARISH,
            confidence_score=0.82,
            annotation_source=AnnotationSource.RULE_BASED,
            reasoning="Keywords 'slower pace' and 'sticky inflation' indicate bearish sentiment"
        )
        annotation_id = await db.insert_annotation(annotation)
        print(f"Inserted annotation ID: {annotation_id}")
        
        # Get statistics
        stats = await db.get_statistics()
        print(f"Statistics: {stats}")
        
        print("\nTest complete!")
    
    asyncio.run(test_database())

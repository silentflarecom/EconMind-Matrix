import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add Layer 3 to path
# Script is in layer3-sentiment/tests/
current_dir = Path(__file__).parent
layer3_root = current_dir.parent  # layer3-sentiment
project_root = layer3_root.parent # EconMind-Matrix

if str(layer3_root) not in sys.path:
    sys.path.insert(0, str(layer3_root))
# Also add project root for imports if needed (though we rely on layer3-sentiment imports)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger.info(f"Added {layer3_root} and {project_root} to sys.path")

try:
    from backend.database import SentimentDatabase
    from backend.models import NewsArticle, SentimentAnnotation, SentimentLabel, NewsSource, AnnotationSource
    from crawler.news_crawler import NewsCrawler
    from annotation.llm_annotator import RuleBasedAnnotator, SentimentResult
    from analysis.trend_analysis import TrendAnalyzer
except ImportError as e:
    logger.error(f"Import Error: {e}")
    sys.exit(1)

TEST_DB_FILE = os.path.join(current_dir, "test_layer3.db")

async def test_workflow():
    logger.info("Starting Layer 3 System Test...")
    
    # Clean up previous test
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
            logger.info(f"Removed old {TEST_DB_FILE}")
        except PermissionError:
            logger.warning(f"Could not remove {TEST_DB_FILE}, using existing or manual cleanup needed.")

    # 1. Initialize Database
    db = SentimentDatabase(TEST_DB_FILE)
    await db.initialize()
    logger.info("✓ Database initialized")

    # 2. Simulate Crawling
    logger.info("Simulating news crawling...")
    
    fake_articles = [
        NewsArticle(
            id=None,
            title="Inflation Rises Unexpectedly in November, Fed May Hold Rates",
            summary="Consumer prices increased by 0.5% last month, driven by energy costs. The Federal Reserve is now expected to keep interest rates steady.",
            source=NewsSource.REUTERS,
            url="http://fake.reuters.com/1",
            published_date=datetime.now() - timedelta(days=2),
            language="en"
        ),
        NewsArticle(
            id=None,
            title="Markets Rally as Inflation Shows Signs of Cooling",
            summary="Stock markets hit new highs today as the latest data suggests inflation is finally coming down.",
            source=NewsSource.BLOOMBERG,
            url="http://fake.bloomberg.com/1",
            published_date=datetime.now() - timedelta(days=1),
            language="en"
        ),
        NewsArticle(
            id=None,
            title="Central Bank Warns of Persistent Inflation Risks",
            summary="The central bank governor stated that while progress has been made, inflation remains a key risk for the economy.",
            source=NewsSource.WSJ,
            url="http://fake.wsj.com/1",
            published_date=datetime.now(),
            language="en"
        ),
        NewsArticle(
            id=None,
            title="Tech Stocks Surge Despite Rate Hike Fears",
            summary="Technology companies led the market gains.",
            source=NewsSource.FT,
            url="http://fake.ft.com/1",
            published_date=datetime.now(),
            language="en"
        )
    ]
    
    # Insert articles
    article_ids = await db.insert_articles_batch(fake_articles)
    logger.info(f"✓ Inserted {len(article_ids)} articles")
    
    # Verify insertion
    articles = await db.get_articles(limit=10)
    assert len(articles) == 4
    logger.info(f"✓ Verified article count: {len(articles)}")

    # 3. Test Search
    results = await db.search_articles("inflation")
    logger.info(f"✓ Search for 'inflation' returned {len(results)} articles (Expected ~3)")
    
    # 4. Sentiment Annotation (Rule-based)
    logger.info("Running Rule-Based Annotation...")
    annotator = RuleBasedAnnotator()
    
    annotated_count = 0
    for article in articles:
        # Simulate annotation
        result = annotator.annotate(article.title, article.summary)
        
        # Save to DB
        annotation = result.to_annotation(article_id=article.id)
        await db.insert_annotation(annotation)
        annotated_count += 1
        
        logger.info(f"  Article: {article.title[:30]}... -> {result.label.value} (Score: {result.score:.2f})")

    logger.info(f"✓ Annotated {annotated_count} articles")

    # 5. Trend Analysis
    logger.info("Testing Trend Analysis...")
    analyzer = TrendAnalyzer(TEST_DB_FILE)
    
    # Analyze 'inflation'
    trend_summary = await analyzer.analyze_term_trend("inflation", days_back=7)
    
    logger.info(f"Trend Analysis for 'inflation':")
    logger.info(f"  Total Mentions: {trend_summary.total_mentions}")
    logger.info(f"  Avg Sentiment: {trend_summary.avg_sentiment_score:.2f}")
    logger.info(f"  Trend Direction: {trend_summary.trend_direction}")
    
    # 6. Verify full data integration
    hot_terms = await analyzer.get_hot_terms(limit=5)
    logger.info(f"Hot Terms detected: {hot_terms}")

    logger.info("SUCCESS: All Layer 3 tests passed!")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_workflow())

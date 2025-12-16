"""
Layer 3: News Crawler Module
Crawls financial news from RSS feeds and news APIs

Usage:
    from news_crawler import NewsCrawler
    
    crawler = NewsCrawler()
    news_items = await crawler.crawl_all(days_back=7)
"""

import asyncio
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import time

# Third-party imports
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    print("⚠ feedparser not installed. Install with: pip install feedparser")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Import models
# Import models
try:
    # When imported as package
    from ..backend.models import NewsArticle, NewsSource, detect_related_terms
except (ImportError, ValueError):
    try:
        # When layer3-sentiment is in path (e.g. testing)
        from backend.models import NewsArticle, NewsSource, detect_related_terms
    except ImportError:
        # Fallback
        try:
            from models import NewsArticle, NewsSource, detect_related_terms
        except ImportError:
            pass


# Available news sources with RSS feeds - EXPANDED INTERNATIONAL COVERAGE
NEWS_SOURCES = {
    # === US News Sources (English) ===
    "bloomberg": {
        "name": "Bloomberg",
        "country": "US",
        "rss_urls": [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://feeds.bloomberg.com/economics/news.rss",
        ],
        "language": "en",
        "source_enum": NewsSource.BLOOMBERG
    },
    "reuters": {
        "name": "Reuters Business",
        "country": "UK/US",
        "rss_urls": [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.reuters.com/reuters/economicsNews",
        ],
        "language": "en",
        "source_enum": NewsSource.REUTERS
    },
    "wsj": {
        "name": "WSJ Markets",
        "country": "US",
        "rss_urls": [
            "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        ],
        "language": "en",
        "source_enum": NewsSource.WSJ
    },
    "ft": {
        "name": "Financial Times",
        "country": "UK",
        "rss_urls": [
            "https://www.ft.com/markets?format=rss",
            "https://www.ft.com/world/us?format=rss",
        ],
        "language": "en",
        "source_enum": NewsSource.FT
    },
    "cnbc": {
        "name": "CNBC",
        "country": "US",
        "rss_urls": [
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # Top News
            "https://www.cnbc.com/id/20910258/device/rss/rss.html",  # Economy
        ],
        "language": "en",
        "source_enum": NewsSource.CNBC
    },
    "marketwatch": {
        "name": "MarketWatch",
        "country": "US",
        "rss_urls": [
            "http://feeds.marketwatch.com/marketwatch/marketpulse/",
            "http://feeds.marketwatch.com/marketwatch/topstories/",
        ],
        "language": "en",
        "source_enum": NewsSource.MARKETWATCH
    },
    
    # === China (Chinese + English) ===
    "xinhua": {
        "name": "Xinhua Finance",
        "country": "CN",
        "rss_urls": [
            "http://www.xinhuanet.com/english/rss/financenews.xml",
        ],
        "language": "en",
        "source_enum": NewsSource.XINHUA
    },
    "chinadaily": {
        "name": "China Daily Business",
        "country": "CN",
        "rss_urls": [
            "http://www.chinadaily.com.cn/rss/business_rss.xml",
        ],
        "language": "en",
        "source_enum": NewsSource.CHINA_DAILY
    },
    "caixin": {
        "name": "Caixin Global",
        "country": "CN",
        "rss_urls": [
            "https://www.caixinglobal.com/feed/",  # English version has RSS
        ],
        "language": "en",
        "source_enum": NewsSource.CAIXIN
    },
    
    # === Japan (Japanese + English) ===
    "nikkei": {
        "name": "Nikkei Asia",
        "country": "JP",
        "rss_urls": [
            "https://asia.nikkei.com/rss/feed/nar",
        ],
        "language": "en",
        "source_enum": NewsSource.NIKKEI
    },
    "japantimes": {
        "name": "Japan Times Business",
        "country": "JP",
        "rss_urls": [
            "https://www.japantimes.co.jp/feed/topstories/",
        ],
        "language": "en",
        "source_enum": NewsSource.JAPAN_TIMES
    },
    
    # === Germany (German + English) ===
    "handelsblatt": {
        "name": "Handelsblatt (English)",
        "country": "DE",
        "rss_urls": [
            "https://www.handelsblatt.com/contentexport/feed/top-themen",
        ],
        "language": "de",
        "source_enum": NewsSource.HANDELSBLATT
    },
    "dw": {
        "name": "Deutsche Welle Business",
        "country": "DE",
        "rss_urls": [
            "https://rss.dw.com/xml/rss-en-bus",
        ],
        "language": "en",
        "source_enum": NewsSource.DW
    },
    
    # === France (French + English) ===
    "lesechos": {
        "name": "Les Échos",
        "country": "FR",
        "rss_urls": [
            "https://www.lesechos.fr/rss/fils-finance-marches.xml",
        ],
        "language": "fr",
        "source_enum": NewsSource.LES_ECHOS
    },
    
    # === UK ===
    "bbc": {
        "name": "BBC Business",
        "country": "UK",
        "rss_urls": [
            "http://feeds.bbci.co.uk/news/business/rss.xml",
        ],
        "language": "en",
        "source_enum": NewsSource.BBC
    },
    "guardian": {
        "name": "The Guardian Business",
        "country": "UK",
        "rss_urls": [
            "https://www.theguardian.com/business/rss",
            "https://www.theguardian.com/business/economics/rss",
        ],
        "language": "en",
        "source_enum": NewsSource.GUARDIAN
    },
    
    # === Australia ===
    "afr": {
        "name": "Australian Financial Review",
        "country": "AU",
        "rss_urls": [
            "https://www.afr.com/rss/markets",  # Updated working URL
            "https://www.afr.com/rss/companies",
        ],
        "language": "en",
        "source_enum": NewsSource.AFR
    },
    "smh": {
        "name": "Sydney Morning Herald Business",
        "country": "AU",
        "rss_urls": [
            "https://www.smh.com.au/rss/business.xml",
        ],
        "language": "en",
        "source_enum": NewsSource.SMH
    },
    
    # === India ===
    "economictimes": {
        "name": "Economic Times India",
        "country": "IN",
        "rss_urls": [
            "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
        ],
        "language": "en",
        "source_enum": NewsSource.ECONOMIC_TIMES
    },
    
    # === South Korea ===
    "koreaherald": {
        "name": "Korea Herald Business",
        "country": "KR",
        "rss_urls": [
            "http://www.koreaherald.com/common/rss_xml.php?ct=11",
        ],
        "language": "en",
        "source_enum": NewsSource.KOREA_HERALD
    },
    
    # === Canada ===
    "globeandmail": {
        "name": "Globe and Mail Business",
        "country": "CA",
        "rss_urls": [
            "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
        ],
        "language": "en",
        "source_enum": NewsSource.GLOBE_AND_MAIL
    },
    
    # === International/Multi-region ===
    "yahoo_finance": {
        "name": "Yahoo Finance",
        "country": "GLOBAL",
        "rss_urls": [
            "https://finance.yahoo.com/news/rssindex",
        ],
        "language": "en",
        "source_enum": NewsSource.YAHOO_FINANCE
    },
}

# Common term variants for search
TERM_VARIANTS = {
    "inflation": ["inflation", "inflationary", "price increase", "cpi", "pce"],
    "recession": ["recession", "recessionary", "economic downturn", "contraction"],
    "interest_rate": ["interest rate", "rate hike", "rate cut", "fed funds", "policy rate"],
    "gdp": ["gdp", "economic growth", "growth rate"],
    "unemployment": ["unemployment", "jobless", "labor market", "employment"],
    "fed": ["federal reserve", "fed", "fomc", "powell"],
    "pboc": ["people's bank of china", "pboc", "中国人民银行"],
    "trade": ["trade war", "tariff", "trade deficit", "trade surplus"],
    "bonds": ["treasury", "bond", "yield curve", "fixed income"],
    "stock": ["stock market", "equity", "s&p 500", "dow jones", "nasdaq"],
}


# User-Agent pool for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

class NewsCrawler:
    """
    Advanced News Crawler with:
    - User-Agent rotation
    - Proxy pool support
    - Concurrency control
    - Custom delay
    - Manual start/stop
    """
    
    def __init__(
        self,
        sources: List[str] = None,
        proxies: List[str] = None,
        max_concurrent: int = 3,
        delay_seconds: float = 1.0,
        rotate_user_agent: bool = True
    ):
        """
        Initialize crawler with advanced options.
        
        Args:
            sources: List of source keys from NEWS_SOURCES
            proxies: List of proxy URLs (e.g., ["http://proxy1:8080", "socks5://proxy2:1080"])
            max_concurrent: Maximum concurrent requests (1-10)
            delay_seconds: Delay between requests in seconds (0.5-10)
            rotate_user_agent: Whether to rotate User-Agent for each request
        """
        if sources is None:
            self.sources = [k for k, v in NEWS_SOURCES.items() if v.get("rss_urls")]
        else:
            self.sources = [s for s in sources if s in NEWS_SOURCES]
        
        self.proxies = proxies or []
        self.max_concurrent = max(1, min(10, max_concurrent))
        self.delay_seconds = max(0.5, min(10, delay_seconds))
        self.rotate_user_agent = rotate_user_agent
        
        # State
        self._session = None
        self._is_running = False
        self._should_stop = False
        self._current_proxy_idx = 0
        self._crawl_stats = {
            "articles_found": 0,
            "sources_completed": 0,
            "current_source": None,
            "errors": [],
            "started_at": None,
            "stopped_at": None
        }
        self._semaphore = None
    
    def _get_user_agent(self) -> str:
        """Get a random User-Agent from the pool."""
        import random
        if self.rotate_user_agent:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]
    
    def _get_proxy(self) -> Optional[str]:
        """Get next proxy from pool (round-robin)."""
        if not self.proxies:
            return None
        proxy = self.proxies[self._current_proxy_idx % len(self.proxies)]
        self._current_proxy_idx += 1
        return proxy
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def stats(self) -> dict:
        return self._crawl_stats.copy()
    
    def stop(self):
        """Signal the crawler to stop after current operation."""
        self._should_stop = True
        self._crawl_stats["stopped_at"] = datetime.now().isoformat()
        print("⏹ Crawler stop requested...")
    
    async def _get_session(self):
        """Get or create aiohttp session with current User-Agent."""
        if self._session is None and AIOHTTP_AVAILABLE:
            import aiohttp
            connector = aiohttp.TCPConnector(limit=self.max_concurrent, ssl=False)
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": self._get_user_agent()},
                timeout=aiohttp.ClientTimeout(total=30),
                connector=connector
            )
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
        self._is_running = False
    
    def _parse_date(self, entry: Dict) -> Optional[datetime]:
        """Parse date from RSS entry."""
        # Try different date fields
        for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if date_field in entry and entry[date_field]:
                try:
                    tt = entry[date_field]
                    return datetime(tt[0], tt[1], tt[2], tt[3], tt[4], tt[5])
                except:
                    pass
        
        # Try string date fields
        for date_field in ['published', 'updated', 'created']:
            if date_field in entry and entry[date_field]:
                try:
                    from email.utils import parsedate_to_datetime
                    return parsedate_to_datetime(entry[date_field])
                except:
                    pass
        
        return datetime.now()
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&#39;', "'")
        clean = clean.replace('&nbsp;', ' ')
        # Clean whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    async def crawl_rss(self, source_key: str) -> List[NewsArticle]:
        """
        Crawl news from a single RSS source.
        
        Args:
            source_key: Key from NEWS_SOURCES
            
        Returns:
            List of NewsArticle objects
        """
        # Check stop signal
        if self._should_stop:
            return []
            
        if not FEEDPARSER_AVAILABLE:
            print(f"⚠ Cannot crawl {source_key}: feedparser not installed")
            return []
        
        source = NEWS_SOURCES.get(source_key)
        if not source or not source.get("rss_urls"):
            return []
        
        articles = []
        user_agent = self._get_user_agent()
        
        self._crawl_stats["current_source"] = source_key
        
        for rss_url in source["rss_urls"]:
            # Check stop signal before each URL
            if self._should_stop:
                break
                
            try:
                # Use rotating User-Agent
                feed = feedparser.parse(
                    rss_url,
                    agent=user_agent,
                    request_headers={
                        'User-Agent': user_agent,
                        'Accept': 'application/rss+xml, application/xml, text/xml',
                    }
                )
                
                # Check for errors
                if hasattr(feed, 'status') and feed.status >= 400:
                    print(f"⚠ HTTP {feed.status} for {source_key}: {rss_url}")
                    self._crawl_stats["errors"].append(f"{source_key}: HTTP {feed.status}")
                    continue
                
                if feed.bozo and feed.bozo_exception:
                    error_type = type(feed.bozo_exception).__name__
                    print(f"⚠ RSS parse warning for {source_key} ({error_type}): {str(feed.bozo_exception)[:100]}")
                    if not feed.entries:
                        continue
                
                for entry in feed.entries:
                    title = self._clean_html(entry.get('title', ''))
                    if not title:
                        continue
                    
                    summary = self._clean_html(entry.get('summary', '') or entry.get('description', ''))
                    url = entry.get('link', '')
                    published_date = self._parse_date(entry)
                    
                    text_for_analysis = f"{title} {summary}"
                    related_terms = detect_related_terms(text_for_analysis, source.get("language", "en"))
                    
                    article = NewsArticle(
                        source=source.get("source_enum", NewsSource.CUSTOM),
                        title=title,
                        url=url,
                        published_date=published_date,
                        summary=summary[:1000] if summary else None,
                        language=source.get("language", "en"),
                        related_terms=related_terms
                    )
                    articles.append(article)
                
                if articles:
                    print(f"  ✓ Fetched {len(articles)} articles from {rss_url[:50]}...")
                
                # Apply delay between requests
                await asyncio.sleep(self.delay_seconds)
                
            except Exception as e:
                error_msg = str(e)
                if "SSL" in error_msg or "CERTIFICATE" in error_msg:
                    print(f"✗ SSL error for {source_key}: {rss_url[:60]}...")
                elif "timeout" in error_msg.lower():
                    print(f"✗ Timeout for {source_key}: {rss_url[:60]}...")
                elif "403" in error_msg or "forbidden" in error_msg.lower():
                    print(f"✗ Access forbidden for {source_key}: {rss_url[:60]}...")
                else:
                    print(f"✗ Error crawling {source_key}: {error_msg[:100]}")
                self._crawl_stats["errors"].append(f"{source_key}: {error_msg[:50]}")
                continue
        
        self._crawl_stats["articles_found"] += len(articles)
        return articles
    
    async def crawl_all(
        self,
        days_back: int = 7,
        keywords: List[str] = None,
        limit_per_source: int = 50
    ) -> List[NewsArticle]:
        """
        Crawl news from all configured sources.
        
        Args:
            days_back: Only include news from the last N days
            keywords: Optional filter by keywords in title
            limit_per_source: Maximum articles per source
            
        Returns:
            List of NewsArticle objects, sorted by date (newest first)
        """
        # Initialize state
        self._is_running = True
        self._should_stop = False
        self._crawl_stats = {
            "articles_found": 0,
            "sources_completed": 0,
            "current_source": None,
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "stopped_at": None
        }
        
        all_articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Crawl each source
        for i, source_key in enumerate(self.sources):
            # Check stop signal
            if self._should_stop:
                print(f"⏹ Crawl stopped by user after {i} sources")
                break
                
            try:
                print(f"📰 Crawling {NEWS_SOURCES[source_key]['name']}...")
                articles = await self.crawl_rss(source_key)
                
                # Filter by date
                articles = [a for a in articles if a.published_date and a.published_date >= cutoff_date]
                
                # Limit per source
                articles = articles[:limit_per_source]
                
                all_articles.extend(articles)
                self._crawl_stats["sources_completed"] = i + 1
                print(f"  ✓ Found {len(articles)} articles from {source_key}")
                
            except Exception as e:
                print(f"✗ Error crawling {source_key}: {e}")
                self._crawl_stats["errors"].append(f"{source_key}: {str(e)[:50]}")
        
        # Filter by keywords if specified
        if keywords and not self._should_stop:
            keywords_lower = [k.lower() for k in keywords]
            all_articles = [
                article for article in all_articles
                if any(kw in article.title.lower() for kw in keywords_lower)
            ]
        
        # Sort by date (newest first)
        all_articles.sort(key=lambda x: x.published_date or datetime.min, reverse=True)
        
        # Update final stats
        self._is_running = False
        self._crawl_stats["articles_found"] = len(all_articles)
        
        return all_articles
    
    async def crawl_for_term(
        self,
        term: str,
        days_back: int = 30,
        include_variants: bool = True
    ) -> List[NewsArticle]:
        """
        Crawl news related to a specific economic term.
        
        Args:
            term: Term to search for (e.g., "Inflation")
            days_back: Days of news to search
            include_variants: Whether to include common variants
            
        Returns:
            List of NewsArticle objects mentioning the term
        """
        search_terms = [term.lower()]
        
        if include_variants:
            # Add common variants
            term_key = term.lower().replace(" ", "_")
            variants = TERM_VARIANTS.get(term_key, [])
            search_terms.extend([v.lower() for v in variants])
        
        # Get all articles
        all_articles = await self.crawl_all(days_back=days_back)
        
        # Filter by term
        matching = [
            article for article in all_articles
            if any(t in article.title.lower() or (article.summary and t in article.summary.lower()) 
                   for t in search_terms)
        ]
        
        return matching
    
    def filter_by_term(
        self,
        articles: List[NewsArticle],
        term: str,
        include_variants: bool = True
    ) -> List[NewsArticle]:
        """
        Filter existing articles by economic term.
        
        Args:
            articles: List of NewsArticle objects
            term: Term to search for (e.g., "Inflation")
            include_variants: Whether to include common variants
            
        Returns:
            Filtered list of NewsArticle objects
        """
        search_terms = [term.lower()]
        
        if include_variants:
            term_key = term.lower().replace(" ", "_")
            variants = TERM_VARIANTS.get(term_key, [])
            search_terms.extend([v.lower() for v in variants])
        
        return [
            article for article in articles
            if any(t in article.title.lower() or (article.summary and t in article.summary.lower())
                   for t in search_terms)
        ]
    
    @staticmethod
    def get_available_sources() -> Dict[str, Dict]:
        """Get information about available news sources."""
        return {
            key: {
                "name": info["name"],
                "language": info["language"],
                "has_rss": bool(info.get("rss_urls")),
                "rss_count": len(info.get("rss_urls", []))
            }
            for key, info in NEWS_SOURCES.items()
        }


# Synchronous wrapper for testing
def crawl_sync(sources: List[str] = None, days_back: int = 7) -> List[NewsArticle]:
    """Synchronous wrapper for crawl_all."""
    async def _crawl():
        crawler = NewsCrawler(sources=sources)
        try:
            return await crawler.crawl_all(days_back=days_back)
        finally:
            await crawler.close()
    
    return asyncio.run(_crawl())


if __name__ == "__main__":
    print("=" * 60)
    print("Testing News Crawler")
    print("=" * 60)
    
    # Show available sources
    print("\nAvailable sources:")
    for key, info in NewsCrawler.get_available_sources().items():
        status = "✓ RSS" if info["has_rss"] else "✗ No RSS"
        print(f"  {key}: {info['name']} ({info['language']}) - {status}")
    
    if not FEEDPARSER_AVAILABLE:
        print("\n⚠ feedparser not installed. Install with: pip install feedparser")
        print("Skipping crawl test.")
    else:
        print("\nTesting crawl (last 3 days, limited sources)...")
        
        async def test_crawl():
            crawler = NewsCrawler(sources=["reuters", "wsj"])
            try:
                articles = await crawler.crawl_all(days_back=3, limit_per_source=5)
                print(f"\nFound {len(articles)} articles total")
                
                for i, article in enumerate(articles[:5], 1):
                    print(f"\n[{i}] {article.title[:60]}...")
                    print(f"    Source: {article.source.value}")
                    print(f"    Date: {article.published_date}")
                    print(f"    Terms: {article.related_terms}")
                
            finally:
                await crawler.close()
        
        asyncio.run(test_crawl())
    
    print("\n" + "=" * 60)
    print("Test complete!")

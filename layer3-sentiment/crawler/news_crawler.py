"""
Layer 3: News Crawler Module
Crawls financial news from RSS feeds and news APIs

Usage:
    from news_crawler import NewsCrawler
    
    crawler = NewsCrawler()
    news_items = crawler.crawl_all(days_back=7)
"""

import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# feedparser for RSS (install with: pip install feedparser)
# import feedparser

# Available news sources
NEWS_SOURCES = {
    "bloomberg": {
        "name": "Bloomberg",
        "rss_url": "https://feeds.bloomberg.com/markets/news.rss",
        "language": "en"
    },
    "reuters_business": {
        "name": "Reuters Business",
        "rss_url": "https://feeds.reuters.com/reuters/businessNews",
        "language": "en"
    },
    "wsj_markets": {
        "name": "WSJ Markets",
        "rss_url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "language": "en"
    },
    "ft_markets": {
        "name": "Financial Times",
        "rss_url": "https://www.ft.com/markets?format=rss",
        "language": "en"
    },
    # Chinese sources
    "caixin": {
        "name": "Caixin",
        "rss_url": None,  # Caixin doesn't have public RSS, need API
        "language": "zh"
    },
    "yicai": {
        "name": "Yicai (第一财经)",
        "rss_url": None,
        "language": "zh"
    }
}


@dataclass
class NewsItem:
    """Represents a single news item."""
    title: str
    source: str
    url: str
    published_date: datetime
    summary: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_date": self.published_date.isoformat(),
            "summary": self.summary
        }


class NewsCrawler:
    """
    Crawls financial news from various RSS feeds.
    """
    
    def __init__(self, sources: List[str] = None):
        """
        Initialize crawler with specific sources.
        
        Args:
            sources: List of source keys from NEWS_SOURCES
                    If None, uses all available sources with RSS
        """
        if sources is None:
            # Use all sources that have RSS feeds
            self.sources = [k for k, v in NEWS_SOURCES.items() if v.get("rss_url")]
        else:
            self.sources = sources
    
    def crawl_rss(self, source_key: str) -> List[NewsItem]:
        """
        Crawl news from a single RSS feed.
        
        Args:
            source_key: Key from NEWS_SOURCES
            
        Returns:
            List of NewsItem objects
        """
        # TODO: Implement RSS parsing
        # 
        # Example implementation:
        # import feedparser
        # source = NEWS_SOURCES[source_key]
        # feed = feedparser.parse(source["rss_url"])
        # 
        # items = []
        # for entry in feed.entries:
        #     items.append(NewsItem(
        #         title=entry.title,
        #         source=source["name"],
        #         url=entry.link,
        #         published_date=datetime(*entry.published_parsed[:6]),
        #         summary=entry.get("summary", "")
        #     ))
        # return items
        
        raise NotImplementedError(
            "RSS parsing not yet implemented. "
            "Install with: pip install feedparser"
        )
    
    def crawl_all(
        self, 
        days_back: int = 7,
        keywords: List[str] = None
    ) -> List[NewsItem]:
        """
        Crawl news from all configured sources.
        
        Args:
            days_back: Only include news from the last N days
            keywords: Optional filter by keywords in title
            
        Returns:
            List of NewsItem objects, sorted by date (newest first)
        """
        all_items = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for source_key in self.sources:
            try:
                items = self.crawl_rss(source_key)
                # Filter by date
                items = [i for i in items if i.published_date >= cutoff_date]
                all_items.extend(items)
            except Exception as e:
                print(f"Error crawling {source_key}: {e}")
        
        # Filter by keywords if specified
        if keywords:
            keywords_lower = [k.lower() for k in keywords]
            all_items = [
                item for item in all_items
                if any(kw in item.title.lower() for kw in keywords_lower)
            ]
        
        # Sort by date (newest first)
        all_items.sort(key=lambda x: x.published_date, reverse=True)
        return all_items
    
    def filter_by_term(
        self, 
        items: List[NewsItem], 
        term: str,
        include_variants: bool = True
    ) -> List[NewsItem]:
        """
        Filter news items by economic term.
        
        Args:
            items: List of NewsItem objects
            term: Term to search for (e.g., "Inflation")
            include_variants: Whether to include common variants
            
        Returns:
            Filtered list of NewsItem objects
        """
        search_terms = [term.lower()]
        
        if include_variants:
            # Add common variants
            variants = TERM_VARIANTS.get(term.lower(), [])
            search_terms.extend([v.lower() for v in variants])
        
        return [
            item for item in items
            if any(t in item.title.lower() for t in search_terms)
        ]


# Common term variants for search
TERM_VARIANTS = {
    "inflation": ["inflation", "inflationary", "price increase", "cpi"],
    "recession": ["recession", "recessionary", "economic downturn", "contraction"],
    "interest rate": ["interest rate", "rate hike", "rate cut", "fed funds", "policy rate"],
    "gdp": ["gdp", "economic growth", "growth rate"],
    "unemployment": ["unemployment", "jobless", "labor market", "employment"]
}


if __name__ == "__main__":
    # Test crawler
    print("Testing news crawler...")
    
    crawler = NewsCrawler(sources=["bloomberg", "reuters_business"])
    
    try:
        items = crawler.crawl_all(days_back=7, keywords=["inflation", "fed"])
        print(f"Found {len(items)} news items")
        for item in items[:5]:
            print(f"- {item.title[:60]}... ({item.source})")
    except NotImplementedError as e:
        print(f"Note: {e}")
        print("Once feedparser is installed, crawling will work.")

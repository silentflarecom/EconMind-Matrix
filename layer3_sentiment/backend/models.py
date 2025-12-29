"""
Layer 3: Sentiment & News Data Models
Database models and Pydantic schemas for financial news sentiment analysis.

Integrates with Layer 1 terminology and Layer 2 policy by linking to terms and topics.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class NewsSource(Enum):
    """News source identifiers - International Coverage."""
    # US
    BLOOMBERG = "bloomberg"
    REUTERS = "reuters"
    WSJ = "wsj"
    FT = "ft"
    CNBC = "cnbc"
    MARKETWATCH = "marketwatch"
    YAHOO_FINANCE = "yahoo_finance"
    
    # China
    XINHUA = "xinhua"
    CHINA_DAILY = "chinadaily"
    CAIXIN = "caixin"
    YICAI = "yicai"
    
    # Japan
    NIKKEI = "nikkei"
    JAPAN_TIMES = "japantimes"
    
    # Germany
    HANDELSBLATT = "handelsblatt"
    DW = "dw"
    
    # France
    LES_ECHOS = "lesechos"
    
    # UK
    BBC = "bbc"
    GUARDIAN = "guardian"
    
    # Australia
    AFR = "afr"
    SMH = "smh"
    
    # India
    ECONOMIC_TIMES = "economictimes"
    
    # South Korea
    KOREA_HERALD = "koreaherald"
    
    # Canada
    GLOBE_AND_MAIL = "globeandmail"
    
    # Custom
    CUSTOM = "custom"


class SentimentLabel(Enum):
    """Sentiment labels for financial news."""
    BULLISH = "bullish"      # Positive for markets
    BEARISH = "bearish"      # Negative for markets
    NEUTRAL = "neutral"      # No clear market impact


class AnnotationSource(Enum):
    """Source of the annotation."""
    LLM_GEMINI = "llm_gemini"
    LLM_GPT = "llm_gpt"
    RULE_BASED = "rule_based"
    HUMAN = "human"
    DOCCANO = "doccano"


# Economic term variants for news filtering
ECONOMIC_TERM_VARIANTS = {
    "inflation": ["inflation", "inflationary", "price increase", "cpi", "pce", "deflation"],
    "recession": ["recession", "recessionary", "economic downturn", "contraction", "slowdown"],
    "interest_rate": ["interest rate", "rate hike", "rate cut", "fed funds", "policy rate", "benchmark rate"],
    "gdp": ["gdp", "economic growth", "growth rate", "expansion"],
    "unemployment": ["unemployment", "jobless", "labor market", "employment", "workforce"],
    "trade": ["trade war", "tariff", "export", "import", "trade deficit", "trade surplus"],
    "currency": ["exchange rate", "dollar", "yuan", "forex", "appreciation", "depreciation"],
    "stock_market": ["stock", "equity", "s&p 500", "dow jones", "nasdaq", "bull market", "bear market"],
    "bonds": ["bond", "treasury", "yield", "fixed income", "credit spread"],
    "real_estate": ["housing", "real estate", "mortgage", "property", "home prices"],
}

# Chinese term variants
ECONOMIC_TERM_VARIANTS_ZH = {
    "inflation": ["通胀", "通货膨胀", "物价上涨", "CPI", "消费价格"],
    "recession": ["衰退", "经济下行", "收缩", "萎缩"],
    "interest_rate": ["利率", "加息", "降息", "基准利率", "政策利率"],
    "gdp": ["GDP", "经济增长", "增速", "国内生产总值"],
    "unemployment": ["失业", "就业", "劳动力市场", "失业率"],
    "trade": ["贸易战", "关税", "出口", "进口", "贸易顺差", "贸易逆差"],
    "currency": ["汇率", "人民币", "美元", "外汇", "汇率升值", "汇率贬值"],
    "stock_market": ["股市", "股票", "上证指数", "深证指数", "牛市", "熊市"],
    "bonds": ["债券", "国债", "收益率", "信用利差"],
    "real_estate": ["房地产", "房价", "房贷", "楼市"],
}


@dataclass
class NewsArticle:
    """Represents a news article."""
    id: Optional[int] = None
    source: NewsSource = NewsSource.CUSTOM
    title: str = ""
    url: str = ""
    published_date: Optional[datetime] = None
    summary: Optional[str] = None
    full_text: Optional[str] = None
    language: str = "en"
    related_terms: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source.value,
            "title": self.title,
            "url": self.url,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "summary": self.summary,
            "language": self.language,
            "related_terms": self.related_terms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class SentimentAnnotation:
    """Represents a sentiment annotation for a news article."""
    id: Optional[int] = None
    article_id: int = 0
    sentiment_label: SentimentLabel = SentimentLabel.NEUTRAL
    confidence_score: float = 0.0
    annotation_source: AnnotationSource = AnnotationSource.RULE_BASED
    reasoning: Optional[str] = None
    detected_entities: List[str] = field(default_factory=list)
    verified: bool = False
    verified_by: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Populated when fetching with joins
    article_title: Optional[str] = None
    article_url: Optional[str] = None
    article_source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "article_id": self.article_id,
            "sentiment": {
                "label": self.sentiment_label.value,
                "score": round(self.confidence_score, 4)
            },
            "annotation_source": self.annotation_source.value,
            "reasoning": self.reasoning,
            "detected_entities": self.detected_entities,
            "verified": self.verified,
            "verified_by": self.verified_by,
            "article_title": self.article_title,
            "article_url": self.article_url,
            "article_source": self.article_source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class MarketContext:
    """Market data context for a specific date."""
    id: Optional[int] = None
    context_date: date = None
    sp500_close: Optional[float] = None
    sp500_change_pct: Optional[float] = None
    nasdaq_close: Optional[float] = None
    nasdaq_change_pct: Optional[float] = None
    vix_close: Optional[float] = None
    us_10y_yield: Optional[float] = None
    dxy_close: Optional[float] = None  # Dollar index
    sse_close: Optional[float] = None  # Shanghai Composite
    sse_change_pct: Optional[float] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.context_date.isoformat() if self.context_date else None,
            "sp500": {"close": self.sp500_close, "change_pct": self.sp500_change_pct},
            "nasdaq": {"close": self.nasdaq_close, "change_pct": self.nasdaq_change_pct},
            "vix": self.vix_close,
            "us_10y_yield": self.us_10y_yield,
            "dxy": self.dxy_close,
            "sse": {"close": self.sse_close, "change_pct": self.sse_change_pct}
        }


@dataclass
class TrendDataPoint:
    """Represents a data point in a time series trend."""
    date: date
    term: str
    mention_count: int = 0
    avg_sentiment: float = 0.0
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    market_context: Optional[MarketContext] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "term": self.term,
            "mention_count": self.mention_count,
            "avg_sentiment": round(self.avg_sentiment, 4),
            "sentiment_breakdown": {
                "bullish": self.bullish_count,
                "bearish": self.bearish_count,
                "neutral": self.neutral_count
            },
            "market_context": self.market_context.to_dict() if self.market_context else None
        }


# Pydantic models for API requests/responses
try:
    from pydantic import BaseModel, Field
    
    class CrawlRequest(BaseModel):
        """Request model for news crawling."""
        sources: List[str] = Field(default=["bloomberg", "reuters"], description="News sources to crawl")
        days_back: int = Field(default=7, ge=1, le=30, description="Days of news to fetch")
        keywords: Optional[List[str]] = Field(None, description="Filter by keywords")
    
    class AnnotateRequest(BaseModel):
        """Request model for sentiment annotation."""
        article_ids: Optional[List[int]] = Field(None, description="Specific article IDs to annotate")
        method: str = Field(default="auto", description="Annotation method: auto, llm, rule_based")
        force_reannotate: bool = Field(default=False, description="Re-annotate even if already annotated")
    
    class TrendRequest(BaseModel):
        """Request model for trend analysis."""
        term: str = Field(..., description="Economic term to analyze")
        days_back: int = Field(default=30, ge=7, le=365, description="Days of data to analyze")
        include_market_data: bool = Field(default=True, description="Include market context")
    
    class DoccanoExportRequest(BaseModel):
        """Request model for Doccano export."""
        format: str = Field(default="jsonl", description="Export format: jsonl, csv")
        include_unannotated: bool = Field(default=False, description="Include articles without annotations")
        limit: int = Field(default=1000, ge=1, le=10000, description="Maximum articles to export")

except ImportError:
    # Pydantic not installed, skip API models
    pass

# SQL statements for creating Layer 3 tables
# Centralized in shared/schema.py (Issue #6 fix)
try:
    from shared.schema import LAYER3_SQL_SCHEMA
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from shared.schema import LAYER3_SQL_SCHEMA


def detect_related_terms(text: str, language: str = "auto") -> List[str]:
    """
    Detect economic terms mentioned in text.
    
    Args:
        text: Text to analyze
        language: Language code or "auto" to detect
        
    Returns:
        List of detected term keys
    """
    text_lower = text.lower()
    
    # Auto-detect language
    if language == "auto":
        import re
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        language = "zh" if chinese_chars > english_words else "en"
    
    variants_dict = ECONOMIC_TERM_VARIANTS_ZH if language == "zh" else ECONOMIC_TERM_VARIANTS
    
    detected = []
    for term_key, variants in variants_dict.items():
        for variant in variants:
            if variant.lower() in text_lower:
                detected.append(term_key)
                break
    
    return list(set(detected))


def calculate_sentiment_score(label: SentimentLabel, confidence: float) -> float:
    """
    Convert sentiment label and confidence to a numeric score.
    
    Returns:
        Score from -1.0 (very bearish) to +1.0 (very bullish)
    """
    if label == SentimentLabel.BULLISH:
        return confidence
    elif label == SentimentLabel.BEARISH:
        return -confidence
    else:
        return 0.0

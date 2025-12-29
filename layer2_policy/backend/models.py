"""
Layer 2: Policy Report Data Models
Database models and Pydantic schemas for policy reports

Integrate with Layer 1 database by extending the existing schema.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class ReportSource(Enum):
    """Policy report source identifiers."""
    PBOC = "pboc"           # People's Bank of China
    FED = "fed"             # Federal Reserve
    ECB = "ecb"             # European Central Bank (future)
    BOJ = "boj"             # Bank of Japan (future)


class ReportType(Enum):
    """Types of policy reports."""
    MONETARY_POLICY = "monetary_policy"      # PBOC Monetary Policy Report
    BEIGE_BOOK = "beige_book"                # Fed Beige Book
    FOMC_MINUTES = "fomc_minutes"            # FOMC Meeting Minutes
    FOMC_STATEMENT = "fomc_statement"        # FOMC Statement
    FINANCIAL_STABILITY = "financial_stability"


class AlignmentMethod(Enum):
    """Methods used for paragraph alignment."""
    SENTENCE_BERT = "sentence_bert"
    TOPIC_CLUSTERING = "topic_clustering"
    KEYWORD_MATCHING = "keyword_matching"
    MANUAL = "manual"


# Topic categories for policy reports
POLICY_TOPICS = {
    "inflation": {
        "en_keywords": ["inflation", "price", "cpi", "pce", "cost", "deflation"],
        "zh_keywords": ["通胀", "物价", "CPI", "消费价格", "通缩", "价格"],
        "description": "Inflation and price stability"
    },
    "employment": {
        "en_keywords": ["employment", "unemployment", "labor", "job", "workforce", "wage"],
        "zh_keywords": ["就业", "失业", "劳动力", "工作", "人力", "工资"],
        "description": "Employment and labor market"
    },
    "interest_rate": {
        "en_keywords": ["interest rate", "policy rate", "federal funds", "lending rate", "benchmark"],
        "zh_keywords": ["利率", "政策利率", "基准利率", "存贷款利率", "LPR"],
        "description": "Interest rates and monetary policy stance"
    },
    "gdp_growth": {
        "en_keywords": ["gdp", "growth", "economic activity", "output", "expansion", "contraction"],
        "zh_keywords": ["GDP", "增长", "经济活动", "产出", "扩张", "收缩"],
        "description": "Economic growth and GDP"
    },
    "credit": {
        "en_keywords": ["credit", "lending", "loan", "borrowing", "debt", "financing"],
        "zh_keywords": ["信贷", "贷款", "借贷", "融资", "债务", "社会融资"],
        "description": "Credit conditions and lending"
    },
    "liquidity": {
        "en_keywords": ["liquidity", "money supply", "monetary base", "reserve", "open market"],
        "zh_keywords": ["流动性", "货币供应", "基础货币", "准备金", "公开市场"],
        "description": "Liquidity and money supply"
    },
    "exchange_rate": {
        "en_keywords": ["exchange rate", "currency", "dollar", "forex", "appreciation", "depreciation"],
        "zh_keywords": ["汇率", "货币", "美元", "外汇", "升值", "贬值", "人民币"],
        "description": "Exchange rates and currency"
    },
    "financial_market": {
        "en_keywords": ["stock", "bond", "market", "yield", "treasury", "equity"],
        "zh_keywords": ["股票", "债券", "市场", "收益率", "国债", "股市"],
        "description": "Financial markets"
    }
}


@dataclass
class PolicyReport:
    """Represents a policy report document."""
    id: Optional[int] = None
    source: ReportSource = ReportSource.PBOC
    report_type: ReportType = ReportType.MONETARY_POLICY
    title: str = ""
    report_date: Optional[date] = None
    raw_text: str = ""
    parsed_markdown: str = ""
    file_path: Optional[str] = None
    language: str = "zh"  # Primary language of the report
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source.value,
            "report_type": self.report_type.value,
            "title": self.title,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "parsed_markdown": self.parsed_markdown[:500] + "..." if len(self.parsed_markdown) > 500 else self.parsed_markdown,
            "file_path": self.file_path,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class PolicyParagraph:
    """Represents a paragraph from a policy report."""
    id: Optional[int] = None
    report_id: int = 0
    paragraph_index: int = 0
    paragraph_text: str = ""
    topic: Optional[str] = None          # Detected topic (from POLICY_TOPICS)
    topic_confidence: float = 0.0
    section_title: Optional[str] = None  # Section this paragraph belongs to
    word_count: int = 0
    embedding: Optional[bytes] = None    # Serialized embedding vector
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.word_count and self.paragraph_text:
            # Rough word count (handles both Chinese and English)
            import re
            # Count Chinese characters
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', self.paragraph_text))
            # Count English words
            english_words = len(re.findall(r'[a-zA-Z]+', self.paragraph_text))
            self.word_count = chinese_chars + english_words
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "report_id": self.report_id,
            "paragraph_index": self.paragraph_index,
            "paragraph_text": self.paragraph_text,
            "topic": self.topic,
            "topic_confidence": self.topic_confidence,
            "section_title": self.section_title,
            "word_count": self.word_count
        }


@dataclass
class PolicyAlignment:
    """Represents an alignment between two paragraphs from different reports."""
    id: Optional[int] = None
    source_paragraph_id: int = 0         # Typically PBOC paragraph
    target_paragraph_id: int = 0         # Typically Fed paragraph
    similarity_score: float = 0.0
    alignment_method: AlignmentMethod = AlignmentMethod.SENTENCE_BERT
    topic: Optional[str] = None          # Shared topic
    term_id: Optional[int] = None        # Related terminology term (Layer 1 link)
    verified: bool = False               # Human verification flag
    created_at: Optional[datetime] = None
    
    # Populated when fetching with joins
    source_text: Optional[str] = None
    target_text: Optional[str] = None
    source_report_title: Optional[str] = None
    target_report_title: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_paragraph_id": self.source_paragraph_id,
            "target_paragraph_id": self.target_paragraph_id,
            "similarity_score": round(self.similarity_score, 4),
            "alignment_method": self.alignment_method.value,
            "topic": self.topic,
            "term_id": self.term_id,
            "verified": self.verified,
            "source_text": self.source_text,
            "target_text": self.target_text,
            "source_report_title": self.source_report_title,
            "target_report_title": self.target_report_title
        }


# Pydantic models for API requests/responses
try:
    from pydantic import BaseModel, Field
    
    class ReportUploadRequest(BaseModel):
        """Request model for uploading a policy report."""
        source: str = Field(..., description="Report source: pboc, fed")
        report_type: str = Field(default="monetary_policy", description="Report type")
        title: str = Field(..., description="Report title")
        report_date: Optional[str] = Field(None, description="Report date (YYYY-MM-DD)")
    
    class AlignmentRequest(BaseModel):
        """Request model for running alignment."""
        source_report_id: int = Field(..., description="Source report ID (e.g., PBOC)")
        target_report_id: int = Field(..., description="Target report ID (e.g., Fed)")
        threshold: float = Field(default=0.6, description="Minimum similarity threshold")
        method: str = Field(default="sentence_bert", description="Alignment method")
        topic_filter: Optional[str] = Field(None, description="Filter by topic")
    
    class AlignmentResponse(BaseModel):
        """Response model for alignment results."""
        total_alignments: int
        alignments: List[Dict[str, Any]]
        source_report: str
        target_report: str
        method: str
        threshold: float

except ImportError:
    # Pydantic not installed, skip API models
    pass

# SQL statements for creating Layer 2 tables
# Centralized in shared/schema.py (Issue #6 fix)
try:
    from shared.schema import LAYER2_SQL_SCHEMA
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from shared.schema import LAYER2_SQL_SCHEMA


def get_topic_by_keywords(text: str, language: str = "auto") -> tuple:
    """
    Detect topic from text using keyword matching.
    
    Args:
        text: Text to analyze
        language: Language code or "auto" to detect
        
    Returns:
        Tuple of (topic_key, confidence_score)
    """
    text_lower = text.lower()
    
    # Auto-detect language
    if language == "auto":
        import re
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        language = "zh" if chinese_chars > english_words else "en"
    
    keyword_key = "zh_keywords" if language == "zh" else "en_keywords"
    
    scores = {}
    for topic_key, topic_info in POLICY_TOPICS.items():
        keywords = topic_info.get(keyword_key, [])
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        if matches > 0:
            # Normalize by keyword count
            scores[topic_key] = matches / len(keywords)
    
    if not scores:
        return None, 0.0
    
    best_topic = max(scores, key=scores.get)
    return best_topic, min(scores[best_topic] * 2, 1.0)  # Scale confidence

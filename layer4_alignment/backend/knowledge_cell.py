"""
Knowledge Cell Data Model

The atomic unit of the aligned dataset. Each Knowledge Cell represents
one economic term with its multilingual definitions, policy evidence,
and sentiment evidence from news articles.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class TermDefinition(BaseModel):
    """Multilingual term definition from Layer 1 (Wikipedia)."""
    language: str = Field(..., description="ISO language code (e.g., 'en', 'zh')")
    term: str = Field(..., description="Term in this language")
    summary: str = Field(..., description="Definition/summary text")
    url: str = Field(..., description="Wikipedia URL")
    source: str = Field(default="Wikipedia", description="Data source")


class AlignmentScores(BaseModel):
    """Scores from different alignment methods."""
    llm: Optional[float] = Field(None, ge=0, le=1, description="LLM semantic score")
    vector: Optional[float] = Field(None, ge=0, le=1, description="Vector similarity score")
    rule: Optional[float] = Field(None, ge=0, le=1, description="Rule-based score")
    final: float = Field(..., ge=0, le=1, description="Weighted ensemble score")


class ReportMetadata(BaseModel):
    """Metadata for policy report."""
    title: str = Field(..., description="Report title")
    date: str = Field(..., description="Report date (YYYY-MM-DD)")
    section: Optional[str] = Field(None, description="Section within report")


class PolicyEvidence(BaseModel):
    """Aligned policy paragraph from Layer 2."""
    source: str = Field(..., description="Source institution ('pboc' or 'fed')")
    paragraph_id: int = Field(..., description="Database ID of paragraph")
    text: str = Field(..., description="Paragraph text content")
    topic: Optional[str] = Field(None, description="Detected topic")
    alignment_scores: AlignmentScores = Field(..., description="Scores from alignment methods")
    alignment_method: str = Field(default="hybrid_ensemble", description="Primary method used")
    report_metadata: ReportMetadata = Field(..., description="Source report info")


class SentimentInfo(BaseModel):
    """Sentiment annotation details."""
    label: str = Field(..., description="Sentiment label (bullish/bearish/neutral)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    annotator: str = Field(default="gemini-1.5-flash", description="Annotation source")


class SentimentEvidence(BaseModel):
    """Aligned news article from Layer 3."""
    article_id: int = Field(..., description="Database ID of article")
    title: str = Field(..., description="Article title")
    source: str = Field(..., description="News source (e.g., Bloomberg)")
    url: str = Field(..., description="Article URL")
    published_date: str = Field(..., description="Publication date (YYYY-MM-DD)")
    sentiment: SentimentInfo = Field(..., description="Sentiment annotation")
    alignment_scores: AlignmentScores = Field(..., description="Scores from alignment methods")


class QualityMetrics(BaseModel):
    """Quality metrics for a Knowledge Cell."""
    overall_score: float = Field(..., ge=0, le=1, description="Weighted average of all scores")
    language_coverage: int = Field(..., ge=0, description="Number of languages with definitions")
    policy_evidence_count: int = Field(..., ge=0, description="Number of aligned policy paragraphs")
    sentiment_evidence_count: int = Field(..., ge=0, description="Number of aligned news articles")
    avg_policy_score: float = Field(default=0.0, ge=0, le=1, description="Average policy alignment score")
    avg_sentiment_score: float = Field(default=0.0, ge=0, le=1, description="Average sentiment alignment score")


class CellMetadata(BaseModel):
    """Metadata for Knowledge Cell generation."""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    alignment_engine_version: str = Field(default="4.0.0")
    quality_metrics: QualityMetrics = Field(..., description="Quality assessment")


class KnowledgeCell(BaseModel):
    """
    The atomic unit of the aligned dataset.
    
    Each Knowledge Cell contains:
    - Multilingual definitions from Layer 1
    - Policy evidence from Layer 2 (PBOC/Fed)
    - Sentiment evidence from Layer 3 (News)
    - Quality metrics and metadata
    """
    concept_id: str = Field(..., description="Wikidata QID or TERM_<id>")
    primary_term: str = Field(..., description="English canonical term")
    
    # Layer 1: Multilingual definitions
    definitions: Dict[str, TermDefinition] = Field(
        default_factory=dict, 
        description="Definitions by language code"
    )
    
    # Layer 2: Policy evidence
    policy_evidence: List[PolicyEvidence] = Field(
        default_factory=list,
        description="Aligned policy paragraphs"
    )
    
    # Layer 3: Sentiment evidence
    sentiment_evidence: List[SentimentEvidence] = Field(
        default_factory=list,
        description="Aligned news articles"
    )
    
    # Metadata
    metadata: CellMetadata = Field(..., description="Generation metadata")
    
    def to_jsonl_line(self) -> str:
        """Serialize to a single JSONL line."""
        import json
        return json.dumps(self.model_dump(), ensure_ascii=False)
    
    @classmethod
    def from_jsonl_line(cls, line: str) -> "KnowledgeCell":
        """Deserialize from a JSONL line."""
        import json
        data = json.loads(line)
        return cls(**data)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a brief summary of the cell for logging."""
        return {
            "concept_id": self.concept_id,
            "primary_term": self.primary_term,
            "languages": list(self.definitions.keys()),
            "policy_count": len(self.policy_evidence),
            "sentiment_count": len(self.sentiment_evidence),
            "quality_score": self.metadata.quality_metrics.overall_score
        }


def create_empty_cell(term_id: int, term: str) -> KnowledgeCell:
    """Create an empty Knowledge Cell for a term."""
    return KnowledgeCell(
        concept_id=f"TERM_{term_id}",
        primary_term=term,
        definitions={},
        policy_evidence=[],
        sentiment_evidence=[],
        metadata=CellMetadata(
            quality_metrics=QualityMetrics(
                overall_score=0.0,
                language_coverage=0,
                policy_evidence_count=0,
                sentiment_evidence_count=0
            )
        )
    )

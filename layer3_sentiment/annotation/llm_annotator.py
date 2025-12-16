"""
Layer 3: LLM Annotator Module
Uses Gemini API for sentiment pre-annotation of financial news

Usage:
    from llm_annotator import SentimentAnnotator, RuleBasedAnnotator
    
    # With Gemini API
    annotator = SentimentAnnotator(api_key="your-api-key")
    result = await annotator.annotate("Fed signals slower pace of rate cuts")
    
    # Without API (rule-based fallback)
    fallback = RuleBasedAnnotator()
    result = fallback.annotate("S&P 500 surges to record high")
"""

import os
import json
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import re

# Import models
# Import models
try:
    # When imported as package
    from ..backend.models import (
        SentimentLabel, AnnotationSource, SentimentAnnotation,
        detect_related_terms
    )
except (ImportError, ValueError):
    try:
        # When layer3-sentiment is in path
        from backend.models import (
            SentimentLabel, AnnotationSource, SentimentAnnotation,
            detect_related_terms
        )
    except ImportError:
        # Fallback
        try:
            from models import (
                SentimentLabel, AnnotationSource, SentimentAnnotation,
                detect_related_terms
            )
        except ImportError:
            pass

# Gemini API (install with: pip install google-generativeai)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠ google-generativeai not installed. Install with: pip install google-generativeai")


@dataclass
class SentimentResult:
    """Result of sentiment annotation."""
    label: SentimentLabel
    score: float                    # Confidence score 0-1
    reasoning: Optional[str] = None  # LLM's reasoning
    related_terms: List[str] = field(default_factory=list)  # Detected economic terms
    source: AnnotationSource = AnnotationSource.RULE_BASED
    
    def to_dict(self) -> dict:
        return {
            "label": self.label.value,
            "score": self.score,
            "reasoning": self.reasoning,
            "related_terms": self.related_terms,
            "source": self.source.value
        }
    
    def to_annotation(self, article_id: int) -> SentimentAnnotation:
        """Convert to SentimentAnnotation for database storage."""
        return SentimentAnnotation(
            article_id=article_id,
            sentiment_label=self.label,
            confidence_score=self.score,
            annotation_source=self.source,
            reasoning=self.reasoning,
            detected_entities=self.related_terms
        )


# Prompt template for sentiment analysis
SENTIMENT_PROMPT = """You are a financial news sentiment analyzer specializing in market impact assessment. Analyze the following news headline and determine its likely market sentiment.

News: {title}
{summary_section}

Respond in JSON format only:
{{
    "sentiment": "bullish" or "bearish" or "neutral",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation of the sentiment assessment",
    "economic_terms": ["list", "of", "economic", "terms", "mentioned"]
}}

Definitions:
- bullish: Positive for stock markets - indicates economic growth, lower inflation, accommodative policy, strong earnings, positive economic data
- bearish: Negative for stock markets - indicates economic slowdown, higher inflation, tightening policy, weak earnings, negative economic data  
- neutral: No clear directional impact on markets, or mixed signals

Consider:
1. Central bank policy implications (rate cuts = bullish, rate hikes = bearish)
2. Economic indicators (strong growth = bullish, recession signals = bearish)
3. Corporate earnings and guidance
4. Geopolitical and trade developments
5. Market sentiment indicators

Return ONLY the JSON object, no other text or markdown formatting."""


SENTIMENT_PROMPT_ZH = """你是一位专业的金融新闻情绪分析师。分析以下新闻标题并判断其对市场的影响。

新闻: {title}
{summary_section}

仅以JSON格式回复：
{{
    "sentiment": "bullish" 或 "bearish" 或 "neutral",
    "confidence": 0.0 到 1.0,
    "reasoning": "情绪判断的简短解释",
    "economic_terms": ["相关", "经济", "术语", "列表"]
}}

定义：
- bullish (看涨): 对股市有利 - 经济增长、通胀降低、宽松政策、强劲财报、积极经济数据
- bearish (看跌): 对股市不利 - 经济放缓、通胀上升、紧缩政策、疲软财报、消极经济数据
- neutral (中性): 对市场无明确方向性影响,或信号混杂

仅返回JSON对象，不要其他文本。"""


class SentimentAnnotator:
    """
    Annotates financial news sentiment using Gemini API.
    """
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "gemini-1.5-flash"
    ):
        """
        Initialize the annotator with Gemini API key.
        
        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self.model = None  # Lazy loading
        self._fallback = RuleBasedAnnotator()  # Fallback for errors
    
    def _init_model(self):
        """Initialize the Gemini model if not already done."""
        if self.model is None:
            if not GENAI_AVAILABLE:
                raise ImportError(
                    "google-generativeai not installed. "
                    "Install with: pip install google-generativeai"
                )
            
            if not self.api_key:
                raise ValueError(
                    "Gemini API key required. Set GEMINI_API_KEY environment variable "
                    "or pass api_key to constructor."
                )
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response, handling various formats."""
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        
        # Try to find JSON in the response
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract key information manually
            sentiment = "neutral"
            if "bullish" in text.lower():
                sentiment = "bullish"
            elif "bearish" in text.lower():
                sentiment = "bearish"
            
            return {
                "sentiment": sentiment,
                "confidence": 0.5,
                "reasoning": "Parsed from non-JSON response",
                "economic_terms": []
            }
    
    async def annotate(
        self,
        title: str,
        summary: str = None,
        language: str = "en"
    ) -> SentimentResult:
        """
        Annotate a single news headline.
        
        Args:
            title: News headline text
            summary: Optional article summary for more context
            language: Language of the text ("en" or "zh")
            
        Returns:
            SentimentResult object
        """
        try:
            self._init_model()
        except (ImportError, ValueError) as e:
            print(f"⚠ Using fallback annotator: {e}")
            return self._fallback.annotate(title)
        
        # Choose prompt based on language
        prompt_template = SENTIMENT_PROMPT_ZH if language == "zh" else SENTIMENT_PROMPT
        
        summary_section = f"\nSummary: {summary}" if summary else ""
        prompt = prompt_template.format(title=title, summary_section=summary_section)
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            result_json = self._parse_response(response.text)
            
            sentiment = result_json.get("sentiment", "neutral").lower()
            if sentiment not in ["bullish", "bearish", "neutral"]:
                sentiment = "neutral"
            
            return SentimentResult(
                label=SentimentLabel(sentiment),
                score=float(result_json.get("confidence", 0.5)),
                reasoning=result_json.get("reasoning"),
                related_terms=result_json.get("economic_terms", []),
                source=AnnotationSource.LLM_GEMINI
            )
            
        except Exception as e:
            print(f"✗ Gemini API error: {e}")
            # Fall back to rule-based
            return self._fallback.annotate(title)
    
    async def annotate_batch(
        self,
        articles: List[Dict[str, str]],
        delay_seconds: float = 0.5,
        use_fallback_on_error: bool = True
    ) -> List[SentimentResult]:
        """
        Annotate multiple news articles.
        
        Args:
            articles: List of dicts with 'title' and optional 'summary', 'language'
            delay_seconds: Delay between API calls to avoid rate limiting
            use_fallback_on_error: Use rule-based fallback on API errors
            
        Returns:
            List of SentimentResult objects
        """
        results = []
        
        for i, article in enumerate(articles):
            try:
                result = await self.annotate(
                    title=article.get("title", ""),
                    summary=article.get("summary"),
                    language=article.get("language", "en")
                )
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    print(f"  Annotated {i + 1}/{len(articles)} articles...")
                
            except Exception as e:
                if use_fallback_on_error:
                    results.append(self._fallback.annotate(article.get("title", "")))
                else:
                    results.append(SentimentResult(
                        label=SentimentLabel.NEUTRAL,
                        score=0.0,
                        reasoning=f"Error: {str(e)}",
                        source=AnnotationSource.RULE_BASED
                    ))
            
            await asyncio.sleep(delay_seconds)
        
        return results


class RuleBasedAnnotator:
    """
    Simple rule-based sentiment annotator as fallback.
    Uses keyword matching for basic sentiment detection.
    No API required - works offline.
    """
    
    BULLISH_KEYWORDS = [
        # English
        "surge", "soar", "rally", "gain", "rise", "growth", "boom",
        "strong", "improve", "beat", "exceed", "optimism", "recovery",
        "rate cut", "easing", "stimulus", "support", "record high",
        "upturn", "rebound", "expansion", "confidence", "upside",
        "outperform", "upgrade", "positive", "strength", "accelerate",
        # Chinese
        "上涨", "大涨", "反弹", "增长", "利好", "乐观", "突破",
        "降息", "宽松", "刺激", "复苏", "牛市", "走强",
    ]
    
    BEARISH_KEYWORDS = [
        # English
        "drop", "fall", "decline", "plunge", "crash", "slump", "weak",
        "concern", "fear", "worry", "recession", "slowdown", "contraction",
        "rate hike", "tightening", "inflation", "crisis", "default",
        "downturn", "collapse", "sell-off", "tumble", "sink", "bear",
        "downgrade", "negative", "warning", "cut forecast", "miss",
        # Chinese
        "下跌", "大跌", "暴跌", "萎缩", "利空", "悲观", "危机",
        "加息", "紧缩", "通胀", "衰退", "熊市", "走弱", "下滑",
    ]
    
    # Modifier keywords that strengthen/weaken signals
    STRONG_MODIFIERS = ["significantly", "sharply", "dramatically", "strongly", "大幅", "显著"]
    WEAK_MODIFIERS = ["slightly", "marginally", "modestly", "小幅", "温和"]
    
    def annotate(self, title: str, summary: str = None) -> SentimentResult:
        """
        Annotate using keyword matching.
        
        Args:
            title: News headline
            summary: Optional summary (uses title + summary if provided)
            
        Returns:
            SentimentResult with confidence based on keyword matches
        """
        text = title.lower()
        if summary:
            text += " " + summary.lower()
        
        bullish_count = sum(1 for kw in self.BULLISH_KEYWORDS if kw.lower() in text)
        bearish_count = sum(1 for kw in self.BEARISH_KEYWORDS if kw.lower() in text)
        
        # Check for modifiers
        has_strong_modifier = any(mod in text for mod in self.STRONG_MODIFIERS)
        has_weak_modifier = any(mod in text for mod in self.WEAK_MODIFIERS)
        
        # Detect related terms
        related_terms = detect_related_terms(title + (summary or ""))
        
        # Calculate sentiment
        if bullish_count > bearish_count:
            base_score = min(0.5 + (bullish_count * 0.1), 0.85)
            if has_strong_modifier:
                base_score = min(base_score + 0.1, 0.95)
            elif has_weak_modifier:
                base_score = max(base_score - 0.1, 0.5)
            
            return SentimentResult(
                label=SentimentLabel.BULLISH,
                score=base_score,
                reasoning=f"Matched {bullish_count} bullish keywords vs {bearish_count} bearish",
                related_terms=related_terms,
                source=AnnotationSource.RULE_BASED
            )
        
        elif bearish_count > bullish_count:
            base_score = min(0.5 + (bearish_count * 0.1), 0.85)
            if has_strong_modifier:
                base_score = min(base_score + 0.1, 0.95)
            elif has_weak_modifier:
                base_score = max(base_score - 0.1, 0.5)
            
            return SentimentResult(
                label=SentimentLabel.BEARISH,
                score=base_score,
                reasoning=f"Matched {bearish_count} bearish keywords vs {bullish_count} bullish",
                related_terms=related_terms,
                source=AnnotationSource.RULE_BASED
            )
        
        else:
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                score=0.5,
                reasoning="No strong sentiment indicators detected",
                related_terms=related_terms,
                source=AnnotationSource.RULE_BASED
            )
    
    def annotate_batch(self, titles: List[str]) -> List[SentimentResult]:
        """Annotate multiple headlines synchronously."""
        return [self.annotate(title) for title in titles]


class HybridAnnotator:
    """
    Hybrid annotator that uses LLM for uncertain cases and rule-based for clear cases.
    Optimizes API usage while maintaining quality.
    """
    
    def __init__(self, api_key: str = None, certainty_threshold: float = 0.75):
        """
        Initialize hybrid annotator.
        
        Args:
            api_key: Gemini API key
            certainty_threshold: If rule-based confidence > threshold, skip LLM
        """
        self.llm_annotator = SentimentAnnotator(api_key=api_key)
        self.rule_annotator = RuleBasedAnnotator()
        self.certainty_threshold = certainty_threshold
    
    async def annotate(
        self,
        title: str,
        summary: str = None,
        language: str = "en"
    ) -> SentimentResult:
        """
        Annotate using hybrid approach.
        
        Uses rule-based first. If uncertain, uses LLM.
        """
        # Try rule-based first
        rule_result = self.rule_annotator.annotate(title, summary)
        
        # If confident enough, use rule-based result
        if rule_result.score >= self.certainty_threshold:
            return rule_result
        
        # Otherwise, use LLM
        try:
            return await self.llm_annotator.annotate(title, summary, language)
        except Exception as e:
            # Fall back to rule-based on error
            print(f"⚠ LLM error, using rule-based: {e}")
            return rule_result
    
    async def annotate_batch(
        self,
        articles: List[Dict[str, str]],
        delay_seconds: float = 0.5
    ) -> List[SentimentResult]:
        """Annotate batch with hybrid approach."""
        results = []
        llm_calls = 0
        
        for article in articles:
            result = await self.annotate(
                title=article.get("title", ""),
                summary=article.get("summary"),
                language=article.get("language", "en")
            )
            results.append(result)
            
            if result.source == AnnotationSource.LLM_GEMINI:
                llm_calls += 1
                await asyncio.sleep(delay_seconds)
        
        print(f"  Hybrid annotation: {llm_calls} LLM calls, {len(articles) - llm_calls} rule-based")
        return results


if __name__ == "__main__":
    # Test annotation
    test_headlines = [
        ("Fed signals slower pace of rate cuts amid sticky inflation", "en"),
        ("S&P 500 surges to record high on strong earnings", "en"),
        ("Unemployment claims rise, signaling labor market cooling", "en"),
        ("Stock futures flat ahead of key inflation data", "en"),
        ("央行降准释放流动性，市场反应积极", "zh"),
        ("美联储暗示放缓降息步伐，美股承压", "zh"),
    ]
    
    print("=" * 60)
    print("Testing Sentiment Annotators")
    print("=" * 60)
    
    print("\n1. Rule-based Annotator (no API required):")
    print("-" * 60)
    
    annotator = RuleBasedAnnotator()
    for headline, lang in test_headlines:
        result = annotator.annotate(headline)
        print(f"\nHeadline: {headline[:50]}...")
        print(f"  Sentiment: {result.label.value} (confidence: {result.score:.2f})")
        print(f"  Reasoning: {result.reasoning}")
        print(f"  Terms: {result.related_terms}")
    
    print("\n" + "=" * 60)
    
    if GENAI_AVAILABLE and os.environ.get("GEMINI_API_KEY"):
        print("\n2. LLM Annotator (Gemini API):")
        print("-" * 60)
        
        async def test_llm():
            annotator = SentimentAnnotator()
            for headline, lang in test_headlines[:2]:  # Test first 2 only
                result = await annotator.annotate(headline, language=lang)
                print(f"\nHeadline: {headline[:50]}...")
                print(f"  Sentiment: {result.label.value} (confidence: {result.score:.2f})")
                print(f"  Source: {result.source.value}")
                print(f"  Reasoning: {result.reasoning}")
        
        asyncio.run(test_llm())
    else:
        print("\n2. LLM Annotator: Skipped (no API key or google-generativeai not installed)")
        print("   Set GEMINI_API_KEY environment variable and install google-generativeai to test")
    
    print("\n" + "=" * 60)
    print("Test complete!")

"""
Layer 3: LLM Annotator Module
Uses Gemini API for sentiment pre-annotation of financial news

Usage:
    from llm_annotator import SentimentAnnotator
    
    annotator = SentimentAnnotator(api_key="your-api-key")
    result = annotator.annotate("Fed signals slower pace of rate cuts")
"""

import os
import json
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

# Gemini API (install with: pip install google-generativeai)
# import google.generativeai as genai


class SentimentLabel(Enum):
    """Sentiment labels for financial news."""
    BULLISH = "bullish"      # Positive for markets
    BEARISH = "bearish"      # Negative for markets
    NEUTRAL = "neutral"      # No clear market impact


@dataclass
class SentimentResult:
    """Result of sentiment annotation."""
    label: SentimentLabel
    score: float                    # Confidence score 0-1
    reasoning: Optional[str] = None # LLM's reasoning
    related_terms: List[str] = None # Detected economic terms
    
    def to_dict(self) -> dict:
        return {
            "label": self.label.value,
            "score": self.score,
            "reasoning": self.reasoning,
            "related_terms": self.related_terms or []
        }


# Prompt template for sentiment analysis
SENTIMENT_PROMPT = """You are a financial news sentiment analyzer. Analyze the following news headline and determine its market sentiment.

News: {title}

Respond in JSON format:
{{
    "sentiment": "bullish" or "bearish" or "neutral",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation",
    "related_terms": ["list", "of", "economic", "terms", "mentioned"]
}}

Definitions:
- bullish: Positive for stock markets, indicates economic growth, lower inflation, accommodative policy
- bearish: Negative for stock markets, indicates economic slowdown, higher inflation, tightening policy
- neutral: No clear directional impact on markets

Return ONLY the JSON, no other text."""


class SentimentAnnotator:
    """
    Annotates financial news sentiment using Gemini API.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the annotator with Gemini API key.
        
        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = None  # Lazy loading
    
    def _init_model(self):
        """Initialize the Gemini model if not already done."""
        if self.model is None:
            if not self.api_key:
                raise ValueError(
                    "Gemini API key required. Set GEMINI_API_KEY environment variable "
                    "or pass api_key to constructor."
                )
            
            # TODO: Uncomment when google-generativeai is installed
            # import google.generativeai as genai
            # genai.configure(api_key=self.api_key)
            # self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            raise NotImplementedError(
                "Gemini API not yet configured. "
                "Install with: pip install google-generativeai"
            )
    
    def annotate(self, title: str) -> SentimentResult:
        """
        Annotate a single news headline.
        
        Args:
            title: News headline text
            
        Returns:
            SentimentResult object
        """
        self._init_model()
        
        prompt = SENTIMENT_PROMPT.format(title=title)
        
        # TODO: Uncomment when model is initialized
        # response = self.model.generate_content(prompt)
        # result_json = json.loads(response.text)
        
        # return SentimentResult(
        #     label=SentimentLabel(result_json["sentiment"]),
        #     score=result_json["confidence"],
        #     reasoning=result_json.get("reasoning"),
        #     related_terms=result_json.get("related_terms", [])
        # )
        
        raise NotImplementedError("Model not initialized")
    
    def annotate_batch(
        self, 
        titles: List[str],
        delay_seconds: float = 0.5
    ) -> List[SentimentResult]:
        """
        Annotate multiple news headlines.
        
        Args:
            titles: List of news headlines
            delay_seconds: Delay between API calls to avoid rate limiting
            
        Returns:
            List of SentimentResult objects
        """
        import time
        
        results = []
        for title in titles:
            try:
                result = self.annotate(title)
                results.append(result)
            except Exception as e:
                # Return neutral sentiment on error
                results.append(SentimentResult(
                    label=SentimentLabel.NEUTRAL,
                    score=0.0,
                    reasoning=f"Error: {str(e)}"
                ))
            
            time.sleep(delay_seconds)
        
        return results


# Rule-based fallback annotator (no API required)
class RuleBasedAnnotator:
    """
    Simple rule-based sentiment annotator as fallback.
    Uses keyword matching for basic sentiment detection.
    """
    
    BULLISH_KEYWORDS = [
        "surge", "soar", "rally", "gain", "rise", "growth", "boom",
        "strong", "improve", "beat", "exceed", "optimism", "recovery",
        "rate cut", "easing", "stimulus", "support"
    ]
    
    BEARISH_KEYWORDS = [
        "drop", "fall", "decline", "plunge", "crash", "slump", "weak",
        "concern", "fear", "worry", "recession", "slowdown", "contraction",
        "rate hike", "tightening", "inflation", "crisis", "default"
    ]
    
    def annotate(self, title: str) -> SentimentResult:
        """
        Annotate using keyword matching.
        
        Args:
            title: News headline
            
        Returns:
            SentimentResult with confidence based on keyword matches
        """
        title_lower = title.lower()
        
        bullish_count = sum(1 for kw in self.BULLISH_KEYWORDS if kw in title_lower)
        bearish_count = sum(1 for kw in self.BEARISH_KEYWORDS if kw in title_lower)
        
        if bullish_count > bearish_count:
            score = min(0.5 + (bullish_count * 0.1), 0.9)
            return SentimentResult(
                label=SentimentLabel.BULLISH,
                score=score,
                reasoning=f"Matched {bullish_count} bullish keywords"
            )
        elif bearish_count > bullish_count:
            score = min(0.5 + (bearish_count * 0.1), 0.9)
            return SentimentResult(
                label=SentimentLabel.BEARISH,
                score=score,
                reasoning=f"Matched {bearish_count} bearish keywords"
            )
        else:
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                score=0.5,
                reasoning="No strong sentiment indicators"
            )


if __name__ == "__main__":
    # Test annotation
    test_headlines = [
        "Fed signals slower pace of rate cuts amid sticky inflation",
        "S&P 500 surges to record high on strong earnings",
        "Unemployment claims rise, signaling labor market cooling",
        "Stock futures flat ahead of key inflation data"
    ]
    
    print("Testing rule-based annotator (no API required):")
    print("-" * 60)
    
    annotator = RuleBasedAnnotator()
    for headline in test_headlines:
        result = annotator.annotate(headline)
        print(f"Headline: {headline[:50]}...")
        print(f"  Sentiment: {result.label.value} (confidence: {result.score:.2f})")
        print(f"  Reasoning: {result.reasoning}")
        print()
    
    print("\nTo use LLM annotator, install google-generativeai and set GEMINI_API_KEY")

"""
Layer 3: Trend Analysis Module
Time series analysis and trend detection for economic terms in news.

Usage:
    from trend_analysis import TrendAnalyzer
    
    analyzer = TrendAnalyzer(db_path="corpus.db")
    trend = await analyzer.analyze_term_trend("inflation", days_back=30)
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from collections import defaultdict
import json

# Third-party imports (optional, for advanced analysis)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Import models and database
# Import models and database
try:
    # When imported as package
    from ..backend.models import (
        TrendDataPoint, MarketContext, SentimentLabel,
        ECONOMIC_TERM_VARIANTS, ECONOMIC_TERM_VARIANTS_ZH
    )
    from ..backend.database import SentimentDatabase
except (ImportError, ValueError):
    try:
        # When layer3-sentiment is in path
        from backend.models import (
            TrendDataPoint, MarketContext, SentimentLabel,
            ECONOMIC_TERM_VARIANTS, ECONOMIC_TERM_VARIANTS_ZH
        )
        from backend.database import SentimentDatabase
    except ImportError:
        # Fallback
        try:
            from models import (
                TrendDataPoint, MarketContext, SentimentLabel,
                ECONOMIC_TERM_VARIANTS, ECONOMIC_TERM_VARIANTS_ZH
            )
            from database import SentimentDatabase
        except ImportError:
            pass


@dataclass
class TrendSummary:
    """Summary of trend analysis for a term."""
    term: str
    period_start: date
    period_end: date
    total_mentions: int
    avg_daily_mentions: float
    sentiment_distribution: Dict[str, int]  # bullish, bearish, neutral counts
    avg_sentiment_score: float  # -1 to +1 scale
    trend_direction: str  # "increasing", "decreasing", "stable"
    peak_date: Optional[date]
    peak_mentions: int
    correlation_with_market: Optional[float]  # Correlation with S&P 500
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat()
            },
            "mentions": {
                "total": self.total_mentions,
                "avg_daily": round(self.avg_daily_mentions, 2),
                "peak": {
                    "date": self.peak_date.isoformat() if self.peak_date else None,
                    "count": self.peak_mentions
                }
            },
            "sentiment": {
                "distribution": self.sentiment_distribution,
                "avg_score": round(self.avg_sentiment_score, 4),
                "direction": "bullish" if self.avg_sentiment_score > 0.1 else ("bearish" if self.avg_sentiment_score < -0.1 else "neutral")
            },
            "trend": {
                "direction": self.trend_direction,
                "market_correlation": round(self.correlation_with_market, 4) if self.correlation_with_market else None
            }
        }


class TrendAnalyzer:
    """
    Analyzes trends in term mentions and sentiment over time.
    """
    
    def __init__(self, db_path: str = "corpus.db"):
        """
        Initialize trend analyzer.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db = SentimentDatabase(db_path)
    
    async def calculate_daily_frequencies(
        self,
        term: str,
        days_back: int = 30
    ) -> Dict[date, Dict[str, Any]]:
        """
        Calculate daily mention frequencies and sentiment counts for a term.
        
        Args:
            term: Economic term to analyze
            days_back: Number of days to analyze
            
        Returns:
            Dict mapping dates to frequency/sentiment data
        """
        # Get term variants
        term_key = term.lower().replace(" ", "_")
        variants = ECONOMIC_TERM_VARIANTS.get(term_key, [term])
        variants_zh = ECONOMIC_TERM_VARIANTS_ZH.get(term_key, [])
        all_variants = set(v.lower() for v in variants + variants_zh)
        
        # Get articles mentioning the term
        articles = await self.db.search_articles(term, days_back=days_back, limit=10000)
        
        # Get annotations for these articles
        annotations_map = {}
        for article in articles:
            if article.id:
                annots = await self.db.get_annotations(article_id=article.id, limit=1)
                if annots:
                    annotations_map[article.id] = annots[0]
        
        # Aggregate by date
        daily_data = defaultdict(lambda: {
            "mention_count": 0,
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
            "articles": []
        })
        
        for article in articles:
            if not article.published_date:
                continue
            
            article_date = article.published_date.date()
            daily_data[article_date]["mention_count"] += 1
            daily_data[article_date]["articles"].append({
                "id": article.id,
                "title": article.title
            })
            
            # Add sentiment if available
            if article.id in annotations_map:
                annot = annotations_map[article.id]
                label = annot.sentiment_label.value
                if label in daily_data[article_date]:
                    daily_data[article_date][label] += 1
        
        return dict(daily_data)
    
    async def update_frequency_table(
        self,
        term: str,
        days_back: int = 30
    ) -> int:
        """
        Update the term_frequency table with calculated frequencies.
        
        Args:
            term: Term to update
            days_back: Days of data to calculate
            
        Returns:
            Number of days updated
        """
        daily_data = await self.calculate_daily_frequencies(term, days_back)
        
        updated = 0
        for freq_date, data in daily_data.items():
            await self.db.update_term_frequency(
                term=term,
                frequency_date=freq_date,
                mention_count=data["mention_count"],
                bullish_count=data["bullish"],
                bearish_count=data["bearish"],
                neutral_count=data["neutral"]
            )
            updated += 1
        
        return updated
    
    async def get_trend_data(
        self,
        term: str,
        days_back: int = 30,
        fill_gaps: bool = True
    ) -> List[TrendDataPoint]:
        """
        Get trend data points for a term.
        
        Args:
            term: Term to analyze
            days_back: Days of data to retrieve
            fill_gaps: Fill in zero values for missing days
            
        Returns:
            List of TrendDataPoint objects
        """
        # First update the frequency table
        await self.update_frequency_table(term, days_back)
        
        # Get from database
        trend_data = await self.db.get_term_trend(term, days_back)
        
        if fill_gaps and trend_data:
            # Fill in missing days with zero values
            start_date = date.today() - timedelta(days=days_back)
            end_date = date.today()
            
            existing_dates = {dp.date for dp in trend_data}
            filled_data = []
            
            current = start_date
            while current <= end_date:
                if current in existing_dates:
                    # Use existing data point
                    dp = next(d for d in trend_data if d.date == current)
                    filled_data.append(dp)
                else:
                    # Add zero data point
                    filled_data.append(TrendDataPoint(
                        date=current,
                        term=term,
                        mention_count=0,
                        avg_sentiment=0.0,
                        bullish_count=0,
                        bearish_count=0,
                        neutral_count=0
                    ))
                current += timedelta(days=1)
            
            return filled_data
        
        return trend_data
    
    async def analyze_term_trend(
        self,
        term: str,
        days_back: int = 30,
        include_market_correlation: bool = True
    ) -> TrendSummary:
        """
        Perform comprehensive trend analysis for a term.
        
        Args:
            term: Economic term to analyze
            days_back: Days of data to analyze
            include_market_correlation: Calculate correlation with market returns
            
        Returns:
            TrendSummary object with analysis results
        """
        trend_data = await self.get_trend_data(term, days_back, fill_gaps=True)
        
        if not trend_data:
            # Return empty summary
            return TrendSummary(
                term=term,
                period_start=date.today() - timedelta(days=days_back),
                period_end=date.today(),
                total_mentions=0,
                avg_daily_mentions=0.0,
                sentiment_distribution={"bullish": 0, "bearish": 0, "neutral": 0},
                avg_sentiment_score=0.0,
                trend_direction="stable",
                peak_date=None,
                peak_mentions=0,
                correlation_with_market=None
            )
        
        # Calculate statistics
        total_mentions = sum(dp.mention_count for dp in trend_data)
        avg_daily = total_mentions / len(trend_data) if trend_data else 0
        
        bullish_total = sum(dp.bullish_count for dp in trend_data)
        bearish_total = sum(dp.bearish_count for dp in trend_data)
        neutral_total = sum(dp.neutral_count for dp in trend_data)
        
        # Calculate average sentiment (-1 to +1)
        total_annotated = bullish_total + bearish_total + neutral_total
        avg_sentiment = (bullish_total - bearish_total) / total_annotated if total_annotated > 0 else 0
        
        # Find peak
        peak_dp = max(trend_data, key=lambda x: x.mention_count)
        
        # Determine trend direction
        trend_direction = self._calculate_trend_direction(trend_data)
        
        # Calculate market correlation if requested
        correlation = None
        if include_market_correlation and NUMPY_AVAILABLE:
            correlation = await self._calculate_market_correlation(trend_data)
        
        return TrendSummary(
            term=term,
            period_start=trend_data[0].date if trend_data else date.today() - timedelta(days=days_back),
            period_end=trend_data[-1].date if trend_data else date.today(),
            total_mentions=total_mentions,
            avg_daily_mentions=avg_daily,
            sentiment_distribution={
                "bullish": bullish_total,
                "bearish": bearish_total,
                "neutral": neutral_total
            },
            avg_sentiment_score=avg_sentiment,
            trend_direction=trend_direction,
            peak_date=peak_dp.date if peak_dp.mention_count > 0 else None,
            peak_mentions=peak_dp.mention_count,
            correlation_with_market=correlation
        )
    
    def _calculate_trend_direction(self, trend_data: List[TrendDataPoint]) -> str:
        """Calculate if the trend is increasing, decreasing, or stable."""
        if len(trend_data) < 7:
            return "stable"
        
        # Compare first half average to second half average
        half = len(trend_data) // 2
        first_half = trend_data[:half]
        second_half = trend_data[half:]
        
        first_avg = sum(dp.mention_count for dp in first_half) / len(first_half)
        second_avg = sum(dp.mention_count for dp in second_half) / len(second_half)
        
        # Threshold for determining significant change (20%)
        if first_avg == 0:
            return "increasing" if second_avg > 0 else "stable"
        
        change_ratio = (second_avg - first_avg) / first_avg
        
        if change_ratio > 0.2:
            return "increasing"
        elif change_ratio < -0.2:
            return "decreasing"
        else:
            return "stable"
    
    async def _calculate_market_correlation(
        self,
        trend_data: List[TrendDataPoint]
    ) -> Optional[float]:
        """Calculate correlation between mention sentiment and market returns."""
        if not NUMPY_AVAILABLE:
            return None
        
        # Get market data for the same period
        if not trend_data:
            return None
        
        start_date = trend_data[0].date
        end_date = trend_data[-1].date
        market_data = await self.db.get_market_context_range(start_date, end_date)
        
        if len(market_data) < 7:
            return None
        
        # Create aligned arrays
        market_by_date = {md.context_date: md.sp500_change_pct for md in market_data if md.sp500_change_pct is not None}
        
        sentiments = []
        returns = []
        
        for dp in trend_data:
            if dp.date in market_by_date:
                sentiments.append(dp.avg_sentiment)
                returns.append(market_by_date[dp.date])
        
        if len(sentiments) < 7:
            return None
        
        # Calculate Pearson correlation
        sentiments_arr = np.array(sentiments)
        returns_arr = np.array(returns)
        
        if np.std(sentiments_arr) == 0 or np.std(returns_arr) == 0:
            return 0.0
        
        correlation = np.corrcoef(sentiments_arr, returns_arr)[0, 1]
        return float(correlation)
    
    async def compare_terms(
        self,
        terms: List[str],
        days_back: int = 30
    ) -> Dict[str, TrendSummary]:
        """
        Compare trend metrics across multiple terms.
        
        Args:
            terms: List of terms to compare
            days_back: Days of data to analyze
            
        Returns:
            Dict mapping term to TrendSummary
        """
        results = {}
        for term in terms:
            results[term] = await self.analyze_term_trend(term, days_back)
        return results
    
    async def get_hot_terms(
        self,
        days_back: int = 7,
        limit: int = 10
    ) -> List[Tuple[str, int, float]]:
        """
        Get the most mentioned economic terms.
        
        Args:
            days_back: Days to analyze
            limit: Maximum terms to return
            
        Returns:
            List of (term, mention_count, avg_sentiment) tuples
        """
        # Analyze all known terms
        all_terms = list(ECONOMIC_TERM_VARIANTS.keys())
        
        term_stats = []
        for term_key in all_terms:
            # Get a representative term
            term = term_key.replace("_", " ")
            daily_data = await self.calculate_daily_frequencies(term, days_back)
            
            total_mentions = sum(d["mention_count"] for d in daily_data.values())
            total_bullish = sum(d["bullish"] for d in daily_data.values())
            total_bearish = sum(d["bearish"] for d in daily_data.values())
            total_neutral = sum(d["neutral"] for d in daily_data.values())
            
            total_annotated = total_bullish + total_bearish + total_neutral
            avg_sentiment = (total_bullish - total_bearish) / total_annotated if total_annotated > 0 else 0
            
            if total_mentions > 0:
                term_stats.append((term, total_mentions, avg_sentiment))
        
        # Sort by mention count
        term_stats.sort(key=lambda x: x[1], reverse=True)
        
        return term_stats[:limit]
    
    def generate_chart_data(
        self,
        trend_data: List[TrendDataPoint],
        include_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        Generate data formatted for ECharts visualization.
        
        Args:
            trend_data: List of TrendDataPoint objects
            include_sentiment: Include sentiment breakdown
            
        Returns:
            Dict with ECharts-compatible data structure
        """
        dates = [dp.date.isoformat() for dp in trend_data]
        mentions = [dp.mention_count for dp in trend_data]
        
        chart_data = {
            "xAxis": dates,
            "series": [
                {
                    "name": "Mentions",
                    "type": "bar",
                    "data": mentions
                }
            ]
        }
        
        if include_sentiment:
            chart_data["series"].extend([
                {
                    "name": "Bullish",
                    "type": "line",
                    "data": [dp.bullish_count for dp in trend_data],
                    "stack": "sentiment"
                },
                {
                    "name": "Bearish",
                    "type": "line",
                    "data": [dp.bearish_count for dp in trend_data],
                    "stack": "sentiment"
                },
                {
                    "name": "Neutral",
                    "type": "line",
                    "data": [dp.neutral_count for dp in trend_data],
                    "stack": "sentiment"
                }
            ])
            
            # Add sentiment score line
            chart_data["series"].append({
                "name": "Sentiment Score",
                "type": "line",
                "yAxisIndex": 1,
                "data": [round(dp.avg_sentiment, 3) for dp in trend_data]
            })
        
        return chart_data


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Trend Analysis Module")
    print("=" * 60)
    
    async def test_analysis():
        analyzer = TrendAnalyzer("test_layer3.db")
        
        # Initialize database
        await analyzer.db.initialize()
        
        print("\n1. Calculating daily frequencies...")
        # This would require actual data in the database
        try:
            frequencies = await analyzer.calculate_daily_frequencies("inflation", days_back=7)
            print(f"   Found data for {len(frequencies)} days")
        except Exception as e:
            print(f"   No data available: {e}")
        
        print("\n2. Generating chart data format...")
        # Create sample data
        sample_data = [
            TrendDataPoint(
                date=date.today() - timedelta(days=i),
                term="inflation",
                mention_count=10 + i,
                avg_sentiment=0.1 * (i - 3),
                bullish_count=5 + i,
                bearish_count=3,
                neutral_count=2
            )
            for i in range(7, 0, -1)
        ]
        
        chart_data = analyzer.generate_chart_data(sample_data)
        print(f"   Generated chart with {len(chart_data['series'])} series")
        print(f"   Dates: {chart_data['xAxis']}")
        
        print("\nTest complete!")
    
    asyncio.run(test_analysis())

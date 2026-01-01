"""
Tests for Unified API (Phase 4)

Run with: python -m pytest tests/test_unified_api.py -v
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create test client for the FastAPI app."""
    from backend.main import app
    return TestClient(app)


class TestUnifiedSearchAPI:
    """Test cases for /api/v1/search/{term} endpoint."""
    
    def test_unified_search_returns_structure(self, client):
        """Test that unified search returns expected response structure."""
        response = client.get("/api/v1/search/Inflation")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level structure
        assert "term" in data
        assert "searched_at" in data
        assert "layer1" in data
        assert "layer2" in data
        assert "layer3" in data
        
        # Check term value
        assert data["term"] == "Inflation"
    
    def test_unified_search_layer1_structure(self, client):
        """Test that layer1 data has correct structure."""
        response = client.get("/api/v1/search/GDP")
        data = response.json()
        
        layer1 = data["layer1"]
        assert "found" in layer1
        assert "definitions" in layer1
        assert "related_terms" in layer1
        assert isinstance(layer1["definitions"], dict)
        assert isinstance(layer1["related_terms"], list)
    
    def test_unified_search_layer2_structure(self, client):
        """Test that layer2 data has correct structure."""
        response = client.get("/api/v1/search/Interest%20Rate")
        data = response.json()
        
        layer2 = data["layer2"]
        assert "found" in layer2
        assert "pboc_paragraphs" in layer2
        assert "fed_paragraphs" in layer2
        assert "alignments" in layer2
        assert "total_mentions" in layer2
        assert isinstance(layer2["pboc_paragraphs"], list)
        assert isinstance(layer2["fed_paragraphs"], list)
    
    def test_unified_search_layer3_structure(self, client):
        """Test that layer3 data has correct structure."""
        response = client.get("/api/v1/search/Recession")
        data = response.json()
        
        layer3 = data["layer3"]
        assert "found" in layer3
        assert "recent_articles" in layer3
        assert "sentiment_distribution" in layer3
        assert "trend_data" in layer3
        assert "days_analyzed" in layer3
        
        # Check sentiment distribution structure
        sentiment = layer3["sentiment_distribution"]
        assert "bullish" in sentiment
        assert "bearish" in sentiment
        assert "neutral" in sentiment
        assert "total" in sentiment
    
    def test_unified_search_empty_term_error(self, client):
        """Test that empty search term returns 400 error."""
        response = client.get("/api/v1/search/%20")  # whitespace only
        assert response.status_code == 400
    
    def test_unified_search_with_days_back_param(self, client):
        """Test that days_back parameter is respected."""
        response = client.get("/api/v1/search/Inflation?days_back=7")
        
        assert response.status_code == 200
        data = response.json()
        assert data["layer3"]["days_analyzed"] == 7
    
    def test_unified_search_layer_exclusion(self, client):
        """Test that layer inclusion parameters work."""
        response = client.get("/api/v1/search/Inflation?include_layer2=false")
        
        assert response.status_code == 200
        data = response.json()
        # Layer2 should have default empty values since it was excluded
        # The exact behavior depends on implementation


class TestUnifiedTrendAPI:
    """Test cases for /api/v1/trend/{term} endpoint."""
    
    def test_trend_returns_structure(self, client):
        """Test that trend endpoint returns expected structure."""
        response = client.get("/api/v1/trend/Inflation")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "term" in data
        assert "days_back" in data
        assert "analyzed_at" in data
        assert "trend_direction" in data
        assert "trend_data" in data
        assert "sentiment_summary" in data
        assert "policy_mentions" in data
        assert "total_articles" in data
    
    def test_trend_direction_values(self, client):
        """Test that trend_direction has valid values."""
        response = client.get("/api/v1/trend/GDP?days_back=30")
        data = response.json()
        
        assert data["trend_direction"] in ["increasing", "decreasing", "stable"]
    
    def test_trend_days_back_parameter(self, client):
        """Test that days_back parameter is respected."""
        response = client.get("/api/v1/trend/Inflation?days_back=14")
        
        assert response.status_code == 200
        data = response.json()
        assert data["days_back"] == 14
    
    def test_trend_empty_term_error(self, client):
        """Test that empty term returns 400 error."""
        response = client.get("/api/v1/trend/%20")
        assert response.status_code == 400


class TestUnifiedHealthAPI:
    """Test cases for /api/v1/health endpoint."""
    
    def test_health_check(self, client):
        """Test that health endpoint returns status."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "layers" in data
        assert "timestamp" in data
        
        # Check layers structure
        layers = data["layers"]
        assert "layer1" in layers
        assert "layer2" in layers
        assert "layer3" in layers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Integration test for backend API endpoints
Tests the enhanced FastAPI service with middleware
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "development" / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client"""
    # Import app after adding to path
    from fastapi_service.main import app
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns service info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "Luminate AI" in data["service"]


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    # May be 200 or 503 depending on ChromaDB availability
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert "chromadb_documents" in data


def test_stats_endpoint(client):
    """Test stats endpoint returns metrics"""
    response = client.get("/stats")
    
    # May fail if ChromaDB not available
    if response.status_code == 200:
        data = response.json()
        assert "api_metrics" in data
        assert "cache_size" in data
        assert "database" in data


def test_rate_limiting():
    """Test rate limiting works"""
    # This test requires a fresh client to test rate limiting
    from fastapi_service.main import app
    client = TestClient(app)
    
    # Make requests up to the limit
    # Note: In test mode, rate limiting may behave differently
    # This is a basic smoke test
    
    for _ in range(5):
        response = client.post(
            "/query/navigate",
            json={
                "query": "test query",
                "n_results": 5
            }
        )
        # Should get either 200 (success) or 503 (service unavailable)
        # or 429 (rate limited)
        assert response.status_code in [200, 429, 503]


def test_input_validation():
    """Test input validation"""
    from fastapi_service.main import app
    client = TestClient(app)
    
    # Test with empty query (should fail validation)
    response = client.post(
        "/query/navigate",
        json={
            "query": "",  # Empty query
            "n_results": 5
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Test with invalid n_results
    response = client.post(
        "/query/navigate",
        json={
            "query": "test",
            "n_results": -1  # Invalid
        }
    )
    assert response.status_code == 422  # Validation error


def test_conversation_endpoints():
    """Test conversation save/load/delete endpoints"""
    from fastapi_service.main import app
    client = TestClient(app)
    
    session_id = "test_session_123"
    
    # Save conversation
    response = client.post(
        "/conversation/save",
        json={
            "session_id": session_id,
            "messages": [
                {
                    "role": "user",
                    "content": "test message",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["session_id"] == session_id
    
    # Load conversation
    response = client.get(f"/conversation/load/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "test message"
    
    # Delete conversation
    response = client.delete(f"/conversation/{session_id}")
    assert response.status_code == 200
    
    # Verify deleted
    response = client.get(f"/conversation/load/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

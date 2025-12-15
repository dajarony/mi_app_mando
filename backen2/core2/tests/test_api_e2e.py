"""
E2E tests for FastAPI health and metrics endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from core2.core_dajarony.entradas.api_app import app

client = TestClient(app)

@pytest.mark.parametrize("path,expected_status", [
    ("/health", 200),
    ("/live", 200),
    ("/ready", 200),
    ("/metrics", 200),
])
def test_endpoints(path: str, expected_status: int):
    response = client.get(path)
    assert response.status_code == expected_status
    if path != "/metrics":
        json_data = response.json()
        assert "status" in json_data
        assert "timestamp" in json_data

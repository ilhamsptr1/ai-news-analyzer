"""
AI News Analyzer — Health Check Tests

Tests the GET /api/health endpoint for:
- HTTP 200 status
- Correct 'status' field
- Correct 'service' field
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """Health endpoint must return HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_has_status():
    """Response body must include a 'status' field."""
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data


def test_health_response_has_service():
    """Response body must include a 'service' field."""
    response = client.get("/api/health")
    data = response.json()
    assert "service" in data


def test_health_status_is_ok():
    """The 'status' field must equal 'ok'."""
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_service_name():
    """The 'service' field must identify the application."""
    response = client.get("/api/health")
    data = response.json()
    assert data["service"] == "AI News Analyzer API"


def test_health_response_content_type():
    """Response must be JSON."""
    response = client.get("/api/health")
    assert "application/json" in response.headers["content-type"]

import pytest
from fastapi.testclient import TestClient
from backend.main import app, validate_origin, ALLOWED_ORIGINS

client = TestClient(app)

def test_cors_origin_validation():
    """Verify origin validation regex works correctly."""
    assert validate_origin("http://localhost:8000") is True
    assert validate_origin("https://sheland.com") is True
    assert validate_origin("https://www.sheland.com") is True
    assert validate_origin("http://127.0.0.1:8000") is True
    
    # Invalid origins
    assert validate_origin("invalid_origin") is False
    assert validate_origin("ftp://sheland.com") is False
    assert validate_origin("javascript:alert(1)") is False

def test_cors_no_wildcard_in_allowed_origins():
    """Ensure wildcard '*' is never present in ALLOWED_ORIGINS."""
    assert "*" not in ALLOWED_ORIGINS
    for origin in ALLOWED_ORIGINS:
        assert origin.startswith("http://") or origin.startswith("https://")

def test_cors_preflight_request():
    """Test CORS preflight OPTIONS request from an allowed origin."""
    response = client.options(
        "/api/products",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8000"
    assert response.headers.get("access-control-allow-credentials") == "true"

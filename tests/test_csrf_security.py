import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_csrf_missing_x_requested_with_header_rejected():
    """Ensure state-changing POST request in browser context without X-Requested-With header is blocked (403 Forbidden)."""
    response = client.post(
        "/api/orders",
        headers={"Origin": "http://localhost:8000"},
        json={"items": [], "shipping_address": "Test"}
    )
    assert response.status_code == 403
    assert "CSRF Error" in response.json()["detail"]

def test_csrf_unauthorized_origin_rejected():
    """Ensure state-changing request from an unauthorized Origin is blocked (403 Forbidden)."""
    response = client.post(
        "/api/orders",
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://malicious-attacker-site.com"
        },
        json={"items": [], "shipping_address": "Test"}
    )
    assert response.status_code == 403
    assert "CSRF Error" in response.json()["detail"]

def test_csrf_valid_headers_accepted():
    """Ensure state-changing request with valid Origin and X-Requested-With header passes CSRF middleware."""
    response = client.post(
        "/api/orders",
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "http://localhost:8000"
        },
        json={"items": [], "shipping_address": "Test"}
    )
    # Passed CSRF check (fails further down on validation 404/422 if products missing, but NOT 403 CSRF error)
    assert response.status_code != 403

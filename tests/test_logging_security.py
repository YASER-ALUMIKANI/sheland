import pytest
import logging
from fastapi.testclient import TestClient
from backend.main import app
from backend.payments import verify_payment_transaction

client = TestClient(app)

def test_request_logging_middleware_execution():
    """Ensure HTTP requests pass through log_requests_middleware cleanly."""
    response = client.get("/")
    assert response.status_code == 200

def test_failed_login_logging(caplog):
    """Ensure failed login attempts produce WARNING level audit log."""
    with caplog.at_level(logging.WARNING):
        response = client.post(
            "/api/auth/login",
            headers={"X-Requested-With": "XMLHttpRequest"},
            json={"email_or_phone": "nonexistent@sheland.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert any("Failed login attempt" in record.message for record in caplog.records)

def test_payment_transaction_logging(caplog):
    """Ensure payment transaction verifications produce audit logs."""
    with caplog.at_level(logging.INFO):
        res = verify_payment_transaction("kuraimi", "TX123456", 15000.0)
        assert res["success"] is True
        assert any("Payment transaction verified" in record.message for record in caplog.records)

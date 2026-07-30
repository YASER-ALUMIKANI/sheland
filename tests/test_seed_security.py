import pytest
from fastapi.testclient import TestClient
from backend.main import app, ensure_default_users
from tests.conftest import TestingSessionLocal
from backend import models, auth

client = TestClient(app)

def test_api_seed_endpoint_removed():
    """Ensure GET /api/seed public endpoint is deleted and returns 404 Not Found."""
    response = client.get("/api/seed")
    assert response.status_code == 404

def test_ensure_default_users_does_not_reset_existing_admin_password(setup_db):
    """Ensure running ensure_default_users does not overwrite an existing admin password hash."""
    db = TestingSessionLocal()
    try:
        # Create initial default admin
        ensure_default_users(db)

        admin = db.query(models.User).filter(models.User.email == "admin@sheland.com").first()
        assert admin is not None
        assert auth.verify_password("admin123", admin.password_hash)

        # Admin changes password to a new custom password
        new_custom_password = "MySecureCustomPassword2026!"
        admin.password_hash = auth.hash_password(new_custom_password)
        db.commit()

        # Re-run ensure_default_users (e.g. during system startup or internal tasks)
        ensure_default_users(db)

        # Refresh admin from DB
        db.refresh(admin)
        # Verify the custom password was NOT overwritten by admin123
        assert auth.verify_password(new_custom_password, admin.password_hash)
        assert not auth.verify_password("admin123", admin.password_hash)
    finally:
        db.close()

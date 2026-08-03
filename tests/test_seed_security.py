import pytest
from fastapi.testclient import TestClient
from backend.main import app, ensure_default_users
from tests.conftest import TestingSessionLocal
from backend import models, auth

client = TestClient(app)

def test_api_seed_endpoint_removed():
    """Ensure GET /api/seed public endpoint is not publicly accessible (returns 404 or 405)."""
    response = client.get("/api/seed")
    assert response.status_code in (404, 405)

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

def test_ensure_default_users_uses_env_vars(monkeypatch, setup_db):
    """Ensure ensure_default_users reads default passwords from environment variables when seeding."""
    monkeypatch.setenv("ADMIN_DEFAULT_PASSWORD", "CustomEnvAdminPass2026!")
    monkeypatch.setenv("SUPERADMIN_DEFAULT_PASSWORD", "CustomEnvSuperPass2026!")
    monkeypatch.setenv("SELLER_DEFAULT_PASSWORD", "CustomEnvSellerPass2026!")

    db = TestingSessionLocal()
    try:
        db.query(models.User).filter(models.User.email.in_([
            "admin@sheland.com", "superadmin@sheland.com", "seller@sheland.com"
        ])).delete(synchronize_session=False)
        db.commit()

        ensure_default_users(db)

        admin = db.query(models.User).filter(models.User.email == "admin@sheland.com").first()
        super_admin = db.query(models.User).filter(models.User.email == "superadmin@sheland.com").first()
        seller = db.query(models.User).filter(models.User.email == "seller@sheland.com").first()

        assert admin is not None and auth.verify_password("CustomEnvAdminPass2026!", admin.password_hash)
        assert super_admin is not None and auth.verify_password("CustomEnvSuperPass2026!", super_admin.password_hash)
        assert seller is not None and auth.verify_password("CustomEnvSellerPass2026!", seller.password_hash)
    finally:
        db.close()



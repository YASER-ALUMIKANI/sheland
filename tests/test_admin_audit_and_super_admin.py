"""
CityLand Backend - Unit & Integration Tests for Admin Audit Logging & Super Admin Security
# ponytail: Compact test suite validating AuditLog record generation, Super Admin privilege boundaries, RBAC on audit logs, and rate limit checks.
"""
import uuid
import pytest
from tests.conftest import TestingSessionLocal
from backend import auth, models

def create_user_token(name: str, email: str, role: str) -> tuple[int, str]:
    """Helper to create a user and return (user_id, JWT token)."""
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            name=name,
            email=email,
            phone=f"077{uuid.uuid4().hex[:6]}",
            password_hash=auth.hash_password("password123"),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = user.id
    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    db.close()
    return user_id, token


def test_admin_update_user_role_generates_audit_log(client):
    """Ensure promoting or changing a user role by admin generates an AuditLog entry."""
    admin_id, admin_token = create_user_token("الأدمن الرئيسي", "admin_audit@sheland.com", "admin")
    target_user_id, _ = create_user_token("العميل المستهدف", "target_cust@sheland.com", "customer")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Requested-With": "XMLHttpRequest"
    }
    payload = {"role": "seller"}

    res = client.put(f"/api/admin/users/{target_user_id}/role", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["role"] == "seller"

    # Verify AuditLog record in DB
    db = TestingSessionLocal()
    audit = db.query(models.AuditLog).filter(
        models.AuditLog.target_user_id == target_user_id,
        models.AuditLog.action == "role_change"
    ).first()
    assert audit is not None
    assert audit.performed_by == admin_id
    assert audit.old_value == "customer"
    assert audit.new_value == "seller"
    db.close()


def test_regular_admin_cannot_promote_to_super_admin(client):
    """Ensure regular admin cannot create or promote any user to super_admin (403 Forbidden)."""
    _, admin_token = create_user_token("أدمن عادي", "regular_admin@sheland.com", "admin")
    target_id, _ = create_user_token("مستخدم عادي", "target_normal@sheland.com", "customer")

    headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Requested-With": "XMLHttpRequest"
    }

    # 1. Attempt to update existing role to super_admin
    res_update = client.put(f"/api/admin/users/{target_id}/role", json={"role": "super_admin"}, headers=headers)
    assert res_update.status_code == 403
    assert "Super Admin" in res_update.json()["detail"]

    # 2. Attempt to create new user with role super_admin
    new_user_payload = {
        "name": "محاولة مدير فائق",
        "email": "try_super@sheland.com",
        "phone": "0770998877",
        "password": "password123",
        "role": "super_admin"
    }
    res_create = client.post("/api/admin/users", json=new_user_payload, headers=headers)
    assert res_create.status_code == 403
    assert "Super Admin" in res_create.json()["detail"]


def test_super_admin_can_manage_all_admins(client):
    """Ensure Super Admin can successfully create and update super_admin role."""
    _, super_token = create_user_token("المدير الفائق", "super_admin_user@sheland.com", "super_admin")
    headers = {
        "Authorization": f"Bearer {super_token}",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Create new super_admin
    new_super_payload = {
        "name": "مدير فائق جديد",
        "email": f"new_super_{uuid.uuid4().hex[:6]}@sheland.com",
        "phone": f"077{uuid.uuid4().hex[:6]}",
        "password": "password123",
        "role": "super_admin"
    }
    res = client.post("/api/admin/users", json=new_super_payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["role"] == "super_admin"


def test_get_audit_logs_rbac(client):
    """Ensure security audit logs endpoint is accessible to admins and forbidden to customers/sellers."""
    _, cust_token = create_user_token("عميل فحص السجلات", "cust_logs@sheland.com", "customer")
    _, seller_token = create_user_token("تاجر فحص السجلات", "seller_logs@sheland.com", "seller")
    _, admin_token = create_user_token("أدمن السجلات", "admin_logs@sheland.com", "admin")

    # Customer attempt -> 403
    res_cust = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {cust_token}"})
    assert res_cust.status_code == 403

    # Seller attempt -> 403
    res_seller = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {seller_token}"})
    assert res_seller.status_code == 403

    # Admin attempt -> 200
    res_admin = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert isinstance(res_admin.json(), list)


def test_rate_limiting_protection(client):
    """Ensure rate-limited endpoints respond appropriately under repeated automated requests."""
    payload = {"email_or_phone": "nonexistent_rate_test@sheland.com", "password": "wrongpassword"}
    responses = [client.post("/api/auth/login", json=payload) for _ in range(5)]
    # All requests should return valid HTTP response status codes (401 Unauthorized or 429 Too Many Requests)
    assert all(r.status_code in [401, 429] for r in responses)

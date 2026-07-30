import pytest
from backend import models, auth
from tests.conftest import TestingSessionLocal

def test_prevent_public_role_escalation(client):
    # Attempt to register as admin via public /api/auth/register endpoint
    payload = {
        "name": "مبتز أدمن",
        "email": "hacker_admin@sheland.com",
        "phone": "0770009988",
        "password": "hacker_password_123",
        "role": "admin"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code in (400, 422)


def test_public_registration_allowed_roles(client):
    # Register customer
    cust_res = client.post("/api/auth/register", json={
        "name": "عميل مشروع",
        "email": "valid_cust@sheland.com",
        "phone": "0771112233",
        "password": "cust_password_123",
        "role": "customer"
    })
    assert cust_res.status_code == 201
    assert cust_res.json()["user"]["role"] == "customer"

    # Register seller
    seller_res = client.post("/api/auth/register", json={
        "name": "تاجر مشروع",
        "email": "valid_seller@sheland.com",
        "phone": "0774445566",
        "password": "seller_password_123",
        "role": "seller"
    })
    assert seller_res.status_code == 201
    assert seller_res.json()["user"]["role"] == "seller"

def test_admin_only_user_management(client):
    db = TestingSessionLocal()
    try:
        # Create admin user directly for test setup
        admin = models.User(
            name="أدمن رئيسي",
            email="super_admin_test@sheland.com",
            phone="0779990011",
            password_hash=auth.hash_password("admin_pass"),
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        token = auth.create_access_token({"sub": str(admin.id), "role": admin.role})
        headers = {"Authorization": f"Bearer {token}"}

        # Admin creates sales manager
        create_res = client.post("/api/admin/users", headers=headers, json={
            "name": "مدير مبيعات",
            "email": "sales_mgr@sheland.com",
            "phone": "0778881122",
            "password": "sales_pass_123",
            "role": "sales_manager"
        })
        assert create_res.status_code == 201
        created_user = create_res.json()
        assert created_user["role"] == "sales_manager"

        # Admin updates role of user
        update_res = client.put(f"/api/admin/users/{created_user['id']}/role", headers=headers, json={"role": "admin"})
        assert update_res.status_code == 200
        assert update_res.json()["role"] == "admin"

        # Verify audit logs endpoint
        audit_res = client.get("/api/admin/audit-logs", headers=headers)
        assert audit_res.status_code == 200
        logs = audit_res.json()
        assert len(logs) >= 2
    finally:
        db.close()

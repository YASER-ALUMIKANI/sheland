"""
CityLand Backend - Profile Management & Cascade Update Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_update_profile_name_and_phone(client: TestClient):
    """Verifies that updating profile name and phone number via PUT /api/auth/profile succeeds."""
    # 1. Register user
    reg = client.post(
        "/api/auth/register",
        json={"name": "Old Name", "email": "profile_test@example.com", "phone": "967770001111", "password": "OldPassword123"}
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # 2. Update profile
    update_resp = client.put(
        "/api/auth/profile",
        json={"name": "New Updated Name", "phone": "967779998888"},
        headers=headers
    )
    assert update_resp.status_code == 200
    user_data = update_resp.json()
    assert user_data["name"] == "New Updated Name"
    assert user_data["phone"] == "967779998888"

    # 3. Verify via GET /api/auth/me
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["name"] == "New Updated Name"
    assert me_resp.json()["phone"] == "967779998888"


def test_update_phone_cascades_to_orders(client: TestClient):
    """Verifies that changing phone number in user profile automatically cascades to past order records."""
    # 1. Register user & place order
    old_phone = "967771234567"
    new_phone = "967777654321"
    reg = client.post(
        "/api/auth/register",
        json={"name": "Cascade User", "email": "cascade_test@example.com", "phone": old_phone, "password": "Password123"}
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    order_resp = client.post(
        "/api/orders",
        json={
            "shipping_address": f"صنعاء - حي الأصبحي ({old_phone})",
            "payment_method": "COD",
            "items": [{"product_id": 1, "quantity": 1}]
        },
        headers=headers
    )
    assert order_resp.status_code == 200
    order_id = order_resp.json()["id"]
    assert order_resp.json()["phone"] == old_phone

    # 2. Update profile phone
    profile_update = client.put(
        "/api/auth/profile",
        json={"name": "Cascade User", "phone": new_phone},
        headers=headers
    )
    assert profile_update.status_code == 200

    # 3. Verify that past order phone and shipping_address string were updated
    my_orders = client.get("/api/orders/my", headers=headers)
    assert my_orders.status_code == 200
    orders_list = my_orders.json()
    target_order = next(o for o in orders_list if o["id"] == order_id)
    assert target_order["phone"] == new_phone
    assert new_phone in target_order["shipping_address"]


def test_profile_update_requires_auth(client: TestClient):
    """Verifies that updating profile without an auth token returns HTTP 401."""
    resp = client.put("/api/auth/profile", json={"name": "Unauthorized Attempt"})
    assert resp.status_code == 401


def test_change_password_wrong_current_rejects(client: TestClient):
    """Verifies that providing an incorrect current password when changing password fails with HTTP 400."""
    reg = client.post(
        "/api/auth/register",
        json={"name": "Password User", "email": "pwd_test@example.com", "phone": "967771122334", "password": "CorrectPassword123"}
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    change_resp = client.put(
        "/api/auth/change-password",
        json={
            "current_password": "WRONG_Current_Password",
            "new_password": "NewSuperPassword123"
        },
        headers=headers
    )
    assert change_resp.status_code == 400
    assert "غير صحيحة" in change_resp.json()["detail"]

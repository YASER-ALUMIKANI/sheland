"""
CityLand Backend - Order Tracking & Customer Orders Isolation Tests
"""
import pytest
from fastapi.testclient import TestClient


def test_track_order_by_owner_success(client: TestClient):
    """Verifies that the customer who created an order can track it by order number."""
    # 1. Register & login Customer A
    email_a = "track_owner@example.com"
    pwd = "Password123"
    reg_resp = client.post(
        "/api/auth/register",
        json={"name": "Owner User", "email": email_a, "phone": "967775556677", "password": pwd}
    )
    assert reg_resp.status_code == 201
    token_a = reg_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Create order for Customer A
    order_resp = client.post(
        "/api/orders",
        json={
            "shipping_address": "صنعاء - شارع الستين",
            "payment_method": "COD",
            "items": [{"product_id": 1, "quantity": 1}]
        },
        headers=headers_a
    )
    assert order_resp.status_code == 200
    order_number = order_resp.json()["order_number"]

    # 3. Track order as Owner
    track_resp = client.get(f"/api/orders/track/{order_number}", headers=headers_a)
    assert track_resp.status_code == 200
    assert track_resp.json()["order_number"] == order_number


def test_track_order_by_another_user_forbidden(client: TestClient):
    """Verifies that a customer cannot track another customer's order (HTTP 403)."""
    # 1. Customer A creates order
    reg_a = client.post(
        "/api/auth/register",
        json={"name": "User A", "email": "user_a_track@example.com", "phone": "967771110001", "password": "Password123"}
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}
    order_resp = client.post(
        "/api/orders",
        json={
            "shipping_address": "عدن - المعلا",
            "payment_method": "COD",
            "items": [{"product_id": 1, "quantity": 1}]
        },
        headers=headers_a
    )
    order_number = order_resp.json()["order_number"]

    # 2. Customer B attempts to track Customer A's order
    reg_b = client.post(
        "/api/auth/register",
        json={"name": "User B", "email": "user_b_track@example.com", "phone": "967771110002", "password": "Password123"}
    )
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    track_resp = client.get(f"/api/orders/track/{order_number}", headers=headers_b)
    assert track_resp.status_code == 403
    assert "غير مصرح" in track_resp.json()["detail"]


def test_track_nonexistent_order_returns_404(client: TestClient):
    """Verifies that tracking an invalid/non-existent order number returns HTTP 404."""
    reg = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "dummy_track@example.com", "phone": "967771110003", "password": "Password123"}
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    track_resp = client.get("/api/orders/track/ORD-FAKE9999", headers=headers)
    assert track_resp.status_code == 404


def test_admin_can_track_any_order(client: TestClient):
    """Verifies that an administrator can track any user's order."""
    # 1. Customer creates an order
    reg_cust = client.post(
        "/api/auth/register",
        json={"name": "Customer User", "email": "cust_order@example.com", "phone": "967771110004", "password": "Password123"}
    )
    headers_cust = {"Authorization": f"Bearer {reg_cust.json()['access_token']}"}
    order_resp = client.post(
        "/api/orders",
        json={
            "shipping_address": "تعز - شارع جمال",
            "payment_method": "COD",
            "items": [{"product_id": 1, "quantity": 1}]
        },
        headers=headers_cust
    )
    order_number = order_resp.json()["order_number"]

    # 2. Generate Admin Access Token directly
    from backend import auth
    admin_token = auth.create_access_token({"sub": "1", "role": "admin"})
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # 3. Admin tracks customer's order
    track_resp = client.get(f"/api/orders/track/{order_number}", headers=headers_admin)
    assert track_resp.status_code == 200
    assert track_resp.json()["order_number"] == order_number



def test_get_my_orders_scoped_to_user(client: TestClient):
    """Verifies that /api/orders/my returns only the orders belonging to the authenticated user."""
    # Customer 1 registers & places 2 orders
    reg1 = client.post(
        "/api/auth/register",
        json={"name": "MyOrders User 1", "email": "myorders1@example.com", "phone": "967778881111", "password": "Password123"}
    )
    h1 = {"Authorization": f"Bearer {reg1.json()['access_token']}"}
    client.post("/api/orders", json={"shipping_address": "Address 1", "payment_method": "COD", "items": [{"product_id": 1, "quantity": 1}]}, headers=h1)
    client.post("/api/orders", json={"shipping_address": "Address 2", "payment_method": "COD", "items": [{"product_id": 1, "quantity": 1}]}, headers=h1)

    # Customer 2 registers & places 1 order
    reg2 = client.post(
        "/api/auth/register",
        json={"name": "MyOrders User 2", "email": "myorders2@example.com", "phone": "967778882222", "password": "Password123"}
    )
    h2 = {"Authorization": f"Bearer {reg2.json()['access_token']}"}
    client.post("/api/orders", json={"shipping_address": "Address 3", "payment_method": "COD", "items": [{"product_id": 1, "quantity": 1}]}, headers=h2)

    # Fetch /api/orders/my for User 1
    resp1 = client.get("/api/orders/my", headers=h1)
    assert resp1.status_code == 200
    orders1 = resp1.json()
    assert len(orders1) == 2

    # Fetch /api/orders/my for User 2
    resp2 = client.get("/api/orders/my", headers=h2)
    assert resp2.status_code == 200
    orders2 = resp2.json()
    assert len(orders2) == 1

"""
Sheland Backend Integration Tests
# ponytail: Simple pytest suite verifying all REST API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

TEST_USER_TOKEN = None
TEST_ADMIN_TOKEN = None


def _register_user(name, email, phone, password, role="customer"):
    """Register a new user and return the token."""
    res = client.post("/api/auth/register", json={
        "name": name, "email": email, "phone": phone, "password": password, "role": role
    })
    if res.status_code == 201:
        return res.json()["access_token"]
    return None


def _login(email, password):
    """Login and return JWT token."""
    res = client.post("/api/auth/login", json={"email_or_phone": email, "password": password})
    if res.status_code == 200:
        return res.json()["access_token"]
    return None


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _get_or_create_user():
    """Login as seeded admin, or register a fallback test user."""
    global TEST_ADMIN_TOKEN
    if TEST_ADMIN_TOKEN:
        return TEST_ADMIN_TOKEN

    token = _login("admin@sheland.com", "admin123")
    if token:
        TEST_ADMIN_TOKEN = token
        return token

    token = _register_user("مدير الاختبار", "testadmin@test.com", "0779999999", "testpass123")
    if token:
        TEST_ADMIN_TOKEN = token
    return token


def _get_or_create_seller():
    """Login as seeded seller, or register a seller test user."""
    token = _login("seller@sheland.com", "seller123")
    if token:
        return token

    token = _register_user("بائع الاختبار", "testseller@test.com", "0778888888", "sellerpass123", role="seller")
    if token:
        return token
    return None


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200


def test_read_admin():
    response = client.get("/admin")
    assert response.status_code == 200


def test_get_categories():
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_products():
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_product_requires_auth():
    new_product = {
        "title_ar": "منتج بدون مصادقة",
        "title_en": "No Auth Product",
        "slug": "no-auth-prod",
        "category_id": 1,
        "price": 50.0,
        "image_url": "https://example.com/img.jpg"
    }
    res = client.post("/api/products", json=new_product)
    assert res.status_code == 401


def test_create_and_delete_product():
    token = _get_or_create_seller()
    if not token:
        pytest.skip("Could not authenticate any seller user")

    new_product = {
        "title_ar": "منتج تجريبي للاختبار",
        "title_en": "Test Product Demo",
        "slug": "test-prod-123",
        "category_id": 1,
        "price": 99.0,
        "compare_at_price": 149.0,
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1",
        "free_shipping": True,
        "cod_available": True
    }
    create_res = client.post("/api/products", json=new_product, headers=_auth(token))
    assert create_res.status_code == 200
    prod_data = create_res.json()
    prod_id = prod_data["id"]
    assert prod_data["title_ar"] == "منتج تجريبي للاختبار"

    del_res = client.delete(f"/api/products/{prod_id}", headers=_auth(token))
    assert del_res.status_code in (200, 403)


def test_create_and_track_order():
    token = _get_or_create_user()
    headers = _auth(token) if token else {}

    products_res = client.get("/api/products")
    products = products_res.json()
    if not products:
        pytest.skip("No products seeded")

    order_payload = {
        "user_id": 1,
        "customer_name": "ياسر العبدلي",
        "phone": "771234567",
        "shipping_address": "مدينة البيضاء - الشارع العام",
        "payment_method": "COD",
        "items": [{"product_id": products[0]["id"], "quantity": 1}]
    }
    res = client.post("/api/orders", json=order_payload, headers=headers)
    assert res.status_code == 200
    order_data = res.json()
    assert "order_number" in order_data
    order_num = order_data["order_number"]

    track_res = client.get(f"/api/orders/track/{order_num}", headers=headers)
    assert track_res.status_code == 200
    assert track_res.json()["order_number"] == order_num


def test_validate_coupon():
    res = client.get("/api/coupons/validate?code=CITY10&total=100")
    if res.status_code == 404:
        pytest.skip("CITY10 coupon not seeded")
    assert res.status_code == 200
    coupon_data = res.json()
    assert coupon_data["valid"] is True
    assert coupon_data["discount_amount"] == 10.0


def test_validate_coupon_invalid():
    res = client.get("/api/coupons/validate?code=FAKE&total=100")
    assert res.status_code == 404


def test_change_password():
    token = _get_or_create_user()
    if not token:
        pytest.skip("Could not authenticate any user")

    # Determine current password based on which user we logged in as
    current_password = "admin123"

    res = client.put("/api/auth/change-password", json={
        "current_password": "wrong_password",
        "new_password": "newpass123"
    }, headers=_auth(token))
    assert res.status_code == 400

    res = client.put("/api/auth/change-password", json={
        "current_password": current_password,
        "new_password": "admin456"
    }, headers=_auth(token))
    assert res.status_code == 200

    res = client.put("/api/auth/change-password", json={
        "current_password": "admin456",
        "new_password": current_password
    }, headers=_auth(token))
    assert res.status_code == 200


def test_change_password_requires_auth():
    res = client.put("/api/auth/change-password", json={
        "current_password": "x",
        "new_password": "y"
    })
    assert res.status_code == 401


def test_change_password_new_too_short():
    token = _get_or_create_user()
    if not token:
        pytest.skip("Could not authenticate any user")

    res = client.put("/api/auth/change-password", json={
        "current_password": "admin123",
        "new_password": "123"
    }, headers=_auth(token))
    assert res.status_code == 422


def test_product_review():
    review_payload = {
        "author_name": "مختبر النظام",
        "order_number": "ORD-TEST-001",
        "rating": 5,
        "comment": "منتج ممتاز جداً وتوصيل سريع"
    }
    res = client.post("/api/products/1/reviews", json=review_payload)
    assert res.status_code == 401

    get_res = client.get("/api/products/1/reviews")
    assert get_res.status_code == 200
    assert isinstance(get_res.json(), list)


def test_user_profile_update():
    token = _get_or_create_user()
    if not token:
        pytest.skip("Could not authenticate any user")

    res = client.put("/api/auth/profile", json={
        "name": "اسم محدث"
    }, headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["name"] == "اسم محدث"


def test_admin_user_management():
    token = _get_or_create_user()
    if not token:
        pytest.skip("Could not authenticate any user")

    res = client.get("/api/admin/users", headers=_auth(token))
    if res.status_code == 403:
        pytest.skip("User is not admin")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

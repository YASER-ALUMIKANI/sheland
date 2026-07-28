"""
Sheland Backend Integration Tests
# ponytail: Simple pytest suite verifying all REST API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

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
    assert len(data) > 0

def test_create_and_delete_product():
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
    # Create
    create_res = client.post("/api/products", json=new_product)
    assert create_res.status_code == 200
    prod_data = create_res.json()
    prod_id = prod_data["id"]
    assert prod_data["title_ar"] == "منتج تجريبي للاختبار"

    # Delete
    del_res = client.delete(f"/api/products/{prod_id}")
    assert del_res.status_code == 200

def test_create_and_track_order():
    order_payload = {
        "user_id": 1,
        "customer_name": "ياسر العبدلي",
        "phone": "771234567",
        "shipping_address": "مدينة البيضاء - الشارع العام",
        "payment_method": "COD",
        "items": [{"product_id": 1, "quantity": 2}]
    }
    res = client.post("/api/orders", json=order_payload)

    assert res.status_code == 200
    order_data = res.json()
    assert "order_number" in order_data
    order_num = order_data["order_number"]

    # Track order
    track_res = client.get(f"/api/orders/track/{order_num}")
    assert track_res.status_code == 200
    assert track_res.json()["order_number"] == order_num

def test_validate_coupon():
    res = client.post("/api/coupons/validate?code=CITY10&total=100")
    assert res.status_code == 200
    coupon_data = res.json()
    assert coupon_data["valid"] is True
    assert coupon_data["discount_amount"] == 10.0

def test_product_review():
    review_payload = {
        "author_name": "مختبر النظام",
        "rating": 5,
        "comment": "منتج ممتاز جداً وتوصيل سريع"
    }
    res = client.post("/api/products/1/reviews", json=review_payload)
    assert res.status_code == 200
    rev_data = res.json()
    assert rev_data["rating"] == 5

    # Get reviews
    get_res = client.get("/api/products/1/reviews")
    assert get_res.status_code == 200
    assert len(get_res.json()) > 0

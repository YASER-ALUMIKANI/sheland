"""
CityLand Backend - Extended Product Reviews & Purchase Verification Tests
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import TestingSessionLocal
from backend import models, auth


def create_delivered_order_for_user(client: TestClient, headers: dict, product_id: int = 1, customer_name: str = None) -> str:
    """Helper to place an order and mark its status as delivered so reviews can be submitted."""
    payload = {
        "shipping_address": "صنعاء - شارع حده",
        "payment_method": "COD",
        "items": [{"product_id": product_id, "quantity": 1}]
    }
    if customer_name:
        payload["customer_name"] = customer_name

    order_resp = client.post(
        "/api/orders",
        json=payload,
        headers=headers
    )
    assert order_resp.status_code == 200
    order_id = order_resp.json()["id"]
    order_number = order_resp.json()["order_number"]

    # Mark as delivered via admin endpoint or direct DB update
    db = TestingSessionLocal()
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if order:
            order.status = "delivered"
            db.commit()
    finally:
        db.close()

    return order_number


def test_review_updates_product_rating(client: TestClient):
    """Verifies that adding a review recalculates the product average rating."""
    reg = client.post(
        "/api/auth/register",
        json={"name": "Rating Reviewer", "email": "rating_rev@example.com", "phone": "967770001999", "password": "Password123"}
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    create_delivered_order_for_user(client, headers, product_id=1)

    # Submit 5-star review
    rev_resp = client.post(
        "/api/products/1/reviews",
        json={"rating": 5, "comment": "منتج ممتاز جدًا!"},
        headers=headers
    )
    assert rev_resp.status_code == 200

    # Fetch product details via DB or GET /api/products
    db = TestingSessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == 1).first()
        assert prod.rating > 0
        assert isinstance(prod.rating, float)
    finally:
        db.close()


def test_review_updates_product_review_count(client: TestClient):
    """Verifies that adding a review updates the product review_count based on actual stored reviews."""
    reg = client.post(
        "/api/auth/register",
        json={"name": "Count Reviewer", "email": "count_rev@example.com", "phone": "967770002999", "password": "Password123"}
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    create_delivered_order_for_user(client, headers, product_id=1)

    rev_resp = client.post(
        "/api/products/1/reviews",
        json={"rating": 4, "comment": "جيد جدًا ووصل بسرعة"},
        headers=headers
    )
    assert rev_resp.status_code == 200

    db = TestingSessionLocal()
    try:
        prod = db.query(models.Product).filter(models.Product.id == 1).first()
        rev_count_db = db.query(models.Review).filter(models.Review.product_id == 1).count()
        assert prod.review_count == rev_count_db
        assert prod.review_count >= 1
    finally:
        db.close()


def test_check_purchased_endpoint_valid(client: TestClient):
    """Verifies that /api/orders/check-purchased returns verified=True for a valid order containing the product."""
    reg = client.post(
        "/api/auth/register",
        json={"name": "Check Buyer", "email": "check_buyer@example.com", "phone": "967770003999", "password": "Password123"}
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    order_number = create_delivered_order_for_user(client, headers, product_id=1, customer_name="Check Buyer")

    resp = client.get(f"/api/orders/check-purchased?order_number={order_number}&product_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["customer_name"] == "Check Buyer"



def test_check_purchased_endpoint_invalid_order(client: TestClient):
    """Verifies that /api/orders/check-purchased returns 404 for non-existent order numbers."""
    resp = client.get("/api/orders/check-purchased?order_number=ORD-INVALID999&product_id=1")
    assert resp.status_code == 404
    assert "غير موجود" in resp.json()["detail"]


def test_get_product_reviews_returns_all(client: TestClient):
    """Verifies GET /api/products/{id}/reviews returns list of reviews for the product."""
    resp = client.get("/api/products/1/reviews")
    assert resp.status_code == 200
    reviews = resp.json()
    assert isinstance(reviews, list)


def test_duplicate_review_same_product(client: TestClient):
    """Verifies behavior when submitting a second review for the same product."""
    reg = client.post(
        "/api/auth/register",
        json={"name": "Duplicate Reviewer", "email": "dup_rev@example.com", "phone": "967770004999", "password": "Password123"}
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    create_delivered_order_for_user(client, headers, product_id=1)

    # First review
    rev1 = client.post(
        "/api/products/1/reviews",
        json={"rating": 5, "comment": "التقييم الأول"},
        headers=headers
    )
    assert rev1.status_code == 200

    # Second review
    rev2 = client.post(
        "/api/products/1/reviews",
        json={"rating": 4, "comment": "التقييم الثاني المحدث"},
        headers=headers
    )
    assert rev2.status_code == 200
    assert rev2.json()["rating"] == 4

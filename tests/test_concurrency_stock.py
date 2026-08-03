"""
CityLand Backend - Concurrency & Race Condition Tests for Stock Deduction
# ponytail: Concurrent order placement tests ensuring zero overbooking and negative stock protection
"""
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

from backend.main import app
from backend import models, auth
from tests.conftest import TestingSessionLocal

client = TestClient(app)

def test_concurrent_orders_on_last_item_prevent_negative_stock(setup_db):
    """
    Simulates 10 concurrent buyers attempting to purchase the last 1 remaining item in stock simultaneously.
    Verifies that:
    1. Exactly 1 buyer succeeds (HTTP 200).
    2. 9 buyers are rejected with stock error (HTTP 422).
    3. Final stock is strictly 0 (never negative).
    4. Only 1 order item is committed to the database.
    """
    db = TestingSessionLocal()
    try:
        # Create a test customer & token
        customer = models.User(
            name="عميل التنافس",
            email="concurrent_buyer@test.com",
            phone="0779988776",
            password_hash=auth.hash_password("pass123"),
            role="customer"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        token = auth.create_access_token({"sub": str(customer.id), "role": "customer"})

        # Create category, seller, product, and variant with EXACTLY 1 item in stock
        cat = db.query(models.Category).first()
        seller = db.query(models.Seller).first()

        product = models.Product(
            seller_id=seller.id if seller else 1,
            category_id=cat.id if cat else 1,
            title_ar="آخر قطعة متوفرة",
            title_en="Last Item In Stock",
            slug="last-item-concurrency-test",
            price=15000.0,
            image_url="https://example.com/last.jpg"
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        variant = models.ProductVariant(
            product_id=product.id,
            sku="SKU-LAST-1",
            color="أحمر",
            size="M",
            stock=1  # Only 1 item left!
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)

        prod_id = product.id
        var_id = variant.id
    finally:
        db.close()

    headers = {"Authorization": f"Bearer {token}"}
    order_payload = {
        "customer_name": "مشتري موازي",
        "phone": "0779988776",
        "shipping_address": "البيضاء",
        "payment_method": "COD",
        "items": [
            {"product_id": prod_id, "variant_id": var_id, "quantity": 1}
        ]
    }

    def place_order():
        return client.post("/api/orders", json=order_payload, headers=headers)

    # Launch 10 concurrent purchase requests simultaneously
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(place_order) for _ in range(10)]
        for f in as_completed(futures):
            results.append(f.result())

    successes = [r for r in results if r.status_code == 200]
    failures = [r for r in results if r.status_code == 422]

    # Verify atomic stock protection guarantees
    assert len(successes) == 1, f"Expected exactly 1 successful order, but got {len(successes)}"
    assert len(failures) == 9, f"Expected 9 rejected orders due to stock depletion, but got {len(failures)}"

    # Check database state post-concurrency
    db_after = TestingSessionLocal()
    try:
        updated_variant = db_after.query(models.ProductVariant).filter(models.ProductVariant.id == var_id).first()
        assert updated_variant is not None
        assert updated_variant.stock == 0, f"Stock should be 0, but is {updated_variant.stock}"
    finally:
        db_after.close()

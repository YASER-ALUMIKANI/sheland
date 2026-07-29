import pytest
from backend import models
from tests.conftest import TestingSessionLocal

def test_order_creation_with_coupon(client):
    db = TestingSessionLocal()
    try:
        # 1. Create a product and a variant
        prod = models.Product(
            seller_id=1,
            title_ar="ساعة يد فاخرة",
            title_en="Luxury Watch",
            slug="luxury-watch",
            price=10000.0,
            category_id=1,
            image_url="http://example.com/watch.jpg"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)

        variant = models.ProductVariant(
            product_id=prod.id,
            color="أسود",
            size="عادي",
            stock=50,
            price_override=10000.0
        )
        db.add(variant)
        
        # 2. Create a coupon: 20% discount
        coupon = models.Coupon(
            code="SAVE20",
            discount_type="percent",
            discount_value=20.0,
            min_order_amount=5000.0,
            is_active=True
        )
        db.add(coupon)
        db.commit()

        # 3. Create order with coupon
        order_payload = {
            "customer_name": "اختبار الكوبون",
            "phone": "771234567",
            "shipping_address": "مدينة البيضاء",
            "payment_method": "COD",
            "coupon_code": "SAVE20",
            "items": [
                {"product_id": prod.id, "variant_id": variant.id, "quantity": 1}
            ]
        }
        
        res = client.post("/api/orders", json=order_payload)
        assert res.status_code == 200
        data = res.json()

        # Product price = 10000, 20% discount = 2000 => final total_amount = 8000
        assert data["coupon_code"] == "SAVE20"
        assert data["discount_amount"] == 2000.0
        assert data["total_amount"] == 8000.0
    finally:
        db.close()

import pytest
from datetime import datetime, timedelta
from backend import models, auth
from tests.conftest import TestingSessionLocal

def test_inventory_alerts_endpoint(client):
    db = TestingSessionLocal()
    try:
        # Create admin user
        admin = models.User(
            name="مدير المخزون",
            email="inv_admin_test@sheland.com",
            phone="07711223344",
            password_hash=auth.hash_password("admin123"),
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        token = auth.create_access_token({"sub": str(admin.id), "role": admin.role})
        headers = {"Authorization": f"Bearer {token}"}

        # Product 1: Low stock (stock = 3)
        p1 = models.Product(
            seller_id=1,
            title_ar="منتج منخفض المخزون",
            title_en="Low Stock Item",
            slug="low-stock-item",
            price=3000.0,
            category_id=1,
            image_url="http://example.com/item1.jpg"
        )
        db.add(p1)
        db.commit()
        db.refresh(p1)

        v1 = models.ProductVariant(
            product_id=p1.id,
            color="أحمر",
            stock=3,
            price_override=3000.0
        )
        db.add(v1)

        # Product 2: Normal active product (stock = 20)
        p2 = models.Product(
            seller_id=1,
            title_ar="منتج عالي المبيعات",
            title_en="High Sales Item",
            slug="high-sales-item",
            price=8000.0,
            category_id=1,
            image_url="http://example.com/item2.jpg"
        )
        db.add(p2)
        db.commit()
        db.refresh(p2)

        v2 = models.ProductVariant(
            product_id=p2.id,
            color="أزرق",
            stock=20,
            price_override=8000.0
        )
        db.add(v2)
        db.commit()

        # Fetch alerts
        res = client.get("/api/admin/inventory/alerts", headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert "low_stock_count" in data
        assert "stagnant_weekly_count" in data
        assert "stagnant_monthly_count" in data

        # Product 1 should be in low stock list (stock <= 5)
        low_stock_ids = [item["id"] for item in data["low_stock_items"]]
        assert p1.id in low_stock_ids
    finally:
        db.close()

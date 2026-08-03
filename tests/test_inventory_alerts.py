import pytest
from datetime import datetime, timedelta
from backend import models, auth
from tests.conftest import TestingSessionLocal

def get_or_create_admin_headers(db):
    admin = db.query(models.User).filter(models.User.email == "inv_admin_test@sheland.com").first()
    if not admin:
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
    return {"Authorization": f"Bearer {token}"}

def test_inventory_alerts_endpoint(client):
    db = TestingSessionLocal()
    try:
        headers = get_or_create_admin_headers(db)

        # Product 1: Low stock (stock = 3)
        p1 = models.Product(
            seller_id=1,
            title_ar="منتج منخفض المخزون",
            title_en="Low Stock Item",
            slug=f"low-stock-item-{Date_now_slug()}",
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
            slug=f"high-sales-item-{Date_now_slug()}",
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

        low_stock_ids = [item["id"] for item in data["low_stock_items"]]
        assert p1.id in low_stock_ids
    finally:
        db.close()


def Date_now_slug():
    import time
    return int(time.time() * 1000)


def test_stagnant_inventory_weekly_and_monthly(client):
    db = TestingSessionLocal()
    try:
        headers = get_or_create_admin_headers(db)
        now = datetime.utcnow()

        # Stagnant Weekly Product (created 10 days ago, no sales)
        p_weekly = models.Product(
            seller_id=1,
            title_ar="منتج راكد أسبوعي",
            title_en="Weekly Stagnant Item",
            slug=f"weekly-stag-{Date_now_slug()}",
            price=5000.0,
            category_id=1,
            created_at=now - timedelta(days=10),
            image_url="http://example.com/weekly.jpg"
        )
        db.add(p_weekly)
        db.commit()
        db.refresh(p_weekly)
        db.add(models.ProductVariant(product_id=p_weekly.id, stock=15))

        # Stagnant Monthly Product (created 40 days ago, no sales)
        p_monthly = models.Product(
            seller_id=1,
            title_ar="منتج راكد شهري",
            title_en="Monthly Stagnant Item",
            slug=f"monthly-stag-{Date_now_slug()}",
            price=9000.0,
            category_id=1,
            created_at=now - timedelta(days=40),
            image_url="http://example.com/monthly.jpg"
        )
        db.add(p_monthly)
        db.commit()
        db.refresh(p_monthly)
        db.add(models.ProductVariant(product_id=p_monthly.id, stock=25))
        db.commit()

        res = client.get("/api/admin/inventory/alerts", headers=headers)
        assert res.status_code == 200
        data = res.json()

        weekly_ids = [item["id"] for item in data["stagnant_weekly_items"]]
        monthly_ids = [item["id"] for item in data["stagnant_monthly_items"]]

        assert p_weekly.id in weekly_ids
        assert p_monthly.id in monthly_ids
    finally:
        db.close()


def test_cancelled_orders_do_not_prevent_stagnancy_alert(client):
    db = TestingSessionLocal()
    try:
        headers = get_or_create_admin_headers(db)
        now = datetime.utcnow()

        p_cancelled = models.Product(
            seller_id=1,
            title_ar="منتج بطلب ملغي",
            title_en="Cancelled Order Item",
            slug=f"cancelled-stag-{Date_now_slug()}",
            price=4500.0,
            category_id=1,
            created_at=now - timedelta(days=35),
            image_url="http://example.com/canc.jpg"
        )
        db.add(p_cancelled)
        db.commit()
        db.refresh(p_cancelled)
        db.add(models.ProductVariant(product_id=p_cancelled.id, stock=10))

        # Create a cancelled order yesterday
        canc_order = models.Order(
            order_number=f"ORD-CANC-{Date_now_slug()}",
            customer_name="عميل اختبار",
            phone="0770000000",
            shipping_address="صنعاء",
            total_amount=4500.0,
            payment_method="COD",
            status="ملغي",
            created_at=now - timedelta(days=1)
        )
        db.add(canc_order)
        db.commit()
        db.refresh(canc_order)

        db.add(models.OrderItem(
            order_id=canc_order.id,
            product_id=p_cancelled.id,
            quantity=1,
            price=4500.0
        ))
        db.commit()

        res = client.get("/api/admin/inventory/alerts", headers=headers)
        assert res.status_code == 200
        data = res.json()

        monthly_ids = [item["id"] for item in data["stagnant_monthly_items"]]
        assert p_cancelled.id in monthly_ids
    finally:
        db.close()


def test_inventory_alerts_rbac(client):
    # Unauthenticated -> 401
    res = client.get("/api/admin/inventory/alerts")
    assert res.status_code == 401

    # Customer -> 403
    db = TestingSessionLocal()
    try:
        cust = models.User(
            name="عميل زبون",
            email=f"cust_{Date_now_slug()}@sheland.com",
            phone="07799887766",
            password_hash=auth.hash_password("cust123"),
            role="customer"
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)

        token = auth.create_access_token({"sub": str(cust.id), "role": cust.role})
        cust_headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/admin/inventory/alerts", headers=cust_headers)
        assert res.status_code == 403
    finally:
        db.close()

"""
CityLand Backend - Unit & Integration Tests for Orders Lifecycle & Tracking
# ponytail: Compact test suite validating order status transitions, parcel details, customer isolation, and stock validations.
"""
import pytest
from tests.conftest import TestingSessionLocal
from backend import auth, models

def create_user_token(name: str, email: str, role: str) -> tuple[int, str]:
    """Helper to create user in DB and return (user_id, JWT token)."""
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            name=name,
            email=email,
            phone="0771112233",
            password_hash=auth.hash_password("password123"),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = user.id
    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    db.close()
    return user_id, token


def test_order_status_transitions(client):
    """Ensure authorized admin/sales manager can update order lifecycle status."""
    db = TestingSessionLocal()
    order = models.Order(
        order_number="ORD-STAT-001",
        customer_name="عميل اختبار الحالات",
        phone="771111222",
        shipping_address="صنعاء",
        payment_method="COD",
        total_amount=5000.0,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    order_id = order.id
    db.close()

    _, admin_token = create_user_token("مدير المبيعات", "sales_ord@sheland.com", "sales_manager")
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Transition 1: pending -> processing
    res1 = client.put(f"/api/orders/{order_id}/status?status=processing", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["new_status"] == "processing"

    # Transition 2: processing -> shipped
    res2 = client.put(f"/api/orders/{order_id}/status?status=shipped", headers=headers)
    assert res2.status_code == 200
    assert res2.json()["new_status"] == "shipped"

    # Transition 3: shipped -> delivered
    res3 = client.put(f"/api/orders/{order_id}/status?status=delivered", headers=headers)
    assert res3.status_code == 200
    assert res3.json()["new_status"] == "delivered"


def test_invalid_order_status_transition_rejected(client):
    """Ensure non-existent order or unauthorized user fails on status update."""
    _, customer_token = create_user_token("عميل عادي", "customer_ord@sheland.com", "customer")
    cust_headers = {
        "Authorization": f"Bearer {customer_token}",
        "X-Requested-With": "XMLHttpRequest"
    }
    # Customer should be forbidden (403)
    res_forbidden = client.put("/api/orders/1/status?status=shipped", headers=cust_headers)
    assert res_forbidden.status_code == 403

    _, admin_token = create_user_token("الأدمن", "admin_ord@sheland.com", "admin")
    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Requested-With": "XMLHttpRequest"
    }
    # Non-existent order should return 404
    res_notfound = client.put("/api/orders/999999/status?status=shipped", headers=admin_headers)
    assert res_notfound.status_code == 404


def test_update_parcel_tracking_details(client):
    """Ensure admin/sales manager can set parcel weight, count, and dimensions."""
    db = TestingSessionLocal()
    order = models.Order(
        order_number="ORD-PARCEL-001",
        customer_name="عميل الطرد",
        phone="771111222",
        shipping_address="عدن",
        payment_method="COD",
        total_amount=12000.0,
        status="processing"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    order_id = order.id
    db.close()

    _, admin_token = create_user_token("الأدمن", "admin_parcel@sheland.com", "admin")
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "parcel_count": "2 من 2",
        "weight": "3.5 كجم",
        "dimensions": "30 × 20 × 15 سم"
    }
    res = client.put(f"/api/orders/{order_id}/parcel-details", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["parcel_count"] == "2 من 2"
    assert data["weight"] == "3.5 كجم"
    assert data["dimensions"] == "30 × 20 × 15 سم"


def test_customer_orders_isolation(client):
    """Ensure customer A only sees customer A's orders, and customer B cannot see them."""
    user_a_id, token_a = create_user_token("العميل أ", "user_a@sheland.com", "customer")
    user_b_id, token_b = create_user_token("العميل ب", "user_b@sheland.com", "customer")

    db = TestingSessionLocal()
    order_a = models.Order(
        order_number="ORD-USER-A",
        user_id=user_a_id,
        customer_name="العميل أ",
        phone="771111222",
        shipping_address="تعز",
        payment_method="COD",
        total_amount=8000.0
    )
    order_b = models.Order(
        order_number="ORD-USER-B",
        user_id=user_b_id,
        customer_name="العميل ب",
        phone="772222333",
        shipping_address="إب",
        payment_method="COD",
        total_amount=14000.0
    )
    db.add_all([order_a, order_b])
    db.commit()
    db.close()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    res_a = client.get("/api/orders/my", headers=headers_a)
    assert res_a.status_code == 200
    orders_a = res_a.json()
    assert len(orders_a) == 1
    assert orders_a[0]["order_number"] == "ORD-USER-A"

    res_b = client.get("/api/orders/my", headers=headers_b)
    assert res_b.status_code == 200
    orders_b = res_b.json()
    assert len(orders_b) == 1
    assert orders_b[0]["order_number"] == "ORD-USER-B"

    # Also test track order isolation: Customer B tracking Customer A's order should return 403 Forbidden
    res_track = client.get("/api/orders/track/ORD-USER-A", headers=headers_b)
    assert res_track.status_code == 403


def test_order_creation_out_of_stock_rejected(client):
    """Ensure order creation is rejected with 422 if requested quantity exceeds available stock."""
    db = TestingSessionLocal()
    seller = db.query(models.Seller).first()
    if not seller:
        user = models.User(name="تاجر فرعي", email="seller_sub@sheland.com", phone="077999888", password_hash="123", role="seller")
        db.add(user)
        db.commit()
        db.refresh(user)
        seller = models.Seller(user_id=user.id, store_name="متجر التجزئة")
        db.add(seller)
        db.commit()
        db.refresh(seller)

    cat = models.Category(name_ar="الكترونيات", name_en="Electronics", slug="elec-stock")
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = models.Product(
        seller_id=seller.id,
        category_id=cat.id,
        title_ar="منتج محدود المخزون",
        title_en="Limited Stock Product",
        slug="limited-prod",
        price=1000.0,
        image_url="https://example.com/img.jpg"
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    variant = models.ProductVariant(product_id=prod.id, stock=2)
    db.add(variant)
    db.commit()

    prod_id = prod.id
    db.close()

    payload = {
        "items": [
            {"product_id": prod_id, "quantity": 10}
        ],
        "customer_name": "عميل كمية زايدة",
        "phone": "770000000",
        "shipping_address": "المكلا",
        "payment_method": "COD"
    }
    headers = {"X-Requested-With": "XMLHttpRequest"}

    res = client.post("/api/orders", json=payload, headers=headers)
    assert res.status_code == 422
    assert "نقص في المخزون" in res.json()["detail"]

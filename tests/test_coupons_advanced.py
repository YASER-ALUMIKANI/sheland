"""
CityLand Backend - Unit & Integration Tests for Advanced Coupon Validation & Management
# ponytail: Compact test suite validating percent/fixed coupons, minimum spend requirements, duplicate creation checks, RBAC, and coupon deletion.
"""
import pytest
from tests.conftest import TestingSessionLocal
from backend import auth, models

def create_user_token(name: str, email: str, role: str) -> str:
    """Helper to create user in DB and return JWT bearer token."""
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            name=name,
            email=email,
            phone="0773334444",
            password_hash=auth.hash_password("password123"),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    db.close()
    return token


def test_validate_valid_percent_and_fixed_coupon(client):
    """Ensure active percentage and fixed discount coupons compute correct discount amounts."""
    db = TestingSessionLocal()
    c_percent = models.Coupon(code="EID2026", discount_type="percent", discount_value=15.0, min_order_amount=5000.0, is_active=True)
    c_fixed = models.Coupon(code="FLAT2000", discount_type="fixed", discount_value=2000.0, min_order_amount=10000.0, is_active=True)
    db.add_all([c_percent, c_fixed])
    db.commit()
    db.close()

    # 1. Percent coupon validation (15% of 10000 = 1500)
    res_p = client.get("/api/coupons/validate?code=eid2026&total=10000")
    assert res_p.status_code == 200
    data_p = res_p.json()
    assert data_p["valid"] is True
    assert data_p["code"] == "EID2026"
    assert data_p["discount_amount"] == 1500.0

    # 2. Fixed coupon validation (2000 off)
    res_f = client.post("/api/coupons/validate?code=FLAT2000&total=15000")
    assert res_f.status_code == 200
    data_f = res_f.json()
    assert data_f["valid"] is True
    assert data_f["discount_amount"] == 2000.0


def test_inactive_or_invalid_coupon_rejected(client):
    """Ensure inactive or non-existent coupon codes return 404 Not Found."""
    db = TestingSessionLocal()
    c_inactive = models.Coupon(code="EXPIRED50", discount_type="percent", discount_value=50.0, min_order_amount=0.0, is_active=False)
    db.add(c_inactive)
    db.commit()
    db.close()

    # Inactive coupon
    res1 = client.get("/api/coupons/validate?code=EXPIRED50&total=10000")
    assert res1.status_code == 404

    # Non-existent coupon
    res2 = client.get("/api/coupons/validate?code=NOCODE123&total=10000")
    assert res2.status_code == 404


def test_coupon_below_min_purchase_rejected(client):
    """Ensure coupon application is rejected with 400 if order total is below minimum requirement."""
    db = TestingSessionLocal()
    coupon = models.Coupon(code="VIPMIN5000", discount_type="fixed", discount_value=1000.0, min_order_amount=5000.0, is_active=True)
    db.add(coupon)
    db.commit()
    db.close()

    res = client.get("/api/coupons/validate?code=VIPMIN5000&total=3000")
    assert res.status_code == 400
    assert "يتطلب أدنى قيمة طلب" in res.json()["detail"]


def test_duplicate_coupon_code_creation_rejected(client):
    """Ensure admin cannot create a duplicate coupon code (409 Conflict)."""
    admin_token = create_user_token("الأدمن", "admin_coupon@sheland.com", "admin")
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "code": "SUMMER10",
        "discount_type": "percent",
        "discount_value": 10.0,
        "min_order_amount": 1000.0
    }

    # First creation -> 201 Created
    res1 = client.post("/api/coupons", json=payload, headers=headers)
    assert res1.status_code == 201

    # Second creation with same code -> 409 Conflict
    res2 = client.post("/api/coupons", json=payload, headers=headers)
    assert res2.status_code == 409
    assert "موجود مسبقاً" in res2.json()["detail"]


def test_admin_create_and_delete_coupon(client):
    """Ensure authorized admin can create and delete coupons, while non-admin users are blocked."""
    customer_token = create_user_token("عميل 1", "customer_coup@sheland.com", "customer")
    admin_token = create_user_token("الأدمن", "admin_del_coup@sheland.com", "admin")

    cust_headers = {"Authorization": f"Bearer {customer_token}", "X-Requested-With": "XMLHttpRequest"}
    admin_headers = {"Authorization": f"Bearer {admin_token}", "X-Requested-With": "XMLHttpRequest"}

    payload = {
        "code": "FLASH50",
        "discount_type": "percent",
        "discount_value": 50.0,
        "min_order_amount": 0.0
    }

    # Customer creation attempt blocked (403)
    res_cust = client.post("/api/coupons", json=payload, headers=cust_headers)
    assert res_cust.status_code == 403

    # Admin creation success (201)
    res_admin = client.post("/api/coupons", json=payload, headers=admin_headers)
    assert res_admin.status_code == 201
    coupon_id = res_admin.json()["id"]

    # Customer deletion attempt blocked (403)
    res_del_cust = client.delete(f"/api/coupons/{coupon_id}", headers=cust_headers)
    assert res_del_cust.status_code == 403

    # Admin deletion success (204)
    res_del_admin = client.delete(f"/api/coupons/{coupon_id}", headers=admin_headers)
    assert res_del_admin.status_code == 204

    # Verification: Coupon deleted from list
    all_coupons = client.get("/api/coupons").json()
    ids = [c["id"] for c in all_coupons]
    assert coupon_id not in ids


def test_coupon_max_uses_exceeded_rejected(client):
    """Ensure coupon application is rejected with 400 if max_uses limit has been reached or exceeded."""
    db = TestingSessionLocal()
    coupon = models.Coupon(
        code="LIMITED100",
        discount_type="fixed",
        discount_value=500.0,
        min_order_amount=1000.0,
        max_uses=3,
        used_count=3,  # Limit reached
        is_active=True
    )
    db.add(coupon)
    db.commit()
    db.close()

    res = client.get("/api/coupons/validate?code=LIMITED100&total=5000")
    assert res.status_code == 400
    assert "الحد الأقصى" in res.json()["detail"]


def test_coupon_expired_date_rejected(client):
    """Ensure coupon application is rejected with 400 if the expiration date has passed."""
    from datetime import datetime, timedelta
    db = TestingSessionLocal()
    past_date = datetime.utcnow() - timedelta(days=1)
    coupon = models.Coupon(
        code="EXPIRED2025",
        discount_type="percent",
        discount_value=20.0,
        min_order_amount=0.0,
        expires_at=past_date,
        is_active=True
    )
    db.add(coupon)
    db.commit()
    db.close()

    res = client.get("/api/coupons/validate?code=EXPIRED2025&total=5000")
    assert res.status_code == 400
    assert "منتهي الصلاحية" in res.json()["detail"]



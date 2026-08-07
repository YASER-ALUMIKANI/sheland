"""
CityLand Backend - Unit & Integration Tests for Payment Methods & Security
# ponytail: Concise tests validating active payment methods retrieval, admin CRUD, RBAC, payment status verification, and customer transaction verification.
"""
import pytest
from tests.conftest import TestingSessionLocal
from backend import auth, models, schemas

def create_user_token(name: str, email: str, role: str) -> str:
    """Helper to create user and generate JWT bearer token."""
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            name=name,
            email=email,
            phone="0770000001",
            password_hash=auth.hash_password("password123"),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    db.close()
    return token


def test_get_active_payment_methods(client):
    """Ensure public endpoint returns active payment methods list for checkout."""
    response = client.get("/api/payments/methods")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    ids = [item.get("id") for item in data]
    assert len(ids) > 0
    assert "cod" in ids or "kuraimi" in ids


def test_admin_create_and_update_payment_method(client):
    """Ensure admin can create, update, and delete a custom digital wallet or payment method."""
    admin_token = create_user_token("مدير الدفع", "admin_pm@sheland.com", "admin")
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Requested-With": "XMLHttpRequest"
    }

    # 1. Create new payment method
    pm_payload = {
        "id": "jawali_test",
        "name_ar": "محفظة جوالي للاختبار",
        "name_en": "Jawali Test Wallet",
        "account_number": "777123456",
        "account_name": "شركة شي لاند",
        "instructions": "قم بتحويل المبلغ إلى رقم المحفظة",
        "icon": "📱",
        "type": "wallet",
        "is_active": True
    }
    create_res = client.post("/api/admin/payments", json=pm_payload, headers=headers)
    assert create_res.status_code == 200
    created_data = create_res.json()
    assert created_data["id"] == "jawali_test"
    assert created_data["name_ar"] == "محفظة جوالي للاختبار"

    # 2. Duplicate creation attempt should be rejected (400 Bad Request)
    dup_res = client.post("/api/admin/payments", json=pm_payload, headers=headers)
    assert dup_res.status_code == 400

    # 3. Update payment method
    update_payload = {
        "id": "jawali_test",
        "name_ar": "محفظة جوالي المحدثة",
        "name_en": "Updated Jawali Wallet",
        "account_number": "777999888",
        "account_name": "شركة شي لاند",
        "instructions": "تعليمات محدثة",
        "icon": "📲",
        "type": "wallet",
        "is_active": False
    }
    update_res = client.put("/api/admin/payments/jawali_test", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["name_ar"] == "محفظة جوالي المحدثة"
    assert update_res.json()["is_active"] is False

    # 4. Delete payment method
    delete_res = client.delete("/api/admin/payments/jawali_test", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "success"


def test_non_admin_cannot_manage_payment_methods(client):
    """Ensure non-admin users (customers and sellers) are forbidden from managing payment methods."""
    customer_token = create_user_token("عميل 1", "customer_pm@sheland.com", "customer")
    headers = {
        "Authorization": f"Bearer {customer_token}",
        "X-Requested-With": "XMLHttpRequest"
    }
    pm_payload = {
        "id": "unauth_pm",
        "name_ar": "محفظة غير مخولة",
        "name_en": "Unauth Wallet",
        "account_number": "123",
        "account_name": "Test",
        "instructions": "Test",
        "is_active": True
    }

    # Customer attempt
    res = client.post("/api/admin/payments", json=pm_payload, headers=headers)
    assert res.status_code == 403

    # Seller attempt
    seller_token = create_user_token("تاجر 1", "seller_pm@sheland.com", "seller")
    seller_headers = {
        "Authorization": f"Bearer {seller_token}",
        "X-Requested-With": "XMLHttpRequest"
    }
    res_seller = client.post("/api/admin/payments", json=pm_payload, headers=seller_headers)
    assert res_seller.status_code == 403


def test_admin_verify_order_payment_status(client):
    """Ensure admin/sales manager can update payment verification status of an order."""
    db = TestingSessionLocal()
    order = models.Order(
        order_number="ORD-PAY-001",
        customer_name="عميل اختبار الدفع",
        phone="771111222",
        shipping_address="صنعاء",
        total_amount=15000.0,
        payment_method="kuraimi",
        payment_status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    order_id = order.id
    db.close()

    token = create_user_token("مدير المبيعات", "sales_pm@sheland.com", "sales_manager")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Requested-With": "XMLHttpRequest"
    }
    payload = {
        "payment_status": "paid",
        "payment_tx_id": "TXN-99887766"
    }

    res = client.put(f"/api/admin/orders/{order_id}/verify-payment", json=payload, headers=headers)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "success"
    assert res_data["payment_status"] == "paid"
    assert res_data["payment_tx_id"] == "TXN-99887766"


def test_customer_submit_payment_verification_reference(client):
    """Ensure customer payment reference verification endpoint processes transaction info."""
    payload = {
        "method": "kuraimi",
        "tx_id": "REF-12345678",
        "amount": 25000.0
    }
    res = client.post("/api/payments/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "status" in data

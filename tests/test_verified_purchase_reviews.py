"""
CityLand Backend - Unit Tests for Automated Verified Purchase Product Reviews
# ponytail: Clean, comprehensive test suite for automated buyer verification
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend import auth, models
from tests.conftest import TestingSessionLocal

client = TestClient(app)

def create_user(db, name="Verified Buyer", phone="0771112233", email="buyer@test.com", role="customer"):
    user = models.User(name=name, phone=phone, email=email, password_hash="hashed_pw", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_product(db, title="اختبار منتج ممتاز", price=10000.0):
    # Ensure a category exists first
    cat = db.query(models.Category).filter(models.Category.slug == "test-cat-rev").first()
    if not cat:
        cat = models.Category(name_ar="قسم الاختبار", name_en="Test Category", slug="test-cat-rev")
        db.add(cat)
        db.commit()
        db.refresh(cat)

    import secrets
    seller_user = create_user(db, name="تاجر خبير", phone=f"077{secrets.randbelow(8999999)+1000000}", email=f"seller_{secrets.token_hex(4)}@test.com", role="seller")
    seller = models.Seller(user_id=seller_user.id, store_name="متجر التقييمات")
    db.add(seller)
    db.commit()
    db.refresh(seller)

    prod = models.Product(
        seller_id=seller.id,
        category_id=cat.id,
        title_ar=title,
        title_en="Test Product",
        slug=f"test-prod-rev-{seller.id}-{hash(title)%10000}",
        description="وصف المنتج",
        price=price,
        image_url="http://example.com/test.jpg",
        rating=0.0,
        review_count=0
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

def create_order(db, user_id, product_id, order_number="ORD-REV-1001", status="delivered"):
    order = models.Order(
        order_number=order_number,
        user_id=user_id,
        customer_name="العميل المشتري",
        phone="0771112233",
        shipping_address="مدينة البيضاء",
        payment_method="COD",
        status=status,
        total_amount=10000.0
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    item = models.OrderItem(
        order_id=order.id,
        product_id=product_id,
        quantity=1,
        price=10000.0
    )
    db.add(item)
    db.commit()
    return order


def test_unauthenticated_review_creation_rejected():
    """Unauthenticated POST to product review must be rejected (401)."""
    payload = {
        "rating": 5,
        "comment": "تقييم بدون تسجيل دخول"
    }
    response = client.post("/api/products/1/reviews", json=payload)
    assert response.status_code == 401


def test_review_creation_for_user_without_purchase_rejected():
    """User who hasn't purchased the product must be rejected with 403."""
    db = TestingSessionLocal()
    user = create_user(db, email="nobuyer@test.com", phone="0770000001")
    prod = create_product(db)
    prod_id = prod.id
    token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})
    db.close()

    payload = {
        "rating": 5,
        "comment": "تقييم بدون شراء سابق"
    }
    response = client.post(
        f"/api/products/{prod_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    assert response.status_code == 403
    assert "يمكنك إضافة تقييم فقط للمنتجات التي قمت بشرائها" in response.json()["detail"]


def test_review_creation_for_undelivered_order_rejected():
    """Reviewing a product in an order with status='pending' must return 400."""
    db = TestingSessionLocal()
    user = create_user(db, email="user_pending@test.com", phone="0770000004")
    prod = create_product(db)
    prod_id = prod.id
    create_order(db, user_id=user.id, product_id=prod_id, order_number="ORD-PENDING-01", status="pending")
    token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})
    db.close()

    payload = {
        "rating": 5,
        "comment": "تقييم لطلب قيد الانتظار لم يُستلم بعد"
    }
    response = client.post(
        f"/api/products/{prod_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    assert response.status_code == 400
    assert "بعد استلام الطلب" in response.json()["detail"]


def test_valid_automated_verified_buyer_review_success():
    """Authenticated buyer with delivered order automatically matches order and marks review verified."""
    db = TestingSessionLocal()
    user = create_user(db, email="valid_buyer@test.com", phone="0770000005")
    prod = create_product(db)
    prod_id = prod.id
    create_order(db, user_id=user.id, product_id=prod_id, order_number="ORD-DELIVERED-88", status="delivered")
    token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})

    payload = {
        "rating": 5,
        "comment": "منتج ممتاز والتحقق الآلي عمل بنجاح!"
    }
    response = client.post(
        f"/api/products/{prod_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["rating"] == 5
    assert res_data["is_verified_purchase"] is True

    # Check database persistence
    db.refresh(prod)
    assert prod.rating == 5.0
    assert prod.review_count == 1
    db.close()

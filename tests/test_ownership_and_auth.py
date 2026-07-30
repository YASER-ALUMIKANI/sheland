import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend import auth, models
from tests.conftest import TestingSessionLocal

client = TestClient(app)

@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def create_test_seller_with_product(db, phone="0775544332", store_name="Seller A Store"):
    user = models.User(name=store_name, phone=phone, email=f"{phone}@seller.com", password_hash=auth.hash_password("password123"), role="seller")
    db.add(user)
    db.commit()
    db.refresh(user)

    seller = models.Seller(user_id=user.id, store_name=store_name)
    db.add(seller)
    db.commit()
    db.refresh(seller)

    cat = models.Category(name_ar="ملابس", name_en="Clothing", slug=f"cat-{user.id}")
    db.add(cat)
    db.commit()
    db.refresh(cat)

    prod = models.Product(
        seller_id=seller.id,
        category_id=cat.id,
        title_ar="قميص رجالي",
        title_en="Shirt",
        slug=f"shirt-{seller.id}",
        price=100.0,
        image_url="/uploads/shirt.jpg"
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)

    return user, seller, prod

def test_password_plaintext_fallback_removed():
    """Ensure plain text password fallback is completely removed in verify_password."""
    plaintext = "admin123"
    # When stored hash is plaintext "admin123" (not bcrypt), verify_password must return False
    assert auth.verify_password("admin123", "admin123") is False

def test_product_update_ownership_enforcement(db):
    """Ensure seller A cannot modify seller B's product (403 Forbidden)."""
    user_a, seller_a, prod_a = create_test_seller_with_product(db, phone="0775544331", store_name="Seller A")
    user_b, seller_b, prod_b = create_test_seller_with_product(db, phone="0775544332", store_name="Seller B")

    token_a = auth.create_access_token(data={"sub": str(user_a.id), "role": user_a.role})

    # Seller A tries to update Seller B's product (prod_b)
    update_payload = {
        "seller_id": seller_b.id,
        "category_id": prod_b.category_id,
        "title_ar": "تم اختراق المنتج",
        "title_en": "Hacked",
        "slug": prod_b.slug,
        "price": 1.0,
        "image_url": prod_b.image_url
    }

    response = client.put(f"/api/products/{prod_b.id}", headers={"Authorization": f"Bearer {token_a}"}, json=update_payload)
    assert response.status_code == 403
    assert "ليس لديك صلاحية تعديل هذا المنتج" in response.json()["detail"]

def test_product_owner_can_update_product(db):
    """Ensure seller can update their own product (200 OK)."""
    user_a, seller_a, prod_a = create_test_seller_with_product(db, phone="0775544333", store_name="Seller Owner")
    token_a = auth.create_access_token(data={"sub": str(user_a.id), "role": user_a.role})

    update_payload = {
        "seller_id": seller_a.id,
        "category_id": prod_a.category_id,
        "title_ar": "قميص معدل",
        "title_en": "Updated Shirt",
        "slug": prod_a.slug,
        "price": 120.0,
        "image_url": prod_a.image_url
    }

    response = client.put(f"/api/products/{prod_a.id}", headers={"Authorization": f"Bearer {token_a}"}, json=update_payload)
    assert response.status_code == 200
    assert response.json()["title_ar"] == "قميص معدل"

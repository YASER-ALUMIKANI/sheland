"""
CityLand Backend - Seller Management & Authorization Tests
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import TestingSessionLocal
from backend import models, auth


def test_register_seller_creates_seller_profile(client: TestClient):
    """Verifies that registering a user with role='seller' automatically creates a corresponding Seller record."""
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "التاجر الجديد",
            "email": "new_seller@sheland.com",
            "phone": "967770007788",
            "password": "SellerPassword123",
            "role": "seller"
        }
    )
    assert reg.status_code == 201
    user_id = reg.json()["user"]["id"]

    db = TestingSessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        assert user is not None
        assert user.role == "seller"

        seller = db.query(models.Seller).filter(models.Seller.user_id == user_id).first()
        assert seller is not None
        assert seller.store_name == "متجر التاجر الجديد"
    finally:
        db.close()


def test_seller_can_update_own_product(client: TestClient):
    """Verifies that a seller can successfully update their own product."""
    db = TestingSessionLocal()
    try:
        user = models.User(name="Seller One", email="seller_one@example.com", phone="967771111111", password_hash=auth.hash_password("Password123"), role="seller")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

        seller = models.Seller(user_id=user.id, store_name="متجر البائع الأول")
        db.add(seller)
        db.commit()
        db.refresh(seller)

        cat = models.Category(name_ar="الكترونيات", name_en="Tech", slug="tech-cat-1")
        db.add(cat)
        db.commit()
        db.refresh(cat)

        prod = models.Product(
            seller_id=seller.id,
            category_id=cat.id,
            title_ar="شاحن سريع",
            title_en="Fast Charger",
            slug="fast-charger-1",
            price=50.0,
            image_url="/uploads/charger.jpg"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        prod_id = prod.id
        seller_id = seller.id
        category_id = cat.id
    finally:
        db.close()

    token = auth.create_access_token({"sub": str(user_id), "role": "seller"})
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "seller_id": seller_id,
        "category_id": category_id,
        "title_ar": "شاحن سريع 65 واط",
        "title_en": "Fast Charger 65W",
        "slug": "fast-charger-65w",
        "price": 75.0,
        "image_url": "/uploads/charger65w.jpg"
    }

    resp = client.put(f"/api/products/{prod_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title_ar"] == "شاحن سريع 65 واط"
    assert resp.json()["price"] == 75.0


def test_seller_cannot_delete_another_sellers_product(client: TestClient):
    """Verifies that a seller cannot update or delete another seller's product (403 Forbidden)."""
    db = TestingSessionLocal()
    try:
        user_a = models.User(name="Seller A", email="seller_a@example.com", phone="967772222222", password_hash=auth.hash_password("Password123"), role="seller")
        user_b = models.User(name="Seller B", email="seller_b@example.com", phone="967773333333", password_hash=auth.hash_password("Password123"), role="seller")
        db.add_all([user_a, user_b])
        db.commit()
        user_a_id = user_a.id

        seller_a = models.Seller(user_id=user_a.id, store_name="متجر أ")
        seller_b = models.Seller(user_id=user_b.id, store_name="متجر ب")
        db.add_all([seller_a, seller_b])
        db.commit()

        cat = models.Category(name_ar="أدوات", name_en="Tools", slug="tools-cat-1")
        db.add(cat)
        db.commit()

        prod_b = models.Product(
            seller_id=seller_b.id,
            category_id=cat.id,
            title_ar="منتج التاجر ب",
            title_en="Seller B Product",
            slug="prod-b-1",
            price=100.0,
            image_url="/uploads/item.jpg"
        )
        db.add(prod_b)
        db.commit()
        db_prod_b_id = prod_b.id
        db_seller_b_id = seller_b.id
        db_cat_id = cat.id
    finally:
        db.close()

    token_a = auth.create_access_token({"sub": str(user_a_id), "role": "seller"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    update_payload = {
        "seller_id": db_seller_b_id,
        "category_id": db_cat_id,
        "title_ar": "تغيير غير مصرح",
        "title_en": "Unauthorized Change",
        "slug": "prod-b-1",
        "price": 1.0,
        "image_url": "/uploads/item.jpg"
    }

    resp = client.put(f"/api/products/{db_prod_b_id}", json=update_payload, headers=headers_a)
    assert resp.status_code == 403

    del_resp = client.delete(f"/api/products/{db_prod_b_id}", headers=headers_a)
    assert del_resp.status_code == 403



def test_seller_cannot_view_all_orders(client: TestClient):
    """Verifies that a seller user cannot access the admin orders endpoint GET /api/orders (403 Forbidden)."""
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "تاجر محظور",
            "email": "restricted_seller@sheland.com",
            "phone": "967770009900",
            "password": "Password123",
            "role": "seller"
        }
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    resp = client.get("/api/orders", headers=headers)
    assert resp.status_code == 403

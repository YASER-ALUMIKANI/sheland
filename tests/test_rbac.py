"""
CityLand Backend - Unit & Integration Tests for Role-Based Access Control (RBAC)
# ponytail: Clean, compact test suite validating RBAC endpoint authorization rules
"""
import pytest
from tests.conftest import TestingSessionLocal
from backend import auth, models

def create_user_and_get_token(name: str, email: str, role: str) -> str:
    """Helper to create a user in DB and return JWT bearer token."""
    db = TestingSessionLocal()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            name=name,
            email=email,
            phone="0770000000",
            password_hash=auth.hash_password("password123"),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    if role == "seller":
        seller = db.query(models.Seller).filter(models.Seller.user_id == user.id).first()
        if not seller:
            seller = models.Seller(user_id=user.id, store_name=f"متجر {name}")
            db.add(seller)
            db.commit()

    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    db.close()
    return token


# --- 1. Unauthenticated Tests ---
def test_unauthenticated_admin_analytics(client):
    response = client.get("/api/admin/analytics")
    assert response.status_code == 401

def test_unauthenticated_create_product(client):
    payload = {
        "title_ar": "منتج خفي",
        "title_en": "Hidden Product",
        "slug": "hidden-prod",
        "price": 5000,
        "image_url": "https://example.com/img.jpg",
        "category_id": 1
    }
    response = client.post("/api/products", json=payload)
    assert response.status_code == 401


# --- 2. Customer Role Tests ---
def test_customer_forbidden_on_admin_analytics(client):
    token = create_user_and_get_token("عميل 1", "customer1@sheland.com", "customer")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/admin/analytics", headers=headers)
    assert response.status_code == 403

def test_customer_forbidden_on_create_product(client):
    token = create_user_and_get_token("عميل 2", "customer2@sheland.com", "customer")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title_ar": "منتج عميل",
        "title_en": "Customer Product",
        "slug": "cust-prod",
        "price": 5000,
        "image_url": "https://example.com/img.jpg",
        "category_id": 1
    }
    response = client.post("/api/products", json=payload, headers=headers)
    assert response.status_code == 403


# --- 3. Seller Role Tests ---
def test_seller_can_create_product(client):
    db = TestingSessionLocal()
    cat = db.query(models.Category).filter(models.Category.id == 1).first()
    if not cat:
        cat = models.Category(id=1, name_ar="نساء", name_en="Women", slug="women-rbac-1")
        db.add(cat)
        db.commit()
    db.close()

    token = create_user_and_get_token("تاجر 1", "seller1@sheland.com", "seller")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title_ar": "فستان سهرة راقي",
        "title_en": "Evening Dress",
        "slug": "evening-dress",
        "price": 18000,
        "image_url": "https://example.com/dress.jpg",
        "category_id": 1,
        "seller_id": 1
    }
    response = client.post("/api/products", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["title_ar"] == "فستان سهرة راقي"

def test_seller_forbidden_on_admin_analytics(client):
    token = create_user_and_get_token("تاجر 2", "seller2@sheland.com", "seller")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/admin/analytics", headers=headers)
    assert response.status_code == 403


# --- 4. Sales Manager Role Tests ---
def test_sales_manager_can_access_admin_analytics(client):
    token = create_user_and_get_token("مدير مبيعات", "sales@sheland.com", "sales_manager")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/admin/analytics", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert "finance" in res_data


# --- 5. Admin & Super Admin Role Tests ---
def test_admin_can_access_analytics_and_delete_product(client):
    db = TestingSessionLocal()
    cat = db.query(models.Category).filter(models.Category.id == 1).first()
    if not cat:
        cat = models.Category(id=1, name_ar="نساء", name_en="Women", slug="women-rbac-2")
        db.add(cat)
        db.commit()

    seller_user = db.query(models.User).filter(models.User.email == "seller_del_test@sheland.com").first()
    if not seller_user:
        seller_user = models.User(name="S", email="seller_del_test@sheland.com", password_hash="h", role="seller")
        db.add(seller_user)
        db.commit()

    seller = db.query(models.Seller).filter(models.Seller.user_id == seller_user.id).first()
    if not seller:
        seller = models.Seller(user_id=seller_user.id, store_name="S")
        db.add(seller)
        db.commit()

    prod = db.query(models.Product).filter(models.Product.id == 99).first()
    if not prod:
        prod = models.Product(
            id=99,
            seller_id=seller.id,
            category_id=cat.id,
            title_ar="منتج لحذف",
            title_en="Delete Me",
            slug="del-me",
            price=1000,
            image_url="https://example.com/img.jpg"
        )
        db.add(prod)
        db.commit()
    db.close()

    token = create_user_and_get_token("المدير العام", "admin@sheland.com", "admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Analytics check
    res_analytics = client.get("/api/admin/analytics", headers=headers)
    assert res_analytics.status_code == 200

    # Delete product check
    res_del = client.delete("/api/products/99", headers=headers)
    assert res_del.status_code == 200

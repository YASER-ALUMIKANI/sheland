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

def create_test_user(db, name="Test Customer", phone="0771122334", role="customer"):
    user = models.User(name=name, phone=phone, email=f"{phone}@test.com", password_hash="hashed", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_unauthenticated_get_all_orders_rejected():
    """Ensure GET /api/orders without authentication is rejected (401)."""
    response = client.get("/api/orders")
    assert response.status_code == 401

def test_customer_get_all_orders_forbidden(db):
    """Ensure regular customer cannot access all orders list via GET /api/orders (403)."""
    customer = create_test_user(db, name="Customer User", phone="0771122335", role="customer")
    token = auth.create_access_token(data={"sub": str(customer.id), "role": customer.role})
    
    response = client.get("/api/orders", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_admin_get_all_orders_authorized(db):
    """Ensure admin can access orders list via GET /api/orders (200)."""
    admin = create_test_user(db, name="Admin User", phone="0771122336", role="admin")
    token = auth.create_access_token(data={"sub": str(admin.id), "role": admin.role})
    
    response = client.get("/api/orders", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_create_order_jwt_user_binding(db):
    """Ensure POST /api/orders automatically binds order to authenticated user's ID."""
    customer = create_test_user(db, name="Logged In Customer", phone="0771122337", role="customer")
    token = auth.create_access_token(data={"sub": str(customer.id), "role": customer.role})
    
    # Create product & variant
    cat = db.query(models.Category).filter(models.Category.slug == "electronics").first()
    if not cat:
        cat = models.Category(name_ar="الكترونيات اختباري", name_en="Test Electronics", slug="electronics-test")
        db.add(cat)
        db.commit()
        db.refresh(cat)
    
    prod = models.Product(seller_id=1, category_id=cat.id, title_ar="هاتف محمول", title_en="Phone", slug="phone", price=500.0, image_url="/uploads/test.jpg")
    db.add(prod)
    db.commit()
    db.refresh(prod)
    
    variant = models.ProductVariant(product_id=prod.id, sku=f"SKU-{prod.id}", stock=10)
    db.add(variant)
    db.commit()
    
    order_payload = {
        "user_id": 9999,  # Attempting spoofed user_id
        "customer_name": "Logged In Customer",
        "phone": "0771122337",
        "shipping_address": "صنعاء",
        "payment_method": "COD",
        "items": [{"product_id": prod.id, "quantity": 1}]
    }
    
    response = client.post("/api/orders", headers={"Authorization": f"Bearer {token}"}, json=order_payload)
    assert response.status_code == 200
    res_data = response.json()
    # Verified user_id must equal customer.id, NOT spoofed 9999
    assert res_data["user_id"] == customer.id

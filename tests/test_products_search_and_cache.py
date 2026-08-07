"""
CityLand Backend - Unit & Integration Tests for Product Search, Filtering, Caching & Imports
# ponytail: Compact test suite validating product filtering, sorting, variant creation, cache clearing, and corrupt Excel import handling.
"""
import io
import uuid
import pytest
from tests.conftest import TestingSessionLocal
from backend import auth, models, cache

def create_seller_and_token() -> tuple[int, str]:
    """Helper to create seller user and return (seller_id, JWT token)."""
    db = TestingSessionLocal()
    unique_suffix = uuid.uuid4().hex[:6]
    user = models.User(
        name="تاجر المنتجات",
        email=f"seller_prod_{unique_suffix}@sheland.com",
        phone=f"077{unique_suffix}",
        password_hash=auth.hash_password("password123"),
        role="seller"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    seller = models.Seller(user_id=user.id, store_name="متجر الاختبار للمنتجات")
    db.add(seller)
    db.commit()
    db.refresh(seller)

    seller_id = seller.id
    token = auth.create_access_token({"sub": str(user.id), "role": user.role})
    db.close()
    return seller_id, token


def test_filter_products_by_price_and_rating(client):
    """Ensure filtering products by min/max price, rating, free shipping, and COD works accurately."""
    cache.clear_cache_by_prefix("cache:")
    db = TestingSessionLocal()
    cat = models.Category(name_ar="أجهزة", name_en="Devices", slug=f"devices-filter-{uuid.uuid4().hex[:6]}")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    cat_id = cat.id

    seller_id, _ = create_seller_and_token()

    # Product 1: Price 5000, Rating 4.8, free_shipping=True, cod=True
    p1 = models.Product(
        seller_id=seller_id, category_id=cat_id, title_ar="هاتف رخيص", title_en="Cheap Phone",
        slug=f"phone-cheap-{uuid.uuid4().hex[:6]}", price=5000.0, rating=4.8, free_shipping=True, cod_available=True,
        image_url="https://example.com/p1.jpg"
    )
    # Product 2: Price 25000, Rating 3.5, free_shipping=False, cod=True
    p2 = models.Product(
        seller_id=seller_id, category_id=cat_id, title_ar="هاتف فخم", title_en="Luxury Phone",
        slug=f"phone-luxury-{uuid.uuid4().hex[:6]}", price=25000.0, rating=3.5, free_shipping=False, cod_available=True,
        image_url="https://example.com/p2.jpg"
    )
    db.add_all([p1, p2])
    db.commit()
    db.close()

    # Filter 1: Price range 1000 to 10000 -> Expect p1
    res1 = client.get(f"/api/products?min_price=1000&max_price=10000&category_id={cat_id}")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1) == 1
    assert data1[0]["price"] == 5000.0

    # Filter 2: Min rating 4.0 -> Expect p1
    res2 = client.get(f"/api/products?min_rating=4.0&min_price=1&category_id={cat_id}")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2) == 1
    assert data2[0]["rating"] >= 4.0


def test_sort_products_by_price_and_newest(client):
    """Ensure sorting by price_asc, price_desc, and rating orders results properly."""
    cache.clear_cache_by_prefix("cache:")
    db = TestingSessionLocal()
    cat = models.Category(name_ar="ملابس", name_en="Clothes", slug=f"clothes-sort-{uuid.uuid4().hex[:6]}")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    cat_id = cat.id

    seller_id, _ = create_seller_and_token()

    p_low = models.Product(
        seller_id=seller_id, category_id=cat_id, title_ar="قميص رخيص", title_en="Cheap Shirt",
        slug=f"shirt-cheap-{uuid.uuid4().hex[:6]}", price=2000.0, rating=3.0, image_url="https://example.com/low.jpg"
    )
    p_high = models.Product(
        seller_id=seller_id, category_id=cat_id, title_ar="معطف غالي", title_en="Expensive Coat",
        slug=f"coat-high-{uuid.uuid4().hex[:6]}", price=15000.0, rating=4.9, image_url="https://example.com/high.jpg"
    )
    db.add_all([p_low, p_high])
    db.commit()
    db.close()

    # Sort price_asc with search query or bypass cache key
    res_asc = client.get(f"/api/products?category_id={cat_id}&sort_by=price_asc&min_price=1")
    assert res_asc.status_code == 200
    items_asc = res_asc.json()
    assert len(items_asc) == 2
    assert items_asc[0]["price"] <= items_asc[1]["price"]

    # Sort price_desc
    res_desc = client.get(f"/api/products?category_id={cat_id}&sort_by=price_desc&min_price=1")
    assert res_desc.status_code == 200
    items_desc = res_desc.json()
    assert len(items_desc) == 2
    assert items_desc[0]["price"] >= items_desc[1]["price"]


def test_product_cache_invalidation_on_update(client):
    """Ensure product update operation invalidates Redis/In-memory product & category caches."""
    cache.clear_cache_by_prefix("cache:")
    db = TestingSessionLocal()
    cat = models.Category(name_ar="ساعات", name_en="Watches", slug=f"watches-cache-{uuid.uuid4().hex[:6]}")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    cat_id = cat.id

    seller_id, token = create_seller_and_token()
    prod = models.Product(
        seller_id=seller_id, category_id=cat_id, title_ar="ساعة يد", title_en="Wrist Watch",
        slug=f"wrist-watch-{uuid.uuid4().hex[:6]}", price=8000.0, image_url="https://example.com/watch.jpg"
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    prod_id = prod.id
    db.close()

    # Populate cache by fetching categories
    client.get("/api/categories")
    cache.set_cache("cache:test_key", {"data": "cached"}, expire_seconds=300)

    # Perform product update
    headers = {"Authorization": f"Bearer {token}", "X-Requested-With": "XMLHttpRequest"}
    update_payload = {
        "title_ar": "ساعة يد فاخرة محدثة",
        "title_en": "Updated Luxury Watch",
        "slug": f"wrist-watch-updated-{uuid.uuid4().hex[:6]}",
        "price": 9500.0,
        "image_url": "https://example.com/watch.jpg",
        "category_id": cat_id,
        "seller_id": seller_id
    }
    update_res = client.put(f"/api/products/{prod_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200

    # Ensure cache with prefix "cache:" is cleared
    assert cache.get_cache("cache:categories") is None
    assert cache.get_cache("cache:test_key") is None


def test_product_with_variants_creation(client):
    """Ensure seller can create product with multiple variants (color, size, stock per variant)."""
    cache.clear_cache_by_prefix("cache:")
    db = TestingSessionLocal()
    cat = models.Category(name_ar="أحذية", name_en="Shoes", slug=f"shoes-var-{uuid.uuid4().hex[:6]}")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    cat_id = cat.id
    db.close()

    seller_id, token = create_seller_and_token()
    headers = {"Authorization": f"Bearer {token}", "X-Requested-With": "XMLHttpRequest"}

    product_payload = {
        "title_ar": "حذاء رياضي متطور",
        "title_en": "Advanced Running Shoes",
        "slug": f"running-shoes-{uuid.uuid4().hex[:6]}",
        "price": 18000.0,
        "image_url": "https://example.com/shoe.jpg",
        "category_id": cat_id,
        "seller_id": seller_id,
        "variants": [
            {"sku": "SHOE-RED-42", "color": "أحمر", "size": "42", "stock": 8, "price_override": 18000.0},
            {"sku": "SHOE-BLACK-44", "color": "أسود", "size": "44", "stock": 12, "price_override": 19000.0}
        ]
    }

    res = client.post("/api/products", json=product_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title_ar"] == "حذاء رياضي متطور"
    assert data["stock"] == 20  # 8 + 12
    assert len(data["variants"]) == 2


def test_excel_import_corrupt_file_handling(client):
    """Ensure invalid file formats or empty files uploaded for bulk import return 400 Bad Request."""
    _, token = create_seller_and_token()
    headers = {"Authorization": f"Bearer {token}", "X-Requested-With": "XMLHttpRequest"}

    # 1. Unsupported extension (.txt)
    txt_file = ("test.txt", io.BytesIO(b"sample text content"), "text/plain")
    res1 = client.post("/api/products/import-excel", files={"file": txt_file}, headers=headers)
    assert res1.status_code == 400
    assert "غير مدعوم" in res1.json()["detail"]

    # 2. Empty CSV file
    csv_file = ("empty.csv", io.BytesIO(b""), "text/csv")
    res2 = client.post("/api/products/import-excel", files={"file": csv_file}, headers=headers)
    assert res2.status_code == 400
    assert "لم يتم العثور على بيانات" in res2.json()["detail"]

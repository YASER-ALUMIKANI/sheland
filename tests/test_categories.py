"""
CityLand Backend - Category & Hierarchy Tests
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import TestingSessionLocal
from backend import models, cache


def test_get_categories_returns_list(client: TestClient):
    """Verifies that GET /api/categories returns a list of seeded categories."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert len(categories) > 0
    first_cat = categories[0]
    assert "id" in first_cat
    assert "name_ar" in first_cat
    assert "slug" in first_cat


def test_get_categories_cached(client: TestClient):
    """Verifies that GET /api/categories caches results and returns cached response on subsequent calls."""
    cache.clear_cache_by_prefix("cache:categories")

    # First call - populates cache
    resp1 = client.get("/api/categories")
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Verify cache key exists
    cached_val = cache.get_cache("cache:categories")
    assert cached_val is not None
    assert len(cached_val) == len(data1)

    # Second call - served from cache
    resp2 = client.get("/api/categories")
    assert resp2.status_code == 200
    assert resp2.json() == data1


def test_category_hierarchy_parent_children(client: TestClient):
    """Verifies parent-child category relationships in the database."""
    db = TestingSessionLocal()
    try:
        # Create parent category
        parent = models.Category(
            name_ar="الإلكترونيات",
            name_en="Electronics",
            slug="electronics-main"
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)

        # Create child category
        child = models.Category(
            parent_id=parent.id,
            name_ar="الهواتف الذكية",
            name_en="Smartphones",
            slug="smartphones-sub"
        )
        db.add(child)
        db.commit()
        db.refresh(child)

        # Query hierarchy
        fetched_child = db.query(models.Category).filter(models.Category.id == child.id).first()
        assert fetched_child.parent_id == parent.id

        children_list = db.query(models.Category).filter(models.Category.parent_id == parent.id).all()
        assert len(children_list) >= 1
        assert any(c.slug == "smartphones-sub" for c in children_list)
    finally:
        db.close()



def test_admin_create_category(client: TestClient):
    """Verifies that adding a new category to the database updates the category list after cache invalidation."""
    cache.clear_cache_by_prefix("cache:categories")

    db = TestingSessionLocal()
    try:
        new_cat = models.Category(
            name_ar="أزياء جديدة",
            name_en="New Fashion",
            slug="new-fashion-cat",
            icon="👕"
        )
        db.add(new_cat)
        db.commit()
    finally:
        db.close()

    cache.clear_cache_by_prefix("cache:categories")
    response = client.get("/api/categories")
    assert response.status_code == 200
    categories = response.json()
    slugs = [c["slug"] for c in categories]
    assert "new-fashion-cat" in slugs


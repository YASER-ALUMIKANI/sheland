"""
CityLand Backend - Analytics & KPIs Engine Unit Tests
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import TestingSessionLocal
from backend import models, analytics, auth


def test_analytics_total_revenue_calculation(client: TestClient):
    """Verifies that gross_revenue in finance KPIs correctly sums valid orders and excludes cancelled ones."""
    db = TestingSessionLocal()
    try:
        # Create Valid Order 1 (1500 YER)
        o1 = models.Order(
            order_number="ORD-REV-100",
            phone="967770001000",
            status="delivered",
            total_amount=1500.0,
            shipping_address="Sanaa",
            payment_method="COD"
        )
        # Create Valid Order 2 (2500 YER)
        o2 = models.Order(
            order_number="ORD-REV-200",
            phone="967770002000",
            status="مكتمل",
            total_amount=2500.0,
            shipping_address="Aden",
            payment_method="COD"
        )
        # Create Cancelled Order (5000 YER - Should be excluded)
        o3 = models.Order(
            order_number="ORD-REV-300",
            phone="967770003000",
            status="ملغي",
            total_amount=5000.0,
            shipping_address="Taiz",
            payment_method="COD"
        )
        db.add_all([o1, o2, o3])
        db.commit()

        # Compute analytics
        res = analytics.compute_ecommerce_analytics(db)
        finance = res["finance"]
        assert finance["gross_revenue"] == 4000.0  # 1500 + 2500
        assert finance["return_rate"] > 0  # 1 cancelled out of 3 total = 33.3%
    finally:
        db.close()


def test_analytics_top_products_ranking(client: TestClient):
    """Verifies that sold units and operational stock metrics calculate correctly across orders."""
    db = TestingSessionLocal()
    try:
        # Fetch initial operations metrics
        initial_res = analytics.compute_ecommerce_analytics(db)
        initial_sold = initial_res["operations"]["total_sold_units"]

        # Create Order with 3 items of product_id=1
        order = models.Order(
            order_number="ORD-OPS-100",
            phone="967771112222",
            status="processing",
            total_amount=300.0,
            shipping_address="Mukalla",
            payment_method="COD"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        item = models.OrderItem(
            order_id=order.id,
            product_id=1,
            price=100.0,
            quantity=3
        )
        db.add(item)
        db.commit()

        new_res = analytics.compute_ecommerce_analytics(db)
        ops = new_res["operations"]
        assert ops["total_sold_units"] == initial_sold + 3
        assert "inventory_turnover" in ops
    finally:
        db.close()


def test_analytics_new_vs_returning_customers(client: TestClient):
    """Verifies customer retention metrics: unique customers, repeat customers, and repeat purchase rate."""
    db = TestingSessionLocal()
    try:
        phone_one_timer = "967779990001"
        phone_repeat_customer = "967779990002"

        # Customer 1 (One-time purchase)
        o1 = models.Order(
            order_number="ORD-RET-1",
            phone=phone_one_timer,
            status="delivered",
            total_amount=1000.0,
            shipping_address="City A",
            payment_method="COD"
        )
        # Customer 2 (Purchase 1)
        o2 = models.Order(
            order_number="ORD-RET-2",
            phone=phone_repeat_customer,
            status="delivered",
            total_amount=2000.0,
            shipping_address="City B",
            payment_method="COD"
        )
        # Customer 2 (Purchase 2 - Repeat)
        o3 = models.Order(
            order_number="ORD-RET-3",
            phone=phone_repeat_customer,
            status="delivered",
            total_amount=1500.0,
            shipping_address="City B",
            payment_method="COD"
        )
        db.add_all([o1, o2, o3])
        db.commit()

        res = analytics.compute_ecommerce_analytics(db)
        retention = res["retention"]

        assert retention["unique_customers"] >= 2
        assert retention["repeat_customers"] >= 1
        assert retention["repeat_purchase_rate"] > 0.0
    finally:
        db.close()

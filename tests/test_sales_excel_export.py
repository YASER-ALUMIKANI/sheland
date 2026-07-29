import io
import pytest
import openpyxl
from backend import models, auth
from tests.conftest import TestingSessionLocal

def test_export_sales_excel_report(client):
    db = TestingSessionLocal()
    try:
        # Create admin user & auth header
        admin_user = models.User(
            name="مدير التصدير",
            email="admin_export_test@sheland.com",
            phone="0779998887",
            password_hash=auth.hash_password("admin123"),
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        token = auth.create_access_token({"sub": str(admin_user.id), "role": admin_user.role})
        headers = {"Authorization": f"Bearer {token}"}

        # Create test order
        order = models.Order(
            order_number="ORD-EXCELTEST01",
            customer_name="عميل التقرير",
            phone="771122334",
            shipping_address="مدينة البيضاء",
            payment_method="COD",
            coupon_code="SHELAND10",
            discount_amount=500.0,
            total_amount=4500.0,
            status="مكتمل"
        )
        db.add(order)
        db.commit()

        # Request excel export
        res = client.get("/api/admin/reports/sales-excel?period=weekly", headers=headers)
        assert res.status_code == 200
        assert "spreadsheetml.sheet" in res.headers["content-type"]

        # Parse with openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(res.content))
        ws = wb.active
        assert ws.title == "تقرير المبيعات الشامل"

        rows = list(ws.iter_rows(values_only=True))
        # Check title in row 1
        assert "منصة شي لاند" in str(rows[0][0])
        # Check header in row 3
        assert "رقم الطلب" in rows[2]
        # Check order data in row 4
        order_row = rows[3]
        assert order_row[0] == "ORD-EXCELTEST01"
        assert order_row[1] == "عميل التقرير"
        assert order_row[5] == "SHELAND10"
        assert order_row[6] == 500.0
        assert order_row[7] == 4500.0
    finally:
        db.close()

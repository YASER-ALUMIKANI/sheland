"""
backend/test_analytics.py - Unit test suite to verify Sheland Analytics KPI accuracy.
"""

from backend.analytics import (
    calculate_marketing_kpis,
    calculate_sales_conversion_kpis,
    calculate_finance_kpis,
    calculate_retention_kpis,
    calculate_operations_kpis,
    calculate_golden_triangle
)

def test_kpi_calculations():
    print("[TEST] Testing E-commerce Analytics Calculations...")

    # 1. Test Marketing
    m = calculate_marketing_kpis(100, 4000)
    assert m["total_visitors"] == 4000
    assert m["cac"] > 0

    # 2. Test Sales & Conversion
    s = calculate_sales_conversion_kpis(95, 100, 500000.0, 4000)
    assert s["conversion_rate"] == 2.5
    assert s["aov"] == 5263.16

    # 3. Test Golden Triangle
    gt = calculate_golden_triangle(2.5, 5263.16, 20.0)
    assert gt["score"] > 0

    print("[SUCCESS] All E-commerce Analytics KPI Unit Tests Passed Successfully!")

if __name__ == "__main__":
    test_kpi_calculations()

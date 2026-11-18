"""
End-to-End (E2E) Integration Test Suite
Validates all REST endpoints, domain exceptions, templates, CSV exports,
and presentation features.
Can run against a live running server OR directly via Flask's test client.
"""

import sys
import os
import json
import urllib.request
import urllib.error

# Ensure project root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app

class UnifiedClient:
    """Unified client that works against live HTTP or Flask test_client."""
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.is_live = False
        try:
            urllib.request.urlopen(f"{base_url}/api/metrics", timeout=1)
            self.is_live = True
            print(f">> Connected to live server at {base_url}")
        except Exception:
            print(">> Live server not running; using in-memory Flask Test Client...")
            self.test_client = app.test_client()

    def get(self, url):
        if self.is_live:
            try:
                res = urllib.request.urlopen(f"{self.base_url}{url}")
                return res.getcode(), res.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read()
        else:
            res = self.test_client.get(url)
            return res.status_code, res.data

    def post(self, url, data_dict):
        if self.is_live:
            req_data = json.dumps(data_dict).encode("utf-8")
            req = urllib.request.Request(f"{self.base_url}{url}", data=req_data, headers={"Content-Type": "application/json"})
            try:
                res = urllib.request.urlopen(req)
                return res.getcode(), res.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read()
        else:
            res = self.test_client.post(url, json=data_dict)
            return res.status_code, res.data


def run_tests():
    client = UnifiedClient()

    print("\n1. Testing GET /api/metrics ...")
    status, body = client.get("/api/metrics")
    assert status == 200, f"Expected 200, got {status}"
    metrics = json.loads(body.decode("utf-8"))
    print(f"   [SUCCESS] Metrics Response: Total Products: {metrics['total_products']}, Stock Units: {metrics['total_stock_units']}, Revenue: ${metrics['total_revenue']}")

    print("\n2. Testing GET /api/inventory?sort_by=price&order=desc ...")
    status, body = client.get("/api/inventory?sort_by=price&order=desc")
    assert status == 200
    inv = json.loads(body.decode("utf-8"))
    print(f"   [SUCCESS] Loaded {len(inv)} items. Top: {inv[0]['name']} (${inv[0]['price']})")

    print("\n3. Testing GET /api/analytics (Pandas & Matplotlib) ...")
    status, body = client.get("/api/analytics")
    assert status == 200
    ana = json.loads(body.decode("utf-8"))
    print(f"   [SUCCESS] Top product: {ana['summary']['top_product']}")
    print(f"   [SUCCESS] Charts generated: {list(ana['charts'].keys())}")
    assert "product_chart" in ana["charts"]
    assert "category_chart" in ana["charts"]
    assert "monthly_chart" in ana["charts"]

    print("\n4. Testing POST /api/sales (Valid Transaction) ...")
    valid_data = {
        "customer_name": "Test Shopper",
        "payment_method": "Credit Card",
        "tax_rate": 0.05,
        "items": [{"product_id": "PRD101", "quantity": 1}]
    }
    status, body = client.post("/api/sales", valid_data)
    assert status == 201, f"Expected 201, got {status}: {body}"
    sale_res = json.loads(body.decode("utf-8"))
    sale_id = sale_res["sale"]["sale_id"]
    print(f"   [SUCCESS] Created Sale: {sale_id}, Total: ${sale_res['sale']['total_amount']}")

    print("\n5. Testing POST /api/sales with InsufficientStockError (Quantity 99999) ...")
    bad_data = {
        "customer_name": "Greedy Shopper",
        "payment_method": "Cash",
        "items": [{"product_id": "PRD104", "quantity": 99999}]
    }
    status, body = client.post("/api/sales", bad_data)
    assert status == 400, f"Expected 400 for InsufficientStockError, got {status}"
    err_body = json.loads(body.decode("utf-8"))
    assert err_body["error"] == "InsufficientStockError"
    print(f"   [SUCCESS] Correctly caught InsufficientStockError: {err_body['message']}")

    print("\n6. Testing POST /api/sales with InvalidProductIDError ...")
    invalid_pid_data = {
        "customer_name": "Ghost Shopper",
        "payment_method": "Cash",
        "items": [{"product_id": "NON_EXISTENT_ID_999", "quantity": 1}]
    }
    status, body = client.post("/api/sales", invalid_pid_data)
    assert status == 404, f"Expected 404 for InvalidProductIDError, got {status}"
    err_body = json.loads(body.decode("utf-8"))
    assert err_body["error"] == "InvalidProductIDError"
    print(f"   [SUCCESS] Correctly caught InvalidProductIDError: {err_body['message']}")

    print("\n7. Testing GET /receipt/<sale_id> ...")
    status, body = client.get(f"/receipt/{sale_id}")
    assert status == 200
    html = body.decode("utf-8")
    assert "NOVA RETAIL STORE" in html or "Invoice" in html
    assert sale_id in html
    print(f"   [SUCCESS] Printable receipt rendered for {sale_id}")

    print("\n8. Testing GET /presentation (Interactive Slide Deck) ...")
    status, body = client.get("/presentation")
    assert status == 200
    pres_html = body.decode("utf-8")
    assert "NovaStock" in pres_html
    assert "PBL" in pres_html
    print("   [SUCCESS] Interactive presentation slide deck rendered successfully")

    print("\n9. Testing GET /api/export/inventory (CSV Export) ...")
    status, body = client.get("/api/export/inventory")
    assert status == 200
    inv_csv = body.decode("utf-8")
    assert "product_id,name,category,price,quantity" in inv_csv
    print(f"   [SUCCESS] Inventory exported as CSV")

    print("\n10. Testing GET /api/export/sales (CSV Export) ...")
    status, body = client.get("/api/export/sales")
    assert status == 200
    sales_csv = body.decode("utf-8")
    assert "sale_id,timestamp,customer_name" in sales_csv
    print(f"   [SUCCESS] Sales history exported as CSV")

    print("\n11. Testing GET /api/system-info ...")
    status, body = client.get("/api/system-info")
    assert status == 200
    info = json.loads(body.decode("utf-8"))
    assert "Product" in info["oop_classes"]
    assert "Inventory" in info["oop_classes"]
    assert "Sale" in info["oop_classes"]
    print(f"   [SUCCESS] System info verified: OOP Classes: {info['oop_classes']}")

    print("\n=======================================================")
    print(">> ALL 11 END-TO-END INTEGRATION TESTS PASSED 100%! <<")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()

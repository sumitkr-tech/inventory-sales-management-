"""
Flask Application for Inventory & Sales Management System
Hosts the web application, REST API endpoints, and serves interactive UI.
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for

# Ensure current directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from models import (
    Inventory,
    InventorySalesException,
    InvalidProductIDError,
    InsufficientStockError,
    DuplicateProductIDError,
    InvalidProductDataError
)
from services import SalesAnalytics
from services.seeder import seed_sample_sales

app = Flask(__name__)
app.config["SECRET_KEY"] = "inventory-sales-secret-key-2026"

DATA_DIR = os.path.join(CURRENT_DIR, "data")
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")

# Initialize models and services
inventory = Inventory(inventory_file=INVENTORY_FILE, sales_file=SALES_FILE)
seed_sample_sales(sales_file=SALES_FILE, inventory_products=inventory.products)
analytics = SalesAnalytics(sales_file=SALES_FILE, inventory_file=INVENTORY_FILE)


# ---------------- Error Handling ----------------

@app.errorhandler(InventorySalesException)
def handle_domain_exception(error: InventorySalesException):
    """Handles domain-specific exceptions and returns formatted JSON response."""
    return jsonify(error.to_dict()), error.status_code


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "NotFound", "message": "The requested resource was not found."}), 404


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "InternalServerError", "message": str(e)}), 500


# ---------------- Web Pages ----------------

@app.route("/")
def index():
    """Main application dashboard."""
    return render_template("index.html")


@app.route("/receipt/<sale_id>")
def view_receipt(sale_id):
    """Renders a printable invoice receipt for a given sale ID."""
    bills = inventory.get_sales_records(limit=1000)
    matched_bill = next((b for b in bills if b["sale_id"] == sale_id), None)
    if not matched_bill:
        return "Invoice not found", 404
    return render_template("receipt.html", bill=matched_bill, items=matched_bill.get("items", []))


@app.route("/presentation")
def view_presentation():
    """Renders the interactive PBL presentation slide deck."""
    return render_template("presentation.html")


@app.route("/api/export/inventory")
def export_inventory_csv():
    """Exports current inventory catalog to CSV file."""
    if not os.path.exists(INVENTORY_FILE):
        inventory.save_to_file()
    return send_file(INVENTORY_FILE, as_attachment=True, download_name="inventory_catalog_export.csv", mimetype="text/csv")


@app.route("/api/export/sales")
def export_sales_csv():
    """Exports sales transactions ledger to CSV file."""
    if not os.path.exists(SALES_FILE):
        return jsonify({"message": "No sales recorded yet."}), 404
    return send_file(SALES_FILE, as_attachment=True, download_name="sales_history_export.csv", mimetype="text/csv")


@app.route("/api/system-info")
def system_info():
    """Returns runtime system specifications and OOP structure metadata for project evaluation."""
    return jsonify({
        "project_name": "NovaStock - Inventory & Sales Management System",
        "purpose": "Project-Based Learning (PBL) Submission",
        "python_version": sys.version,
        "platform": sys.platform,
        "oop_classes": ["Product", "Inventory", "Sale", "SaleItem", "SalesAnalytics"],
        "custom_exceptions": [
            "InventorySalesException",
            "InvalidProductIDError",
            "InsufficientStockError",
            "DuplicateProductIDError",
            "InvalidProductDataError"
        ],
        "data_storage": {
            "inventory_file": INVENTORY_FILE,
            "sales_file": SALES_FILE,
            "format": "Flat CSV with headers"
        },
        "analytics_engine": "Pandas & Matplotlib (Agg headless backend)"
    })


# ---------------- REST API Endpoints ----------------

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Returns overview KPI metrics for the shop."""
    metrics = inventory.get_summary_metrics()
    return jsonify(metrics)


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Returns all unique product categories."""
    return jsonify(inventory.get_categories())


@app.route("/api/inventory", methods=["GET"])
def list_inventory():
    """
    Returns product list with optional filtering and sorting:
    - search: string
    - category: string
    - sort_by: 'price', 'quantity', 'sales', 'name', 'id'
    - order: 'asc' or 'desc'
    - low_stock: 'true' or 'false'
    - threshold: int (default 5)
    """
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()
    sort_by = request.args.get("sort_by", "name").strip()
    order = request.args.get("order", "asc").strip().lower()
    low_stock = request.args.get("low_stock", "false").lower() == "true"
    threshold = int(request.args.get("threshold", 5))

    # Base search
    if search_query:
        products = inventory.search_products(search_query)
    else:
        products = list(inventory.products.values())

    # Category filter
    if category_filter:
        products = [p for p in products if p.category.lower() == category_filter.lower()]

    # Low stock filter
    if low_stock:
        products = [p for p in products if p.is_low_stock(threshold)]

    # Sorting
    ascending = (order == "asc")
    products = inventory.sort_products(sort_by=sort_by, ascending=ascending, products_list=products)

    # Attach sales count to each product dictionary
    sales_counts = inventory.get_product_sales_counts()
    result = []
    for p in products:
        d = p.to_dict()
        d["units_sold"] = sales_counts.get(p.product_id, 0)
        d["is_low_stock"] = p.is_low_stock(threshold)
        result.append(d)

    return jsonify(result)


@app.route("/api/inventory/<product_id>", methods=["GET"])
def get_product(product_id):
    """Fetches details for a single product."""
    product = inventory.get_product(product_id)
    sales_counts = inventory.get_product_sales_counts()
    res = product.to_dict()
    res["units_sold"] = sales_counts.get(product.product_id, 0)
    return jsonify(res)


@app.route("/api/inventory", methods=["POST"])
def add_product():
    """Adds a new product to inventory."""
    data = request.get_json() or {}
    product_id = data.get("product_id", "").strip()
    name = data.get("name", "").strip()
    category = data.get("category", "General").strip()
    try:
        price = float(data.get("price", 0.0))
        quantity = int(data.get("quantity", 0))
    except (ValueError, TypeError):
        raise InvalidProductDataError("Price/Quantity", "invalid", "Price and Quantity must be valid numbers.")

    product = inventory.add_product(product_id, name, category, price, quantity)
    return jsonify({
        "message": f"Product '{product.name}' added successfully.",
        "product": product.to_dict()
    }), 201


@app.route("/api/inventory/<product_id>", methods=["PUT"])
def update_product(product_id):
    """Updates an existing product's metadata and/or quantity."""
    data = request.get_json() or {}
    name = data.get("name")
    category = data.get("category")
    price = data.get("price")
    quantity = data.get("quantity")

    product = inventory.update_product_details(
        product_id=product_id,
        name=name,
        category=category,
        price=price,
        quantity=quantity
    )
    return jsonify({
        "message": f"Product '{product.product_id}' updated successfully.",
        "product": product.to_dict()
    })


@app.route("/api/inventory/<product_id>/stock", methods=["POST"])
def update_stock(product_id):
    """Quick stock adjustment (mode='set' or mode='add')."""
    data = request.get_json() or {}
    try:
        quantity = int(data.get("quantity", 0))
    except (ValueError, TypeError):
        raise InvalidProductDataError("Quantity", data.get("quantity"), "Quantity must be an integer.")

    mode = data.get("mode", "add")
    product = inventory.update_stock(product_id=product_id, quantity=quantity, mode=mode)
    return jsonify({
        "message": f"Stock updated for '{product.name}'. New Quantity: {product.quantity}",
        "product": product.to_dict()
    })


@app.route("/api/inventory/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Deletes a product from the inventory."""
    product = inventory.delete_product(product_id)
    return jsonify({
        "message": f"Product '{product.name}' (ID: {product.product_id}) removed from inventory."
    })


@app.route("/api/sales", methods=["POST"])
def record_sale():
    """
    Records a sale and updates stock.
    Payload:
    {
        "customer_name": "...",
        "payment_method": "Cash|Credit Card|UPI",
        "tax_rate": 0.05,
        "items": [
            { "product_id": "PRD101", "quantity": 2 },
            ...
        ]
    }
    """
    data = request.get_json() or {}
    items = data.get("items", [])
    customer_name = data.get("customer_name", "Walk-in Customer")
    payment_method = data.get("payment_method", "Cash")
    tax_rate = float(data.get("tax_rate", 0.05))

    sale = inventory.record_sale(
        items_data=items,
        customer_name=customer_name,
        payment_method=payment_method,
        tax_rate=tax_rate
    )

    return jsonify({
        "message": "Sale transaction completed successfully.",
        "sale": sale.to_dict()
    }), 201


@app.route("/api/sales", methods=["GET"])
def get_sales_history():
    """Returns list of past sale receipts."""
    limit = int(request.args.get("limit", 100))
    bills = inventory.get_sales_records(limit=limit)
    return jsonify(bills)


@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Returns sales summary via Pandas and Matplotlib charts."""
    summary = analytics.get_analysis_summary()
    charts = analytics.generate_all_charts()
    return jsonify({
        "summary": summary,
        "charts": charts
    })


@app.route("/api/reset-demo", methods=["POST"])
def reset_demo():
    """Seeds sample data for testing and demonstrations."""
    inventory._seed_sample_inventory()
    seed_sample_sales(sales_file=SALES_FILE, inventory_products=inventory.products, force=True)
    return jsonify({"message": "Sample inventory and sales data reloaded successfully."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=================================================")
    print(">> Inventory & Sales Management System")
    print(f">> Localhost URL: http://127.0.0.1:{port}")
    print("=================================================")
    app.run(host="0.0.0.0", port=port, debug=False)

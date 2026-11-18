"""
Seed data generator for realistic initial demonstration.
Populates sample sales transactions if sales.csv is empty.
"""

import os
import csv
from datetime import datetime, timedelta
import random


def seed_sample_sales(sales_file: str, inventory_products: dict, force: bool = False):
    """Generates realistic sample sales history across recent months if empty."""
    if not force and os.path.exists(sales_file):
        try:
            with open(sales_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                if len(lines) > 1:
                    return
        except Exception:
            pass

    os.makedirs(os.path.dirname(sales_file), exist_ok=True)
    fieldnames = [
        "sale_id", "timestamp", "customer_name", "payment_method",
        "product_id", "product_name", "category", "unit_price",
        "quantity", "subtotal", "tax_amount", "total_amount"
    ]

    customers = ["Alice Walker", "David Smith", "Emma Johnson", "Michael Brown", "Sophia Davis", "James Wilson", "Olivia Martinez"]
    payments = ["Cash", "Credit Card", "Debit Card", "UPI / Mobile Pay"]

    # Generate dates across past 4 months up to today
    now = datetime.now()
    base_dates = [
        now - timedelta(days=95),
        now - timedelta(days=75),
        now - timedelta(days=60),
        now - timedelta(days=45),
        now - timedelta(days=30),
        now - timedelta(days=20),
        now - timedelta(days=12),
        now - timedelta(days=5),
        now - timedelta(days=2),
        now
    ]

    sample_items_pool = [
        ("PRD101", "Wireless Optical Mouse", "Electronics", 24.99, 2),
        ("PRD102", "Mechanical Keyboard (RGB)", "Electronics", 69.50, 1),
        ("PRD103", "Noise Cancelling Headphones", "Electronics", 129.99, 1),
        ("PRD105", "Organic Colombian Coffee (500g)", "Groceries", 14.99, 3),
        ("PRD106", "Extra Virgin Olive Oil (1L)", "Groceries", 18.00, 2),
        ("PRD108", "Dark Chocolate Bar 85% (100g)", "Groceries", 3.75, 4),
        ("PRD109", "Classic Cotton Crew T-Shirt", "Clothing", 19.99, 2),
        ("PRD110", "Denim Slim Fit Jeans", "Clothing", 49.99, 1),
        ("PRD112", "Hardcover Ruled Notebook A5", "Stationery", 8.50, 5),
        ("PRD113", "Gel Pen Set 12 Colors", "Stationery", 11.20, 2),
    ]

    rows = []
    sale_counter = 1001

    for idx, dt in enumerate(base_dates):
        # 1 to 2 orders per date
        for _ in range(random.randint(1, 2)):
            sale_id = f"INV-{sale_counter}"
            sale_counter += 1
            cust = random.choice(customers)
            pay = random.choice(payments)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")

            # pick 1 to 3 items
            selected = random.sample(sample_items_pool, k=random.randint(1, 3))
            subtotal_order = sum(item[3] * item[4] for item in selected)
            tax_order = round(subtotal_order * 0.05, 2)

            for item in selected:
                pid, pname, pcat, price, qty = item
                subtotal = round(price * qty, 2)
                item_tax = round((subtotal / subtotal_order) * tax_order, 2)
                item_total = round(subtotal + item_tax, 2)

                rows.append({
                    "sale_id": sale_id,
                    "timestamp": timestamp_str,
                    "customer_name": cust,
                    "payment_method": pay,
                    "product_id": pid,
                    "product_name": pname,
                    "category": pcat,
                    "unit_price": f"{price:.2f}",
                    "quantity": qty,
                    "subtotal": f"{subtotal:.2f}",
                    "tax_amount": f"{item_tax:.2f}",
                    "total_amount": f"{item_total:.2f}"
                })

    with open(sales_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


"""
Inventory Class
Manages the product collection, file persistence, search, sort, and sales execution.
"""

import os
import csv
from typing import Dict, List, Optional, Any
from .product import Product
from .sale import Sale, SaleItem
from .exceptions import (
    InvalidProductIDError,
    InsufficientStockError,
    DuplicateProductIDError,
    InvalidProductDataError
)


class Inventory:
    """Manages product catalog, stock updates, search, sort, and persistence."""

    def __init__(self, inventory_file: str, sales_file: str):
        self.inventory_file = inventory_file
        self.sales_file = sales_file
        self.products: Dict[str, Product] = {}

        # Ensure data folder exists
        os.makedirs(os.path.dirname(self.inventory_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.sales_file), exist_ok=True)

        self._load_inventory()
        self._ensure_sales_file_headers()

    # ---------------- File Persistence ----------------

    def _load_inventory(self) -> None:
        """Loads inventory from the CSV file if it exists, otherwise populates sample data."""
        self.products.clear()
        if os.path.exists(self.inventory_file):
            try:
                with open(self.inventory_file, mode="r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if not row or not row.get("product_id"):
                            continue
                        product = Product(
                            product_id=row["product_id"],
                            name=row["name"],
                            category=row.get("category", "General"),
                            price=float(row.get("price", 0.0)),
                            quantity=int(row.get("quantity", 0))
                        )
                        self.products[product.product_id] = product
            except Exception as e:
                print(f"[Warning] Error reading inventory file {self.inventory_file}: {e}")

        # If empty or not created yet, populate with realistic initial inventory
        if not self.products:
            self._seed_sample_inventory()

    def _seed_sample_inventory(self) -> None:
        """Seeds initial realistic products for a small retail shop."""
        initial_products = [
            Product("PRD101", "Wireless Optical Mouse", "Electronics", 24.99, 35),
            Product("PRD102", "Mechanical Keyboard (RGB)", "Electronics", 69.50, 18),
            Product("PRD103", "Noise Cancelling Headphones", "Electronics", 129.99, 8),
            Product("PRD104", "USB-C Fast Charging Cable (2m)", "Electronics", 12.50, 4),  # Low stock
            Product("PRD105", "Organic Colombian Coffee (500g)", "Groceries", 14.99, 50),
            Product("PRD106", "Extra Virgin Olive Oil (1L)", "Groceries", 18.00, 22),
            Product("PRD107", "Almond Milk Unsweetened (1L)", "Groceries", 4.25, 3),   # Low stock
            Product("PRD108", "Dark Chocolate Bar 85% (100g)", "Groceries", 3.75, 45),
            Product("PRD109", "Classic Cotton Crew T-Shirt", "Clothing", 19.99, 40),
            Product("PRD110", "Denim Slim Fit Jeans", "Clothing", 49.99, 15),
            Product("PRD111", "Wool Blend Winter Scarf", "Clothing", 22.00, 5),   # Low stock
            Product("PRD112", "Hardcover Ruled Notebook A5", "Stationery", 8.50, 60),
            Product("PRD113", "Gel Pen Set 12 Colors", "Stationery", 11.20, 25),
            Product("PRD114", "Ergonomic Desk Gel Pad", "Stationery", 15.00, 2)    # Low stock
        ]
        for p in initial_products:
            self.products[p.product_id] = p
        self.save_to_file()

    def save_to_file(self) -> None:
        """Persists current in-memory products to the inventory CSV file."""
        fieldnames = ["product_id", "name", "category", "price", "quantity"]
        with open(self.inventory_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for product in self.products.values():
                writer.writerow({
                    "product_id": product.product_id,
                    "name": product.name,
                    "category": product.category,
                    "price": f"{product.price:.2f}",
                    "quantity": product.quantity
                })

    def _ensure_sales_file_headers(self) -> None:
        """Ensures sales.csv exists with correct headers."""
        if not os.path.exists(self.sales_file) or os.path.getsize(self.sales_file) == 0:
            fieldnames = [
                "sale_id", "timestamp", "customer_name", "payment_method",
                "product_id", "product_name", "category", "unit_price",
                "quantity", "subtotal", "tax_amount", "total_amount"
            ]
            with open(self.sales_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

    # ---------------- Product Operations ----------------

    def get_product(self, product_id: str) -> Product:
        """Retrieves a product by ID or raises InvalidProductIDError."""
        product_id = str(product_id).strip()
        if product_id not in self.products:
            raise InvalidProductIDError(product_id)
        return self.products[product_id]

    def add_product(self, product_id: str, name: str, category: str, price: float, quantity: int) -> Product:
        """Adds a new product to inventory, ensuring unique ID."""
        product_id = str(product_id).strip()
        if product_id in self.products:
            raise DuplicateProductIDError(product_id)

        product = Product(product_id, name, category, price, quantity)
        self.products[product_id] = product
        self.save_to_file()
        return product

    def update_stock(self, product_id: str, quantity: int, mode: str = "set") -> Product:
        """
        Updates product stock.
        mode="set": overrides current quantity
        mode="add": adds delta to current quantity
        """
        product = self.get_product(product_id)
        if mode == "set":
            product.set_quantity(quantity)
        elif mode == "add":
            product.update_stock(quantity)
        else:
            raise InvalidProductDataError("Mode", mode, "Mode must be 'set' or 'add'")
        self.save_to_file()
        return product

    def update_product_details(
        self, product_id: str, name: str = None, category: str = None, price: float = None, quantity: int = None
    ) -> Product:
        """Updates multiple details of an existing product."""
        product = self.get_product(product_id)
        product.update_details(name=name, category=category, price=price)
        if quantity is not None:
            product.set_quantity(int(quantity))
        self.save_to_file()
        return product

    def delete_product(self, product_id: str) -> Product:
        """Removes a product from inventory."""
        product = self.get_product(product_id)
        del self.products[product_id]
        self.save_to_file()
        return product

    # ---------------- Search and Filtering ----------------

    def search_products(self, query: str) -> List[Product]:
        """Searches products by matching query against ID, Name, or Category."""
        if not query or not query.strip():
            return list(self.products.values())
        q = query.strip().lower()
        results = [
            p for p in self.products.values()
            if q in p.product_id.lower() or q in p.name.lower() or q in p.category.lower()
        ]
        return results

    def get_low_stock_products(self, threshold: int = 5) -> List[Product]:
        """Returns all products where stock is <= threshold."""
        return [p for p in self.products.values() if p.is_low_stock(threshold)]

    def get_categories(self) -> List[str]:
        """Returns distinct sorted categories present in inventory."""
        cats = {p.category for p in self.products.values()}
        return sorted(list(cats))

    # ---------------- Sorting ----------------

    def sort_products(self, sort_by: str = "name", ascending: bool = True, products_list: Optional[List[Product]] = None) -> List[Product]:
        """
        Sorts products based on:
        - 'price'
        - 'quantity'
        - 'sales' (total units sold from sales records)
        - 'name'
        - 'id'
        """
        target = products_list if products_list is not None else list(self.products.values())

        if sort_by == "price":
            return sorted(target, key=lambda p: p.price, reverse=not ascending)
        elif sort_by == "quantity":
            return sorted(target, key=lambda p: p.quantity, reverse=not ascending)
        elif sort_by == "sales":
            sales_counts = self.get_product_sales_counts()
            return sorted(target, key=lambda p: sales_counts.get(p.product_id, 0), reverse=not ascending)
        elif sort_by == "name":
            return sorted(target, key=lambda p: p.name.lower(), reverse=not ascending)
        elif sort_by in ("id", "product_id"):
            return sorted(target, key=lambda p: p.product_id, reverse=not ascending)
        return target

    def get_product_sales_counts(self) -> Dict[str, int]:
        """Computes aggregate units sold per product_id from sales.csv."""
        counts: Dict[str, int] = {}
        if not os.path.exists(self.sales_file):
            return counts
        try:
            with open(self.sales_file, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get("product_id")
                    qty = int(row.get("quantity", 0))
                    if pid:
                        counts[pid] = counts.get(pid, 0) + qty
        except Exception:
            pass
        return counts

    # ---------------- Sales & Billing ----------------

    def record_sale(
        self,
        items_data: List[Dict[str, Any]],
        customer_name: str = "Walk-in Customer",
        payment_method: str = "Cash",
        tax_rate: float = 0.05
    ) -> Sale:
        """
        Processes a sale order:
        1. Validates all requested products exist.
        2. Validates sufficient stock for ALL items before deducting any inventory.
        3. Deducts stock from each product.
        4. Saves updated inventory to inventory.csv.
        5. Writes the transaction to sales.csv.
        6. Returns the completed Sale instance.
        """
        if not items_data:
            raise InvalidProductDataError("Sale Items", "empty", "Sale must include at least one item.")

        # Step 1 & 2: Verification phase (Atomic Check)
        validated_items: List[SaleItem] = []
        for req in items_data:
            pid = str(req.get("product_id", "")).strip()
            qty = int(req.get("quantity", 0))

            if qty <= 0:
                raise InvalidProductDataError("Quantity", qty, f"Quantity to sell must be greater than zero for ID {pid}.")

            product = self.get_product(pid)  # Raises InvalidProductIDError if not found

            if req_qty := qty > product.quantity:
                raise InsufficientStockError(
                    product_id=product.product_id,
                    product_name=product.name,
                    requested=qty,
                    available=product.quantity
                )

            validated_items.append(
                SaleItem(
                    product_id=product.product_id,
                    product_name=product.name,
                    category=product.category,
                    unit_price=product.price,
                    quantity=qty
                )
            )

        # Step 3: Deduction phase
        for item in validated_items:
            product = self.products[item.product_id]
            product.quantity -= item.quantity

        # Step 4: Persist inventory
        self.save_to_file()

        # Step 5: Construct Sale and persist to sales.csv
        sale_id = f"INV-{len(self.get_all_sales_ids()) + 1001}"
        sale = Sale(
            sale_id=sale_id,
            items=validated_items,
            customer_name=customer_name,
            payment_method=payment_method,
            tax_rate=tax_rate
        )

        self._append_sale_to_file(sale)
        return sale

    def _append_sale_to_file(self, sale: Sale) -> None:
        """Appends sale rows to sales.csv."""
        rows = sale.to_flat_rows()
        fieldnames = [
            "sale_id", "timestamp", "customer_name", "payment_method",
            "product_id", "product_name", "category", "unit_price",
            "quantity", "subtotal", "tax_amount", "total_amount"
        ]
        with open(self.sales_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            for row in rows:
                writer.writerow(row)

    def get_all_sales_ids(self) -> List[str]:
        """Returns distinct list of sale IDs from sales.csv."""
        ids = set()
        if not os.path.exists(self.sales_file):
            return []
        try:
            with open(self.sales_file, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sid = row.get("sale_id")
                    if sid:
                        ids.add(sid)
        except Exception:
            pass
        return sorted(list(ids))

    def get_sales_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Reads sales.csv and groups into transaction bills."""
        if not os.path.exists(self.sales_file):
            return []

        sales_map: Dict[str, Dict[str, Any]] = {}
        try:
            with open(self.sales_file, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sid = row.get("sale_id")
                    if not sid:
                        continue
                    if sid not in sales_map:
                        sales_map[sid] = {
                            "sale_id": sid,
                            "timestamp": row.get("timestamp", ""),
                            "customer_name": row.get("customer_name", "Customer"),
                            "payment_method": row.get("payment_method", "Cash"),
                            "subtotal": 0.0,
                            "tax_amount": 0.0,
                            "total_amount": 0.0,
                            "total_units": 0,
                            "items": []
                        }

                    sub = float(row.get("subtotal", 0.0))
                    tax = float(row.get("tax_amount", 0.0))
                    tot = float(row.get("total_amount", 0.0))
                    qty = int(row.get("quantity", 0))

                    sales_map[sid]["subtotal"] = round(sales_map[sid]["subtotal"] + sub, 2)
                    sales_map[sid]["tax_amount"] = round(sales_map[sid]["tax_amount"] + tax, 2)
                    sales_map[sid]["total_amount"] = round(sales_map[sid]["total_amount"] + tot, 2)
                    sales_map[sid]["total_units"] += qty
                    sales_map[sid]["items"].append({
                        "product_id": row.get("product_id"),
                        "product_name": row.get("product_name"),
                        "category": row.get("category"),
                        "unit_price": float(row.get("unit_price", 0.0)),
                        "quantity": qty,
                        "subtotal": sub
                    })
        except Exception as e:
            print(f"Error reading sales file: {e}")

        # Return latest sales first
        bills = list(sales_map.values())
        bills.reverse()
        return bills[:limit]

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Provides quick overview metrics for dashboard."""
        total_products = len(self.products)
        total_stock_units = sum(p.quantity for p in self.products.values())
        total_inventory_value = sum(p.total_stock_value for p in self.products.values())
        low_stock_count = len(self.get_low_stock_products())

        # Total revenue & orders from sales file
        bills = self.get_sales_records(limit=10000)
        total_revenue = sum(b["total_amount"] for b in bills)
        total_orders = len(bills)
        total_items_sold = sum(b["total_units"] for b in bills)

        return {
            "total_products": total_products,
            "total_stock_units": total_stock_units,
            "total_inventory_value": round(total_inventory_value, 2),
            "low_stock_count": low_stock_count,
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "total_items_sold": total_items_sold
        }

"""
Unit and Integration Tests for Inventory & Sales Management System
Tests:
- Product class validations and stock updates
- Custom exceptions (InvalidProductIDError, InsufficientStockError, etc.)
- Inventory management, search, and sorting (price, quantity, sales)
- Sale class, atomic stock deduction, bill calculations
- Pandas sales analytics calculations
- Matplotlib chart generation
"""

import os
import shutil
import tempfile
import unittest

from models import (
    Product,
    Inventory,
    Sale,
    SaleItem,
    InvalidProductIDError,
    InsufficientStockError,
    DuplicateProductIDError,
    InvalidProductDataError
)
from services import SalesAnalytics


class TestInventorySalesSystem(unittest.TestCase):

    def setUp(self):
        # Create isolated temporary files for testing
        self.test_dir = tempfile.mkdtemp()
        self.inventory_file = os.path.join(self.test_dir, "test_inventory.csv")
        self.sales_file = os.path.join(self.test_dir, "test_sales.csv")
        self.inventory = Inventory(self.inventory_file, self.sales_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_product_validation(self):
        # Valid product
        p = Product("P10", "Mechanical Mouse", "Electronics", 29.99, 10)
        self.assertEqual(p.total_stock_value, 299.9)

        # Invalid price
        with self.assertRaises(InvalidProductDataError):
            Product("P11", "Bad Item", "Electronics", -5.0, 10)

        # Invalid quantity
        with self.assertRaises(InvalidProductDataError):
            Product("P12", "Bad Item", "Electronics", 15.0, -1)

    def test_add_and_duplicate_product(self):
        self.inventory.add_product("TEST01", "Gaming Monitor", "Electronics", 299.99, 15)
        p = self.inventory.get_product("TEST01")
        self.assertEqual(p.name, "Gaming Monitor")

        # Duplicate ID should raise DuplicateProductIDError
        with self.assertRaises(DuplicateProductIDError):
            self.inventory.add_product("TEST01", "Duplicate Monitor", "Electronics", 200.0, 5)

    def test_invalid_product_id_error(self):
        # Non-existent ID should raise InvalidProductIDError
        with self.assertRaises(InvalidProductIDError):
            self.inventory.get_product("NON_EXISTENT_ID")

    def test_insufficient_stock_error(self):
        self.inventory.add_product("STOCK01", "Limited Edition GPU", "Electronics", 500.0, 2)

        # Requesting 5 when only 2 are available must raise InsufficientStockError
        with self.assertRaises(InsufficientStockError) as ctx:
            self.inventory.record_sale([{"product_id": "STOCK01", "quantity": 5}])

        err = ctx.exception
        self.assertEqual(err.product_id, "STOCK01")
        self.assertEqual(err.requested, 5)
        self.assertEqual(err.available, 2)
        # Ensure stock was NOT deducted
        self.assertEqual(self.inventory.get_product("STOCK01").quantity, 2)

    def test_successful_sale_and_billing(self):
        self.inventory.add_product("B01", "Coffee Beans", "Groceries", 20.0, 10)
        self.inventory.add_product("B02", "Mug", "Home", 10.0, 10)

        sale = self.inventory.record_sale([
            {"product_id": "B01", "quantity": 2},
            {"product_id": "B02", "quantity": 1}
        ], customer_name="Alice", tax_rate=0.05)

        # Subtotal = (20*2) + (10*1) = 50.00
        # Tax = 50 * 0.05 = 2.50
        # Total = 52.50
        self.assertEqual(sale.subtotal, 50.0)
        self.assertEqual(sale.tax_amount, 2.5)
        self.assertEqual(sale.total_amount, 52.5)

        # Verify inventory stock deduction
        self.assertEqual(self.inventory.get_product("B01").quantity, 8)
        self.assertEqual(self.inventory.get_product("B02").quantity, 9)

    def test_sorting_by_price_and_quantity(self):
        # Sort by price ascending
        sorted_by_price = self.inventory.sort_products(sort_by="price", ascending=True)
        prices = [p.price for p in sorted_by_price]
        self.assertEqual(prices, sorted(prices))

        # Sort by quantity descending
        sorted_by_qty = self.inventory.sort_products(sort_by="quantity", ascending=False)
        qtys = [p.quantity for p in sorted_by_qty]
        self.assertEqual(qtys, sorted(qtys, reverse=True))

    def test_pandas_analytics_and_matplotlib_charts(self):
        analytics = SalesAnalytics(self.sales_file, self.inventory_file)
        summary = analytics.get_analysis_summary()
        self.assertIsInstance(summary, dict)

        charts = analytics.generate_all_charts()
        self.assertTrue(charts["product_chart"].startswith("data:image/png;base64,"))
        self.assertTrue(charts["category_chart"].startswith("data:image/png;base64,"))
        self.assertTrue(charts["monthly_chart"].startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()

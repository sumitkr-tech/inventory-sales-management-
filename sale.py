"""
Sale Class Representation
Encapsulates sales transaction details, billing calculations, and recording.
"""

from datetime import datetime
from typing import List, Dict, Any


class SaleItem:
    """Represents a line item in a sale transaction."""
    def __init__(self, product_id: str, product_name: str, category: str, unit_price: float, quantity: int):
        self.product_id = product_id
        self.product_name = product_name
        self.category = category
        self.unit_price = float(unit_price)
        self.quantity = int(quantity)
        self.subtotal = round(self.unit_price * self.quantity, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "unit_price": round(self.unit_price, 2),
            "quantity": self.quantity,
            "subtotal": self.subtotal
        }


class Sale:
    """Represents an entire sale transaction / invoice."""

    def __init__(
        self,
        sale_id: str,
        items: List[SaleItem],
        timestamp: str = None,
        customer_name: str = "Walk-in Customer",
        payment_method: str = "Cash",
        tax_rate: float = 0.05
    ):
        self.sale_id = sale_id
        self.items = items
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.customer_name = customer_name or "Walk-in Customer"
        self.payment_method = payment_method or "Cash"
        self.tax_rate = float(tax_rate)

        # Calculations
        self.subtotal = round(sum(item.subtotal for item in self.items), 2)
        self.tax_amount = round(self.subtotal * self.tax_rate, 2)
        self.total_amount = round(self.subtotal + self.tax_amount, 2)
        self.total_units = sum(item.quantity for item in self.items)

    def to_dict(self) -> Dict[str, Any]:
        """Converts sale object into dictionary format for API responses."""
        return {
            "sale_id": self.sale_id,
            "timestamp": self.timestamp,
            "customer_name": self.customer_name,
            "payment_method": self.payment_method,
            "tax_rate": self.tax_rate,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "total_amount": self.total_amount,
            "total_units": self.total_units,
            "items": [item.to_dict() for item in self.items]
        }

    def to_flat_rows(self) -> List[Dict[str, Any]]:
        """
        Converts sale items into flat rows suitable for appending to sales.csv.
        Each row contains transaction metadata + specific product line item details.
        """
        rows = []
        for item in self.items:
            rows.append({
                "sale_id": self.sale_id,
                "timestamp": self.timestamp,
                "customer_name": self.customer_name,
                "payment_method": self.payment_method,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "category": item.category,
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "subtotal": item.subtotal,
                "tax_amount": round((item.subtotal / (self.subtotal or 1)) * self.tax_amount, 2),
                "total_amount": round(item.subtotal + (item.subtotal / (self.subtotal or 1)) * self.tax_amount, 2)
            })
        return rows

    def __repr__(self) -> str:
        return f"<Sale {self.sale_id} - ${self.total_amount:.2f} ({self.total_units} units)>"

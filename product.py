"""
Product Class Representation
Encapsulates individual product attributes, validations, and operations.
"""

from typing import Dict, Any
from .exceptions import InvalidProductDataError


class Product:
    """Represents a product item in the inventory system."""

    def __init__(self, product_id: str, name: str, category: str, price: float, quantity: int):
        self.product_id = str(product_id).strip()
        self.name = str(name).strip()
        self.category = str(category).strip() or "General"
        self.price = float(price)
        self.quantity = int(quantity)

        self.validate()

    def validate(self) -> None:
        """Validates product fields according to business rules."""
        if not self.product_id:
            raise InvalidProductDataError("Product ID", self.product_id, "Product ID cannot be empty.")
        if not self.name:
            raise InvalidProductDataError("Product Name", self.name, "Product name cannot be empty.")
        if self.price < 0:
            raise InvalidProductDataError("Price", self.price, "Price must be a non-negative number.")
        if self.quantity < 0:
            raise InvalidProductDataError("Quantity", self.quantity, "Quantity cannot be negative.")

    def update_stock(self, quantity_delta: int) -> int:
        """
        Updates product quantity by a delta (positive for restock, negative for deduction).
        Returns the new quantity.
        """
        new_quantity = self.quantity + quantity_delta
        if new_quantity < 0:
            raise InvalidProductDataError("Quantity", new_quantity, "Resulting quantity cannot be negative.")
        self.quantity = new_quantity
        return self.quantity

    def set_quantity(self, quantity: int) -> int:
        """Sets an exact stock quantity."""
        if quantity < 0:
            raise InvalidProductDataError("Quantity", quantity, "Quantity cannot be negative.")
        self.quantity = quantity
        return self.quantity

    def update_details(self, name: str = None, category: str = None, price: float = None) -> None:
        """Updates product metadata like name, category, and price."""
        if name is not None:
            name_clean = str(name).strip()
            if not name_clean:
                raise InvalidProductDataError("Product Name", name, "Product name cannot be empty.")
            self.name = name_clean

        if category is not None:
            self.category = str(category).strip() or "General"

        if price is not None:
            p = float(price)
            if p < 0:
                raise InvalidProductDataError("Price", p, "Price must be non-negative.")
            self.price = p

    @property
    def total_stock_value(self) -> float:
        """Computes the total inventory valuation for this product."""
        return round(self.price * self.quantity, 2)

    def is_low_stock(self, threshold: int = 5) -> bool:
        """Checks if product quantity is less than or equal to threshold."""
        return self.quantity <= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Converts Product object to a dictionary representation."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "category": self.category,
            "price": round(self.price, 2),
            "quantity": self.quantity,
            "stock_value": self.total_stock_value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        """Instantiates a Product instance from a dictionary."""
        return cls(
            product_id=data.get("product_id"),
            name=data.get("name"),
            category=data.get("category", "General"),
            price=float(data.get("price", 0.0)),
            quantity=int(data.get("quantity", 0))
        )

    def __repr__(self) -> str:
        return f"<Product {self.product_id} - {self.name} (${self.price:.2f}, Qty: {self.quantity})>"

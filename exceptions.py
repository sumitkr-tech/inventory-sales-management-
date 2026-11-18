"""
Custom Exception Classes for Inventory & Sales Management System
Handles domain-specific errors such as invalid product IDs and insufficient stock.
"""

class InventorySalesException(Exception):
    """Base exception for inventory and sales operations."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {"error": self.__class__.__name__, "message": self.message, "status_code": self.status_code}


class InvalidProductIDError(InventorySalesException):
    """Raised when a product ID does not exist or has an invalid format."""
    def __init__(self, product_id: str, message: str = None):
        msg = message or f"Product with ID '{product_id}' does not exist or is invalid."
        super().__init__(msg, status_code=404)
        self.product_id = product_id


class InsufficientStockError(InventorySalesException):
    """Raised when the requested sale quantity exceeds available stock."""
    def __init__(self, product_id: str, product_name: str, requested: int, available: int):
        msg = (
            f"Insufficient stock for product '{product_name}' (ID: {product_id}). "
            f"Requested: {requested}, Available in stock: {available}."
        )
        super().__init__(msg, status_code=400)
        self.product_id = product_id
        self.product_name = product_name
        self.requested = requested
        self.available = available


class DuplicateProductIDError(InventorySalesException):
    """Raised when attempting to add a product with an ID that already exists."""
    def __init__(self, product_id: str):
        msg = f"A product with ID '{product_id}' already exists in inventory."
        super().__init__(msg, status_code=409)
        self.product_id = product_id


class InvalidProductDataError(InventorySalesException):
    """Raised when product validation fails (e.g. negative price or quantity)."""
    def __init__(self, field: str, value, reason: str):
        msg = f"Invalid data for '{field}' ({value}): {reason}"
        super().__init__(msg, status_code=400)
        self.field = field
        self.value = value

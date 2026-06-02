"""Product Service validation policies."""

from decimal import Decimal


def ensure_product_values(*, price: Decimal, stock_quantity: int) -> None:
    if price < 0:
        raise ValueError("Product price cannot be negative")
    if stock_quantity < 0:
        raise ValueError("Product stock cannot be negative")

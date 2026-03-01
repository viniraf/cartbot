"""Input validation helpers shared across handlers.

This module lives in `app/common` to avoid accidental dependency cycles.
Currently it provides a parser for the new pipe-based `/add_item` syntax.
"""

from typing import Tuple


def parse_add_item_input(text: str) -> Tuple[str, int, float]:
    """Parse a string containing name, quantity and price separated by pipes.

    Expected format:
        Name | qty | price

    Examples:
        "Milk | 2 | 1.50"
        "Mortadela 200g | 1 | 11.50"

    Args:
        text: The raw text (everything after the command word).

    Returns:
        A tuple of (name, quantity, unit_price).

    Raises:
        ValueError: When the format is incorrect or numbers cannot be parsed.
    """
    parts = text.split("|")
    if len(parts) != 3:
        raise ValueError("Expected format: Name | qty | price")

    name = parts[0].strip()
    if not name:
        raise ValueError("Item name must not be empty")

    qty_str = parts[1].strip()
    price_str = parts[2].strip()

    try:
        quantity = int(qty_str)
    except ValueError:
        raise ValueError("Quantity must be an integer")

    try:
        unit_price = float(price_str)
    except ValueError:
        raise ValueError("Price must be a number")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")
    if unit_price <= 0:
        raise ValueError("Price must be greater than zero")

    return name, quantity, unit_price

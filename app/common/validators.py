"""Input validation helpers shared across handlers.

This module provides parsers for the new comma-based `/add` syntax (Phase 9.9).
"""

from typing import Tuple


def parse_add_item_input(text: str) -> Tuple[str, int, float]:
    """Parse a string containing price/quantity/name separated by commas.

    Expected formats (Phase 9.9):
        price,item_name        (default quantity = 1)
        price,quantity,item_name

    Examples:
        "19.90,feijao"              → ("feijao", 1, 19.90)
        "20.50,2,file de frango"    → ("file de frango", 2, 20.50)
        "5.30,miojo"                → ("miojo", 1, 5.30)

    Args:
        text: The raw text from a single item line.

    Returns:
        A tuple of (name, quantity, unit_price).

    Raises:
        ValueError: When the format is incorrect or numbers cannot be parsed.
    """
    parts = [p.strip() for p in text.split(",")]
    
    # Must have at least 2 parts: price,name OR 3 parts: price,qty,name
    if len(parts) < 2 or len(parts) > 3:
        raise ValueError("Expected: price,item OR price,qty,item")
    
    price_str = parts[0]
    
    if len(parts) == 2:
        # Format: price,name (quantity defaults to 1)
        name = parts[1]
        quantity = 1
    else:
        # Format: price,qty,name
        qty_str = parts[1]
        name = parts[2]
        try:
            quantity = int(qty_str)
        except ValueError:
            raise ValueError("Quantity must be an integer")
    
    # Validate name
    if not name:
        raise ValueError("Item name must not be empty")
    
    # Validate price
    try:
        unit_price = float(price_str)
    except ValueError:
        raise ValueError("Price must be a number")
    
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")
    if unit_price <= 0:
        raise ValueError("Price must be greater than zero")
    
    return name, quantity, unit_price

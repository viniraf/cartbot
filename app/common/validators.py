"""Input validation helpers shared across handlers.

This module provides parsers for the new comma-based `/add` syntax (Phase 9.9-9.10).
"""

from typing import Tuple, TypedDict, List


class ParsedItem(TypedDict):
    """Parsed item from /add command (Phase 9.10)."""
    name: str
    quantity: int
    price: float


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


def parse_add_input(raw_text: str) -> List[ParsedItem]:
    """Parse /add command input supporting both inline and batch formats (Phase 9.10).

    Supported formats:

    Inline:
        /add 19.90,feijao
        /add 20.50,2,file de frango

    Batch:
        /add
        19.90,feijao
        20.50,2,file de frango
        5.30,miojo

    Parsing strategy:
        1. Split raw_text by newlines
        2. First line is the command (/add)
        3. Remaining lines are item definitions
        4. If first line has content after /add, treat as inline
        5. Validate ALL items before returning (fail entirely if any invalid)

    Args:
        raw_text: The raw message text from the user (e.g., "/add 19.90,feijao" or "/add\n19.90,feijao...")

    Returns:
        List of ParsedItem dictionaries with name, quantity, price.

    Raises:
        ValueError: If any item format is invalid, with helpful error message.
    """
    # Split into lines
    lines = raw_text.split("\n")
    
    if not lines:
        raise ValueError("No input provided")
    
    # First line contains the /add command
    command_line = lines[0].strip()
    
    # Extract inline content (everything after /add)
    # Expected format: /add or /add <content>
    if not command_line.startswith("/add"):
        raise ValueError("Invalid command")
    
    inline_content = command_line[4:].strip()  # Everything after "/add"
    
    # Collect items from both inline and batch
    items_to_parse = []
    
    # Add inline item if present
    if inline_content:
        items_to_parse.append(inline_content)
    
    # Add batch items (lines after the command)
    if len(lines) > 1:
        for line in lines[1:]:
            line = line.strip()
            if line:  # Skip empty lines
                items_to_parse.append(line)
    
    # Fail if no items at all
    if not items_to_parse:
        raise ValueError("No items provided")
    
    # Parse and validate ALL items (fail entirely if ANY invalid)
    parsed_items: List[ParsedItem] = []
    for item_text in items_to_parse:
        try:
            name, qty, price = parse_add_item_input(item_text)
            parsed_items.append({
                "name": name,
                "quantity": qty,
                "price": price
            })
        except ValueError as e:
            # Fail entirely with detailed error
            raise ValueError(f"Invalid item format: {item_text}\n\nError: {str(e)}\n\nExpected: price,item OR price,qty,item")
    
    return parsed_items

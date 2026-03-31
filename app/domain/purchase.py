"""Purchase domain entity and value objects.

Pure Python business logic for shopping list purchases.
No database, Telegram, or framework knowledge.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .exceptions import ValidationError, NotFoundError
from app.common.formatters import format_currency


@dataclass(frozen=True)
class PurchaseItem:
    """Value object representing a single item in a purchase.

    Immutable - create new instances instead of modifying.
    """

    name: str
    quantity: int
    unit_price: float

    def __post_init__(self):
        """Validate invariants after initialization."""
        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Item name must be a non-empty string")

        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValidationError(f"Item quantity must be > 0, got {self.quantity}")

        if not isinstance(self.unit_price, (int, float)) or self.unit_price <= 0:
            raise ValidationError(f"Item unit_price must be > 0, got {self.unit_price}")

    def total_price(self) -> float:
        """Calculate total price for this item (quantity × unit_price)."""
        return self.quantity * self.unit_price

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.name} × {self.quantity} @ {format_currency(self.unit_price)} = "
            f"{format_currency(self.total_price())}"
        )


class Purchase:
    """Aggregate root for shopping list purchases.

    Represents a single purchase (shopping list) with multiple items.
    Items are added/removed through methods, not direct list mutation.
    """

    def __init__(
        self,
        id: Optional[int] = None,
        items: Optional[List[PurchaseItem]] = None,
        created_at: Optional[str] = None,
        finished_at: Optional[str] = None,
        store_name: Optional[str] = None,
    ):
        """Initialize a purchase.

        Args:
            id: Purchase ID (None for new purchases).
            items: List of PurchaseItem objects (default: empty).
            created_at: ISO timestamp when created (default: now).
            finished_at: ISO timestamp when finished (default: None for active).
        """
        if store_name is None or not isinstance(store_name, str):
            raise ValidationError("store_name is required and must be a string")

        normalized_store_name = store_name.strip()
        if not normalized_store_name:
            raise ValidationError("store_name must be a non-empty string")

        self.id = id
        self.items: List[PurchaseItem] = items or []
        self.created_at = created_at or datetime.now().isoformat()
        self.finished_at = finished_at
        self.store_name = normalized_store_name

    def add_item(self, name: str, quantity: int, unit_price: float) -> None:
        """Add an item to the purchase.

        Args:
            name: Item name.
            quantity: Number of units.
            unit_price: Price per unit.

        Raises:
            ValidationError: If any argument violates invariants.
        """
        item = PurchaseItem(name=name, quantity=quantity, unit_price=unit_price)
        self.items.append(item)

    def remove_item(self, index: int) -> None:
        """Remove an item by index (0-based).

        Args:
            index: Zero-based index of item to remove.

        Raises:
            NotFoundError: If index is out of range.
        """
        if not isinstance(index, int) or index < 0 or index >= len(self.items):
            raise NotFoundError(f"Item index {index} not found (purchase has {len(self.items)} items)")

        self.items.pop(index)

    def total(self) -> float:
        """Calculate total cost of all items.

        Returns:
            Sum of all item totals.
        """
        return sum(item.total_price() for item in self.items)

    def item_count(self) -> int:
        """Count items in purchase.

        Returns:
            Number of items.
        """
        return len(self.items)

    def is_active(self) -> bool:
        """Check if purchase is still active (not finished).

        Returns:
            True if finished_at is None, False otherwise.
        """
        return self.finished_at is None

    def finish(self) -> None:
        """Mark purchase as finished.

        Sets finished_at to current time.
        """
        self.finished_at = datetime.now().isoformat()

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "ACTIVE" if self.is_active() else "FINISHED"
        return (
            f"Purchase #{self.id} [{status}] | Items: {self.item_count()} | "
            f"Total: {format_currency(self.total())}"
        )

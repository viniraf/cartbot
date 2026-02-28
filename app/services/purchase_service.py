"""PurchaseService - orchestrates domain logic and repository persistence.

Services are stateless coordinators that:
1. Load entities from repository
2. Execute business logic on domain objects
3. Persist changes back to repository
4. Translate domain exceptions for consumers

Never put SQL, validation, or calculation logic here.
"""

import logging
from typing import Optional

from app.domain import Purchase, NotFoundError, ValidationError
from app.infra.repositories import BaseRepository

logger = logging.getLogger(__name__)


class PurchaseService:
    """Service for purchase operations.

    Orchestrates interactions between domain objects and persistence layer.
    All validation and calculation happens in domain; this just coordinates.
    """

    def __init__(self, repository: BaseRepository):
        """Initialize service with a repository.

        Args:
            repository: Repository implementation (e.g., SQLitePurchaseRepository).
        """
        self.repository = repository

    def start_purchase(self) -> int:
        """Start a new purchase and save to repository.

        Returns:
            ID of the newly created purchase.

        Example:
            purchase_id = service.start_purchase()
            # Now purchase_id can be used with add_item, finish_purchase, etc.
        """
        # Create new domain entity
        purchase = Purchase()

        # Convert to dict for persistence
        purchase_dict = self._purchase_to_dict(purchase)

        # Persist to repository (sets purchase_dict['id'] as side effect)
        self.repository.save(purchase_dict)

        # Update the domain object ID
        purchase.id = purchase_dict['id']

        logger.info(f"Purchase started with ID {purchase.id}")
        return purchase.id

    def add_item(self, purchase_id: int, name: str, quantity: int, unit_price: float) -> float:
        """Add an item to an existing purchase.

        Args:
            purchase_id: ID of purchase to modify.
            name: Item name.
            quantity: Number of units.
            unit_price: Price per unit.

        Returns:
            Updated total cost of the purchase.

        Raises:
            NotFoundError: If purchase not found.
            ValidationError: If item data is invalid.

        Example:
            total = service.add_item(123, "Milk", 2, 1.50)
            print(f"New total: ${total:.2f}")
        """
        # Load purchase from repository
        purchase = self.repository.get_by_id(purchase_id)
        if purchase is None:
            raise NotFoundError(f"Purchase {purchase_id} not found")

        # Reconstruct domain object from dict
        purchase_obj = self._dict_to_purchase(purchase)

        # Execute business logic on domain object
        # (add_item validates quantity > 0, unit_price > 0, etc.)
        purchase_obj.add_item(name, quantity, unit_price)

        # Persist changes
        self.repository.save(self._purchase_to_dict(purchase_obj))

        logger.info(f"Item '{name}' added to purchase {purchase_id}")
        return purchase_obj.total()

    def edit_item(
        self,
        purchase_id: int,
        item_index: int,
        quantity: Optional[int] = None,
        unit_price: Optional[float] = None,
    ) -> float:
        """Edit an item in a purchase (quantity and/or unit_price).

        Args:
            purchase_id: ID of purchase to modify.
            item_index: Zero-based index of item to edit.
            quantity: New quantity (optional).
            unit_price: New unit price (optional).

        Returns:
            Updated total cost of the purchase.

        Raises:
            NotFoundError: If purchase or item index not found.
            ValidationError: If quantity or unit_price invalid.
        """
        from app.domain import PurchaseItem

        purchase = self.repository.get_by_id(purchase_id)
        if purchase is None:
            raise NotFoundError(f"Purchase {purchase_id} not found")

        purchase_obj = self._dict_to_purchase(purchase)

        if item_index < 0 or item_index >= len(purchase_obj.items):
            raise NotFoundError(
                f"Item index {item_index} not found (purchase has {len(purchase_obj.items)} items)"
            )

        if quantity is None and unit_price is None:
            raise ValidationError("Must provide quantity or unit_price to edit")

        item = purchase_obj.items[item_index]
        new_qty = quantity if quantity is not None else item.quantity
        new_price = unit_price if unit_price is not None else item.unit_price

        new_item = PurchaseItem(name=item.name, quantity=new_qty, unit_price=new_price)
        purchase_obj.items[item_index] = new_item

        self.repository.save(self._purchase_to_dict(purchase_obj))

        logger.info(f"Item {item_index} edited in purchase {purchase_id}")
        return purchase_obj.total()

    def remove_item(self, purchase_id: int, item_index: int) -> float:
        """Remove an item from a purchase by index (0-based).

        Args:
            purchase_id: ID of purchase to modify.
            item_index: Zero-based index of item to remove.

        Returns:
            Updated total cost of the purchase.

        Raises:
            NotFoundError: If purchase or item index not found.

        Example:
            total = service.remove_item(123, 0)  # Remove first item
            print(f"New total: ${total:.2f}")
        """
        # Load purchase from repository
        purchase = self.repository.get_by_id(purchase_id)
        if purchase is None:
            raise NotFoundError(f"Purchase {purchase_id} not found")

        # Reconstruct domain object from dict
        purchase_obj = self._dict_to_purchase(purchase)

        # Execute business logic on domain object
        # (remove_item validates index is in range)
        purchase_obj.remove_item(item_index)

        # Persist changes
        self.repository.save(self._purchase_to_dict(purchase_obj))

        logger.info(f"Item {item_index} removed from purchase {purchase_id}")
        return purchase_obj.total()

    def get_purchase(self, purchase_id: int) -> dict:
        """Retrieve a purchase with all details.

        Args:
            purchase_id: ID of purchase to retrieve.

        Returns:
            Purchase dict with id, items, totals, timestamps, etc.

        Raises:
            NotFoundError: If purchase not found.

        Example:
            purchase = service.get_purchase(123)
            print(f"Total items: {purchase['item_count']}")
            print(f"Total cost: ${purchase['total']:.2f}")
        """
        # Load from repository
        purchase = self.repository.get_by_id(purchase_id)
        if purchase is None:
            raise NotFoundError(f"Purchase {purchase_id} not found")

        # Reconstruct domain object to enrich with calculated fields
        purchase_obj = self._dict_to_purchase(purchase)

        # Return enriched dict with computed values
        result = self._purchase_to_dict(purchase_obj)
        result['item_count'] = purchase_obj.item_count()
        result['total'] = purchase_obj.total()
        result['is_active'] = purchase_obj.is_active()

        logger.debug(f"Retrieved purchase {purchase_id}")
        return result

    def finish_purchase(self, purchase_id: int) -> dict:
        """Mark a purchase as finished.

        Args:
            purchase_id: ID of purchase to finish.

        Returns:
            Finished purchase dict with final totals.

        Raises:
            NotFoundError: If purchase not found.

        Example:
            result = service.finish_purchase(123)
            print(f"Final total: ${result['total']:.2f}")
        """
        # Load purchase from repository
        purchase = self.repository.get_by_id(purchase_id)
        if purchase is None:
            raise NotFoundError(f"Purchase {purchase_id} not found")

        # Reconstruct domain object
        purchase_obj = self._dict_to_purchase(purchase)

        # Execute business logic: mark as finished
        purchase_obj.finish()

        # Persist changes
        purchase_dict = self._purchase_to_dict(purchase_obj)
        self.repository.save(purchase_dict)

        logger.info(f"Purchase {purchase_id} finished with total ${purchase_obj.total():.2f}")

        # Return final state
        result = self._purchase_to_dict(purchase_obj)
        result['item_count'] = purchase_obj.item_count()
        result['total'] = purchase_obj.total()
        result['is_active'] = purchase_obj.is_active()
        return result

    # Helper methods for domain ↔ dict conversion

    @staticmethod
    def _dict_to_purchase(purchase_dict: dict) -> Purchase:
        """Convert dict (from repository) to Purchase domain object.

        Args:
            purchase_dict: Dict with id, items, created_at, finished_at.

        Returns:
            Purchase domain object.
        """
        from app.domain import PurchaseItem

        purchase = Purchase(
            id=purchase_dict.get('id'),
            created_at=purchase_dict.get('created_at'),
            finished_at=purchase_dict.get('finished_at'),
        )

        # Reconstruct items from dicts
        for item_dict in purchase_dict.get('items', []):
            purchase.items.append(
                PurchaseItem(
                    name=item_dict['name'],
                    quantity=item_dict['quantity'],
                    unit_price=item_dict['unit_price'],
                )
            )

        return purchase

    @staticmethod
    def _purchase_to_dict(purchase: Purchase) -> dict:
        """Convert Purchase domain object to dict (for repository).

        Args:
            purchase: Purchase domain object.

        Returns:
            Dict with id, items, created_at, finished_at.
        """
        return {
            'id': purchase.id,
            'created_at': purchase.created_at,
            'finished_at': purchase.finished_at,
            'items': [
                {
                    'name': item.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                }
                for item in purchase.items
            ],
        }

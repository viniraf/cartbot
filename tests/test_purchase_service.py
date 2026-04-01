"""Tests for PurchaseService (orchestration layer)."""

import pytest
from datetime import datetime

from app.services import PurchaseService
from app.domain import NotFoundError, ValidationError
from app.infra.repositories import BaseRepository


class MockRepository(BaseRepository):
    """Mock repository for testing (stores in memory)."""

    def __init__(self):
        """Initialize empty storage."""
        self.storage = {}
        self.next_id = 1

    def save(self, entity):
        """Save entity and assign ID if new."""
        if entity.get('id') is None:
            entity['id'] = self.next_id
            self.next_id += 1

        self.storage[entity['id']] = entity.copy()

    def get_by_id(self, entity_id):
        """Get entity by ID."""
        return self.storage.get(entity_id)

    def delete(self, entity_id):
        """Delete entity by ID."""
        self.storage.pop(entity_id, None)


@pytest.fixture
def mock_repo():
    """Create a fresh mock repository for each test."""
    return MockRepository()


@pytest.fixture
def service(mock_repo):
    """Create a service with mock repository."""
    return PurchaseService(mock_repo)


class TestPurchaseServiceStartPurchase:
    """Test start_purchase() method."""

    def test_start_purchase_creates_new(self, service):
        """Should create new purchase and return ID."""
        purchase_id = service.start_purchase()

        assert isinstance(purchase_id, int)
        assert purchase_id > 0

    def test_start_purchase_increments_ids(self, service):
        """Should assign sequential IDs."""
        id1 = service.start_purchase()
        id2 = service.start_purchase()
        id3 = service.start_purchase()

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_start_purchase_persists_to_repo(self, service, mock_repo):
        """Should save purchase to repository."""
        purchase_id = service.start_purchase()

        stored = mock_repo.get_by_id(purchase_id)
        assert stored is not None
        assert stored['id'] == purchase_id
        assert stored['items'] == []
        assert stored['created_at'] is not None
        assert stored['finished_at'] is None

    def test_start_multiple_purchases_independent(self, service):
        """Multiple purchases should be independent."""
        id1 = service.start_purchase()
        id2 = service.start_purchase()

        p1 = service.get_purchase(id1)
        p2 = service.get_purchase(id2)

        assert p1['id'] == id1
        assert p2['id'] == id2
        assert p1['total'] == 0
        assert p2['total'] == 0


class TestPurchaseServiceAddItem:
    """Test add_item() method."""

    def test_add_item_to_purchase(self, service):
        """Should add item to existing purchase."""
        purchase_id = service.start_purchase()

        total = service.add_item(purchase_id, "Milk", 2, 1.50)

        assert total == 3.0

    def test_add_item_updates_purchase(self, service, mock_repo):
        """Should persist item to repository."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)

        stored = mock_repo.get_by_id(purchase_id)
        assert len(stored['items']) == 1
        assert stored['items'][0]['name'] == "Milk"
        assert stored['items'][0]['quantity'] == 2
        assert stored['items'][0]['unit_price'] == 1.50

    def test_add_multiple_items(self, service):
        """Should add multiple items and accumulate total."""
        purchase_id = service.start_purchase()

        service.add_item(purchase_id, "Milk", 2, 1.50)  # 3.00
        total = service.add_item(purchase_id, "Bread", 1, 2.00)  # + 2.00

        assert abs(total - 5.0) < 0.01

    def test_add_item_validates_quantity(self, service):
        """Should reject negative quantity."""
        purchase_id = service.start_purchase()

        with pytest.raises(ValidationError):
            service.add_item(purchase_id, "Milk", -1, 1.50)

    def test_add_item_validates_price(self, service):
        """Should reject non-positive price."""
        purchase_id = service.start_purchase()

        with pytest.raises(ValidationError):
            service.add_item(purchase_id, "Milk", 1, 0)

        with pytest.raises(ValidationError):
            service.add_item(purchase_id, "Milk", 1, -1.0)

    def test_add_item_to_nonexistent_purchase(self, service):
        """Should raise NotFoundError if purchase doesn't exist."""
        with pytest.raises(NotFoundError, match="Purchase 999 not found"):
            service.add_item(999, "Milk", 1, 1.50)

    def test_add_item_returns_updated_total(self, service):
        """Should return correct total after each add."""
        purchase_id = service.start_purchase()

        t1 = service.add_item(purchase_id, "Milk", 2, 1.50)
        assert t1 == 3.0

        t2 = service.add_item(purchase_id, "Eggs", 12, 0.25)
        assert abs(t2 - 6.0) < 0.01


class TestPurchaseServiceRemoveItem:
    """Test remove_item() method."""

    def test_remove_item_by_index(self, service):
        """Should remove item by zero-based index."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)
        service.add_item(purchase_id, "Eggs", 1, 0.25)

        total = service.remove_item(purchase_id, 1)  # Remove Bread

        assert abs(total - 1.75) < 0.01

    def test_remove_item_persists_to_repo(self, service, mock_repo):
        """Should persist removal to repository."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)

        service.remove_item(purchase_id, 0)

        stored = mock_repo.get_by_id(purchase_id)
        assert len(stored['items']) == 1
        assert stored['items'][0]['name'] == "Bread"

    def test_remove_first_item(self, service):
        """Should remove first item."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)

        total = service.remove_item(purchase_id, 0)

        assert total == 2.0

    def test_remove_last_item(self, service):
        """Should remove last item."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)

        total = service.remove_item(purchase_id, 1)

        assert total == 1.50

    def test_remove_item_invalid_index(self, service):
        """Should raise NotFoundError for invalid index."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)

        with pytest.raises(NotFoundError):
            service.remove_item(purchase_id, 999)

    def test_remove_from_nonexistent_purchase(self, service):
        """Should raise NotFoundError if purchase doesn't exist."""
        with pytest.raises(NotFoundError, match="Purchase 999 not found"):
            service.remove_item(999, 0)

    def test_remove_last_item_leaves_empty_list(self, service):
        """Should allow removing all items."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)

        total = service.remove_item(purchase_id, 0)

        assert total == 0


class TestPurchaseServiceEditItem:
    """Test edit_item() method."""

    def test_edit_item_quantity(self, service):
        """Should update item quantity and return new total."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)

        total = service.edit_item(purchase_id, 0, quantity=5)

        assert total == 7.50  # 5 * 1.50
        purchase = service.get_purchase(purchase_id)
        assert purchase["items"][0]["quantity"] == 5

    def test_edit_item_price(self, service):
        """Should update item unit_price and return new total."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)

        total = service.edit_item(purchase_id, 0, unit_price=2.00)

        assert total == 4.00  # 2 * 2.00
        purchase = service.get_purchase(purchase_id)
        assert purchase["items"][0]["unit_price"] == 2.00

    def test_edit_item_both_quantity_and_price(self, service):
        """Should update both quantity and price."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)

        total = service.edit_item(purchase_id, 0, quantity=3, unit_price=2.00)

        assert total == 6.00
        purchase = service.get_purchase(purchase_id)
        assert purchase["items"][0]["quantity"] == 3
        assert purchase["items"][0]["unit_price"] == 2.00

    def test_edit_item_preserves_name(self, service):
        """Should preserve item name when editing."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Organic Milk", 1, 3.00)

        service.edit_item(purchase_id, 0, quantity=2)

        purchase = service.get_purchase(purchase_id)
        assert purchase["items"][0]["name"] == "Organic Milk"

    def test_edit_item_invalid_index(self, service):
        """Should raise NotFoundError for invalid index."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)

        with pytest.raises(NotFoundError):
            service.edit_item(purchase_id, 999, quantity=2)

    def test_edit_item_nonexistent_purchase(self, service):
        """Should raise NotFoundError if purchase doesn't exist."""
        with pytest.raises(NotFoundError, match="Purchase 999 not found"):
            service.edit_item(999, 0, quantity=2)

    def test_edit_item_requires_quantity_or_price(self, service):
        """Should raise ValidationError if neither quantity nor price provided."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)

        with pytest.raises(ValidationError, match="Must provide"):
            service.edit_item(purchase_id, 0)


class TestPurchaseServiceGetPurchase:
    """Test get_purchase() method."""

    def test_get_purchase_returns_dict(self, service):
        """Should return purchase as dict."""
        purchase_id = service.start_purchase()

        purchase = service.get_purchase(purchase_id)

        assert isinstance(purchase, dict)
        assert purchase['id'] == purchase_id

    def test_get_purchase_includes_items(self, service):
        """Should include all items."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)

        purchase = service.get_purchase(purchase_id)

        assert len(purchase['items']) == 2
        assert purchase['items'][0]['name'] == "Milk"
        assert purchase['items'][1]['name'] == "Bread"

    def test_get_purchase_includes_totals(self, service):
        """Should include calculated totals."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)

        purchase = service.get_purchase(purchase_id)

        assert purchase['item_count'] == 3  # Sum of quantities: 2 + 1
        assert abs(purchase['total'] - 5.0) < 0.01

    def test_get_purchase_includes_status(self, service):
        """Should include active/finished status."""
        purchase_id = service.start_purchase()

        purchase = service.get_purchase(purchase_id)

        assert purchase['is_active'] is True
        assert purchase['finished_at'] is None

    def test_get_purchase_not_found(self, service):
        """Should raise NotFoundError if purchase doesn't exist."""
        with pytest.raises(NotFoundError, match="Purchase 999 not found"):
            service.get_purchase(999)

    def test_get_empty_purchase(self, service):
        """Should return valid dict for empty purchase."""
        purchase_id = service.start_purchase()

        purchase = service.get_purchase(purchase_id)

        assert purchase['item_count'] == 0
        assert purchase['total'] == 0
        assert purchase['is_active'] is True


class TestPurchaseServiceFinishPurchase:
    """Test finish_purchase() method."""

    def test_finish_purchase_marks_complete(self, service):
        """Should mark purchase as finished."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)

        result = service.finish_purchase(purchase_id)

        assert result['is_active'] is False
        assert result['finished_at'] is not None

    def test_finish_purchase_persists(self, service, mock_repo):
        """Should persist finished status to repository."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)

        service.finish_purchase(purchase_id)

        stored = mock_repo.get_by_id(purchase_id)
        assert stored['finished_at'] is not None

    def test_finish_purchase_returns_final_state(self, service):
        """Should return final purchase with totals."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)

        result = service.finish_purchase(purchase_id)

        assert result['item_count'] == 3  # Sum of quantities: 2 + 1
        assert abs(result['total'] - 5.0) < 0.01
        assert result['is_active'] is False

    def test_finish_empty_purchase(self, service):
        """Should allow finishing empty purchase."""
        purchase_id = service.start_purchase()

        result = service.finish_purchase(purchase_id)

        assert result['item_count'] == 0
        assert result['total'] == 0
        assert result['is_active'] is False

    def test_finish_nonexistent_purchase(self, service):
        """Should raise NotFoundError if purchase doesn't exist."""
        with pytest.raises(NotFoundError, match="Purchase 999 not found"):
            service.finish_purchase(999)


class TestPurchaseServiceIntegration:
    """Integration tests for complete workflows."""

    def test_complete_workflow(self, service):
        """Test complete purchase lifecycle."""
        # Start
        purchase_id = service.start_purchase()
        p = service.get_purchase(purchase_id)
        assert p['is_active'] is True
        assert p['item_count'] == 0

        # Add items
        service.add_item(purchase_id, "Milk", 2, 1.50)
        service.add_item(purchase_id, "Bread", 1, 2.00)
        service.add_item(purchase_id, "Eggs", 12, 0.25)
        p = service.get_purchase(purchase_id)
        assert p['item_count'] == 15  # Sum of quantities: 2 + 1 + 12
        assert abs(p['total'] - 8.0) < 0.01

        # Remove one
        service.remove_item(purchase_id, 1)
        p = service.get_purchase(purchase_id)
        assert p['item_count'] == 14  # Remaining quantities: 2 + 12 = 14
        assert abs(p['total'] - 6.0) < 0.01

        # Finish
        result = service.finish_purchase(purchase_id)
        assert result['is_active'] is False
        assert abs(result['total'] - 6.0) < 0.01

    def test_multiple_purchases_concurrent(self, service):
        """Should handle multiple concurrent purchases."""
        # Start multiple purchases
        id1 = service.start_purchase()
        id2 = service.start_purchase()
        id3 = service.start_purchase()

        # Add items to first
        service.add_item(id1, "Milk", 1, 1.50)

        # Add items to second
        service.add_item(id2, "Bread", 1, 2.00)
        service.add_item(id2, "Cheese", 1, 3.00)

        # Verify independence
        p1 = service.get_purchase(id1)
        p2 = service.get_purchase(id2)
        p3 = service.get_purchase(id3)

        assert p1['total'] == 1.50
        assert abs(p2['total'] - 5.0) < 0.01
        assert p3['total'] == 0

        # Finish first and second
        service.finish_purchase(id1)
        service.finish_purchase(id2)

        # Third should still be active
        p3 = service.get_purchase(id3)
        assert p3['is_active'] is True

    def test_error_handling_preserves_state(self, service):
        """Service should not corrupt state when errors occur."""
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 1, 1.50)

        # Attempt invalid operation
        try:
            service.add_item(purchase_id, "Bad", -1, 1.0)
        except ValidationError:
            pass

        # State should be unchanged
        p = service.get_purchase(purchase_id)
        assert p['item_count'] == 1
        assert abs(p['total'] - 1.50) < 0.01

    def test_precision_with_floating_point(self, service):
        """Should maintain precision with floating point arithmetic."""
        purchase_id = service.start_purchase()

        service.add_item(purchase_id, "Item1", 1, 1.99)
        service.add_item(purchase_id, "Item2", 1, 2.49)
        service.add_item(purchase_id, "Item3", 1, 1.52)

        p = service.get_purchase(purchase_id)

        # Should sum to 6.00
        assert abs(p['total'] - 6.0) < 0.01

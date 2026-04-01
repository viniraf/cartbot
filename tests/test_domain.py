"""Tests for domain layer (Purchase, PurchaseItem, exceptions)."""

import pytest
from datetime import datetime

from app.domain import (
    Purchase,
    PurchaseItem,
    DomainError,
    ValidationError,
    NotFoundError,
)


class TestPurchaseItemValueObject:
    """Test PurchaseItem value object and invariants."""

    def test_create_valid_item(self):
        """Should create valid item with positive quantity and price."""
        item = PurchaseItem(name="Milk", quantity=2, unit_price=1.50)

        assert item.name == "Milk"
        assert item.quantity == 2
        assert item.unit_price == 1.50

    def test_item_is_immutable(self):
        """PurchaseItem should be frozen (immutable)."""
        item = PurchaseItem(name="Milk", quantity=2, unit_price=1.50)

        with pytest.raises(AttributeError):
            item.name = "Bread"

    def test_item_total_price(self):
        """Should calculate total price correctly."""
        item = PurchaseItem(name="Milk", quantity=2, unit_price=1.50)

        assert item.total_price() == 3.0

    def test_item_total_price_with_floats(self):
        """Should handle float prices correctly."""
        item = PurchaseItem(name="Item", quantity=3, unit_price=2.99)

        assert abs(item.total_price() - 8.97) < 0.01

    def test_item_validates_name_required(self):
        """Should reject empty name."""
        with pytest.raises(ValidationError, match="name must be a non-empty string"):
            PurchaseItem(name="", quantity=1, unit_price=1.0)

    def test_item_validates_name_is_string(self):
        """Should reject non-string name."""
        with pytest.raises(ValidationError, match="name must be a non-empty string"):
            PurchaseItem(name=123, quantity=1, unit_price=1.0)

    def test_item_validates_quantity_positive(self):
        """Should reject zero or negative quantity."""
        with pytest.raises(ValidationError, match="quantity must be > 0"):
            PurchaseItem(name="Milk", quantity=0, unit_price=1.0)

        with pytest.raises(ValidationError, match="quantity must be > 0"):
            PurchaseItem(name="Milk", quantity=-1, unit_price=1.0)

    def test_item_validates_quantity_is_integer(self):
        """Should reject float quantity."""
        with pytest.raises(ValidationError, match="quantity must be > 0"):
            PurchaseItem(name="Milk", quantity=1.5, unit_price=1.0)

    def test_item_validates_unit_price_positive(self):
        """Should reject zero or negative price."""
        with pytest.raises(ValidationError, match="unit_price must be > 0"):
            PurchaseItem(name="Milk", quantity=1, unit_price=0)

        with pytest.raises(ValidationError, match="unit_price must be > 0"):
            PurchaseItem(name="Milk", quantity=1, unit_price=-1.0)

    def test_item_string_representation(self):
        """Should have readable string format."""
        item = PurchaseItem(name="Milk", quantity=2, unit_price=1.50)

        from app.common.formatters import format_currency

        item_str = str(item)
        assert "Milk" in item_str
        assert "2" in item_str
        assert format_currency(item.unit_price) in item_str
        assert format_currency(item.total_price()) in item_str


class TestPurchaseAggregateRoot:
    """Test Purchase aggregate root and operations."""

    def test_create_new_purchase(self):
        """Should create new purchase with defaults."""
        purchase = Purchase()

        assert purchase.id is None
        assert purchase.items == []
        assert purchase.created_at is not None
        assert purchase.finished_at is None
        assert purchase.is_active() is True

    def test_create_purchase_with_id(self):
        """Should create purchase with existing ID."""
        purchase = Purchase(id=42)

        assert purchase.id == 42

    def test_create_purchase_with_timestamp(self):
        """Should preserve custom timestamps."""
        created = "2026-01-01T10:00:00"
        purchase = Purchase(created_at=created)

        assert purchase.created_at == created

    def test_add_item_to_purchase(self):
        """Should add item to purchase."""
        purchase = Purchase()

        purchase.add_item("Milk", 2, 1.50)

        assert len(purchase.items) == 1
        assert purchase.items[0].name == "Milk"

    def test_add_multiple_items(self):
        """Should add multiple items."""
        purchase = Purchase()

        purchase.add_item("Milk", 2, 1.50)
        purchase.add_item("Bread", 1, 2.00)
        purchase.add_item("Eggs", 12, 0.25)

        assert len(purchase.items) == 3
        assert purchase.item_count() == 15  # Sum of quantities: 2 + 1 + 12

    def test_add_item_validates_arguments(self):
        """Should validate item arguments when adding."""
        purchase = Purchase()

        with pytest.raises(ValidationError):
            purchase.add_item("Milk", -1, 1.50)  # negative quantity

        with pytest.raises(ValidationError):
            purchase.add_item("Milk", 1, 0)  # zero price

        with pytest.raises(ValidationError):
            purchase.add_item("", 1, 1.50)  # empty name

    def test_remove_item_by_index(self):
        """Should remove item by zero-based index."""
        purchase = Purchase()
        purchase.add_item("Milk", 1, 1.50)
        purchase.add_item("Bread", 1, 2.00)
        purchase.add_item("Eggs", 1, 0.25)

        purchase.remove_item(1)  # Remove Bread

        assert len(purchase.items) == 2
        assert purchase.items[0].name == "Milk"
        assert purchase.items[1].name == "Eggs"

    def test_remove_first_item(self):
        """Should remove first item."""
        purchase = Purchase()
        purchase.add_item("Milk", 1, 1.50)
        purchase.add_item("Bread", 1, 2.00)

        purchase.remove_item(0)

        assert len(purchase.items) == 1
        assert purchase.items[0].name == "Bread"

    def test_remove_last_item(self):
        """Should remove last item."""
        purchase = Purchase()
        purchase.add_item("Milk", 1, 1.50)
        purchase.add_item("Bread", 1, 2.00)

        purchase.remove_item(1)

        assert len(purchase.items) == 1
        assert purchase.items[0].name == "Milk"

    def test_remove_item_rejects_invalid_index(self):
        """Should reject invalid indices."""
        purchase = Purchase()
        purchase.add_item("Milk", 1, 1.50)

        with pytest.raises(NotFoundError, match="not found"):
            purchase.remove_item(1)  # Only index 0 exists

        with pytest.raises(NotFoundError, match="not found"):
            purchase.remove_item(-1)  # Negative index

    def test_remove_from_empty_purchase(self):
        """Should reject removal from empty purchase."""
        purchase = Purchase()

        with pytest.raises(NotFoundError, match="not found"):
            purchase.remove_item(0)

    def test_total_calculation(self):
        """Should calculate total cost correctly."""
        purchase = Purchase()
        purchase.add_item("Milk", 2, 1.50)  # 3.00
        purchase.add_item("Bread", 1, 2.00)  # 2.00
        purchase.add_item("Eggs", 12, 0.25)  # 3.00

        assert abs(purchase.total() - 8.0) < 0.01

    def test_total_of_empty_purchase(self):
        """Should return 0 for empty purchase."""
        purchase = Purchase()

        assert purchase.total() == 0

    def test_item_count(self):
        """Should count items correctly."""
        purchase = Purchase()

        assert purchase.item_count() == 0

        purchase.add_item("Milk", 1, 1.50)
        assert purchase.item_count() == 1

        purchase.add_item("Bread", 1, 2.00)
        assert purchase.item_count() == 2

    def test_finish_purchase(self):
        """Should mark purchase as finished."""
        purchase = Purchase()
        purchase.add_item("Milk", 1, 1.50)

        assert purchase.is_active() is True
        assert purchase.finished_at is None

        purchase.finish()

        assert purchase.is_active() is False
        assert purchase.finished_at is not None

    def test_is_active_status(self):
        """Should correctly report active status."""
        purchase = Purchase()
        assert purchase.is_active() is True

        purchase.finish()
        assert purchase.is_active() is False

    def test_string_representation_active(self):
        """Should have readable string for active purchase."""
        purchase = Purchase(id=1)
        purchase.add_item("Milk", 2, 1.50)

        from app.common.formatters import format_currency

        purchase_str = str(purchase)
        assert "Purchase #1" in purchase_str
        assert "ACTIVE" in purchase_str
        assert "Items: 2" in purchase_str  # qty=2 for Milk
        assert format_currency(purchase.total()) in purchase_str

    def test_string_representation_finished(self):
        """Should have readable string for finished purchase."""
        purchase = Purchase(id=2)
        purchase.add_item("Bread", 1, 2.00)
        purchase.finish()

        purchase_str = str(purchase)
        assert "Purchase #2" in purchase_str
        assert "FINISHED" in purchase_str


class TestExceptionHierarchy:
    """Test custom exception hierarchy."""

    def test_validation_error_is_domain_error(self):
        """ValidationError should be subclass of DomainError."""
        assert issubclass(ValidationError, DomainError)

    def test_not_found_error_is_domain_error(self):
        """NotFoundError should be subclass of DomainError."""
        assert issubclass(NotFoundError, DomainError)

    def test_catch_validation_error(self):
        """Should catch ValidationError with DomainError handler."""
        purchase = Purchase()

        try:
            purchase.add_item("Milk", -1, 1.0)
        except DomainError as e:
            assert isinstance(e, ValidationError)
        else:
            pytest.fail("Expected ValidationError")

    def test_catch_not_found_error(self):
        """Should catch NotFoundError with DomainError handler."""
        purchase = Purchase()

        try:
            purchase.remove_item(0)
        except DomainError as e:
            assert isinstance(e, NotFoundError)
        else:
            pytest.fail("Expected NotFoundError")


class TestPurchaseIntegration:
    """Integration tests for complete purchase workflows."""

    def test_complete_purchase_workflow(self):
        """Test complete workflow: create, add items, finish."""
        # Create
        purchase = Purchase()
        assert purchase.id is None
        assert purchase.is_active() is True

        # Add items
        purchase.add_item("Milk", 2, 1.50)
        purchase.add_item("Bread", 1, 2.00)
        assert purchase.item_count() == 3  # Sum of quantities: 2 + 1
        assert abs(purchase.total() - 5.0) < 0.01

        # Remove one item
        purchase.remove_item(0)
        assert purchase.item_count() == 1  # Remaining quantity: 1
        assert abs(purchase.total() - 2.0) < 0.01

        # Finish
        purchase.finish()
        assert purchase.is_active() is False

    def test_multiple_purchases_independent(self):
        """Multiple purchases should be independent."""
        p1 = Purchase(id=1)
        p2 = Purchase(id=2)

        p1.add_item("Milk", 1, 1.50)
        p2.add_item("Bread", 1, 2.00)

        assert p1.total() == 1.50
        assert p2.total() == 2.00
        assert p1.item_count() == 1
        assert p2.item_count() == 1

    def test_price_precision(self):
        """Should handle decimal prices accurately."""
        purchase = Purchase()
        purchase.add_item("Item1", 1, 1.99)
        purchase.add_item("Item2", 1, 2.49)
        purchase.add_item("Item3", 1, 1.52)

        # 1.99 + 2.49 + 1.52 = 6.00
        assert abs(purchase.total() - 6.0) < 0.01

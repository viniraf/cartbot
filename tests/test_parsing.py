"""Unit tests for input parsing utilities in app.common.validators (Phase 9.9).

Tests the new comma-based format for /add command.
"""

import pytest

from app.common.validators import parse_add_item_input


class TestCommaFormatTwoFieldPrice:
    """Test parsing: price,item (quantity defaults to 1)."""

    def test_price_item_basic(self):
        """Parse simple price,item format."""
        name, qty, price = parse_add_item_input("19.90,feijao")
        assert name == "feijao"
        assert qty == 1
        assert price == 19.90

    def test_price_item_multiword(self):
        """Parse price,item with spaces in name."""
        name, qty, price = parse_add_item_input("5.30,miojo com frango")
        assert name == "miojo com frango"
        assert qty == 1
        assert price == 5.30

    def test_price_item_whitespace(self):
        """Parse with extra whitespace."""
        name, qty, price = parse_add_item_input("  10.50  ,  coke zero  ")
        assert name == "coke zero"
        assert qty == 1
        assert price == 10.50


class TestCommaFormatThreeFieldPrice:
    """Test parsing: price,qty,item."""

    def test_price_qty_item_basic(self):
        """Parse simple price,qty,item format."""
        name, qty, price = parse_add_item_input("20.50,2,file de frango")
        assert name == "file de frango"
        assert qty == 2
        assert price == 20.50

    def test_price_qty_item_multiword(self):
        """Parse price,qty,item with spaces."""
        name, qty, price = parse_add_item_input("15.00,3,suco de laranja natural")
        assert name == "suco de laranja natural"
        assert qty == 3
        assert price == 15.00

    def test_price_qty_item_whitespace(self):
        """Parse with extra whitespace."""
        name, qty, price = parse_add_item_input("  25.99  ,  5  ,  chocolate ao leite  ")
        assert name == "chocolate ao leite"
        assert qty == 5
        assert price == 25.99


class TestCommaFormatErrors:
    """Test error cases for comma-based format."""

    def test_too_few_parts(self):
        """Reject single field."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("19.90")
        assert "Expected: price,item OR price,qty,item" in str(exc_info.value)

    def test_too_many_parts(self):
        """Reject 4+ fields."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("19.90,2,feijao,extra")
        assert "Expected: price,item OR price,qty,item" in str(exc_info.value)

    def test_empty_name(self):
        """Reject empty item name."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("19.90,")
        assert "Item name must not be empty" in str(exc_info.value)

    def test_empty_name_with_qty(self):
        """Reject empty item name with quantity."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("19.90,2,")
        assert "Item name must not be empty" in str(exc_info.value)

    def test_invalid_price(self):
        """Reject non-numeric price."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("abc,feijao")
        assert "Price must be a number" in str(exc_info.value)

    def test_invalid_qty(self):
        """Reject non-numeric quantity."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("19.90,abc,feijao")
        assert "Quantity must be an integer" in str(exc_info.value)

    def test_zero_price(self):
        """Reject zero price."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("0,feijao")
        assert "Price must be greater than zero" in str(exc_info.value)

    def test_negative_price(self):
        """Reject negative price."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("-5.00,feijao")
        assert "Price must be greater than zero" in str(exc_info.value)

    def test_zero_qty(self):
        """Reject zero quantity."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("19.90,0,feijao")
        assert "Quantity must be greater than zero" in str(exc_info.value)

    def test_negative_qty(self):
        """Reject negative quantity."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_item_input("19.90,-2,feijao")
        assert "Quantity must be greater than zero" in str(exc_info.value)

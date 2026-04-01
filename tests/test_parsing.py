"""Unit tests for input parsing utilities in app.common.validators (Phase 9.9-9.10).

Tests the new comma-based format for /add command and batch parsing.
"""

import pytest

from app.common.validators import parse_add_item_input, parse_add_input


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


class TestBatchParserInline:
    """Test batch parser with inline format (Phase 9.10)."""

    def test_inline_single_item(self):
        """Parse inline: /add price,item."""
        parsed = parse_add_input("/add 19.90,feijao")
        assert len(parsed) == 1
        assert parsed[0]["name"] == "feijao"
        assert parsed[0]["quantity"] == 1
        assert parsed[0]["price"] == 19.90

    def test_inline_with_quantity(self):
        """Parse inline: /add price,qty,item."""
        parsed = parse_add_input("/add 20.50,2,file de frango")
        assert len(parsed) == 1
        assert parsed[0]["name"] == "file de frango"
        assert parsed[0]["quantity"] == 2
        assert parsed[0]["price"] == 20.50

    def test_inline_with_spaces(self):
        """Parse inline with extra spaces."""
        parsed = parse_add_input("/add   15.99  ,  3  ,  suco de laranja  ")
        assert len(parsed) == 1
        assert parsed[0]["name"] == "suco de laranja"
        assert parsed[0]["quantity"] == 3
        assert parsed[0]["price"] == 15.99


class TestBatchParserBatch:
    """Test batch parser with multiline format (Phase 9.10)."""

    def test_batch_multiple_items(self):
        """Parse batch: /add followed by items on lines."""
        input_text = """/add
19.90,feijao
20.50,2,file de frango
5.30,miojo"""
        parsed = parse_add_input(input_text)
        assert len(parsed) == 3
        
        assert parsed[0]["name"] == "feijao"
        assert parsed[0]["quantity"] == 1
        assert parsed[0]["price"] == 19.90
        
        assert parsed[1]["name"] == "file de frango"
        assert parsed[1]["quantity"] == 2
        assert parsed[1]["price"] == 20.50
        
        assert parsed[2]["name"] == "miojo"
        assert parsed[2]["quantity"] == 1
        assert parsed[2]["price"] == 5.30

    def test_batch_single_item(self):
        """Parse batch with one item on second line."""
        input_text = """/add
19.90,feijao"""
        parsed = parse_add_input(input_text)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "feijao"
        assert parsed[0]["price"] == 19.90

    def test_batch_with_empty_lines(self):
        """Parse batch, skipping empty lines."""
        input_text = """/add
19.90,feijao

20.50,2,file"""
        parsed = parse_add_input(input_text)
        assert len(parsed) == 2


class TestBatchParserErrors:
    """Test error handling in batch parser (Phase 9.10)."""

    def test_no_input(self):
        """Reject when no items provided."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_input("/add")
        assert "No items provided" in str(exc_info.value)

    def test_invalid_command(self):
        """Reject invalid command."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_input("/list")
        assert "Invalid command" in str(exc_info.value)

    def test_batch_invalid_item_format(self):
        """Fail entirely if batch has invalid item."""
        input_text = """/add
19.90,feijao
invalid_line
20.50,2,file"""
        with pytest.raises(ValueError) as exc_info:
            parse_add_input(input_text)
        assert "Invalid item format" in str(exc_info.value)

    def test_batch_invalid_price(self):
        """Fail entirely if any price is invalid."""
        input_text = """/add
19.90,feijao
abc,miojo"""
        with pytest.raises(ValueError) as exc_info:
            parse_add_input(input_text)
        assert "Invalid item format" in str(exc_info.value)

    def test_batch_invalid_quantity(self):
        """Fail entirely if any quantity is invalid."""
        input_text = """/add
19.90,feijao
5.30,abc,miojo"""
        with pytest.raises(ValueError) as exc_info:
            parse_add_input(input_text)
        assert "Invalid item format" in str(exc_info.value)

    def test_inline_invalid_format(self):
        """Fail if inline has invalid format."""
        with pytest.raises(ValueError) as exc_info:
            parse_add_input("/add invalid_no_comma")
        assert "Invalid item format" in str(exc_info.value)

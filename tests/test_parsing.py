"""Unit tests for input parsing utilities in app.common.validators."""

import pytest

from app.common.validators import parse_add_item_input


def test_parse_pipe_valid():
    name, qty, price = parse_add_item_input("Milk | 2 | 1.50")
    assert name == "Milk"
    assert qty == 2
    assert price == 1.50

    name, qty, price = parse_add_item_input("Mortadela 200g | 1 | 11.50")
    assert name == "Mortadela 200g"
    assert qty == 1
    assert price == 11.50


def test_parse_pipe_whitespace():
    name, qty, price = parse_add_item_input("  Coke 2L  | 3  |  9  ")
    assert name == "Coke 2L"
    assert qty == 3
    assert price == 9.0


def test_parse_pipe_errors():
    with pytest.raises(ValueError):
        parse_add_item_input("just one segment")
    with pytest.raises(ValueError):
        parse_add_item_input("a | b | c | d")
    with pytest.raises(ValueError):
        parse_add_item_input(" | 1 | 1")
    with pytest.raises(ValueError):
        parse_add_item_input("Name | 0 | 1")
    with pytest.raises(ValueError):
        parse_add_item_input("Name | -1 | 1")
    with pytest.raises(ValueError):
        parse_add_item_input("Name | 1 | 0")
    with pytest.raises(ValueError):
        parse_add_item_input("Name | 2 | price")
    with pytest.raises(ValueError):
        parse_add_item_input("Name | qty | 5")

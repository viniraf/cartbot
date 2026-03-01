"""Unit tests for formatting helpers defined in app.common.formatters."""

import pytest

from app.common.formatters import format_currency, format_command_block, append_help_hint


def test_format_currency_basic():
    assert format_currency(5) == "R$ 5.00"
    assert format_currency(5.5) == "R$ 5.50"
    assert format_currency(11.567) == "R$ 11.57"  # rounded


def test_format_currency_bad_input():
    # non-numeric should gracefully become 0.00
    assert format_currency(None) == "R$ 0.00"
    assert format_currency("abc") == "R$ 0.00"


def test_format_command_block():
    lines = ["/start - begin", "/finish - end"]
    result = format_command_block(lines)
    assert "/start" in result
    assert "/finish" in result
    assert "\n" in result


def test_append_help_hint_adds_footer():
    original = "Hello world"
    got = append_help_hint(original)
    assert "Need help? Use /help" in got
    # footer should be separated by blank line
    assert original in got
    assert got.endswith("/help")


def test_append_help_hint_preserves_newline():
    original = "Line\n"
    got = append_help_hint(original)
    assert got.count("\n") >= original.count("\n") + 2

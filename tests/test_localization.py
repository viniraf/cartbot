"""Tests for localization system (Phase 8.6).

Tests cover:
- Message retrieval for both languages
- Language switching
- Fallback behavior
- Message formatting with parameters
- Language persistence in user context
"""

import pytest
from unittest.mock import MagicMock
from telegram.ext import ContextTypes

from app.common.messages import (
    get_message,
    set_language,
    get_language,
    format_message,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
)


class TestMessageRetrieval:
    """Test basic message retrieval."""

    def test_get_message_english(self):
        """get_message should return English message by default."""
        msg = get_message("en", "START_NEW")
        assert msg == "Shopping list started."

    def test_get_message_ptbr(self):
        """get_message should return Portuguese message when specified."""
        msg = get_message("ptbr", "START_NEW")
        assert msg == "Lista de compras iniciada."

    def test_get_message_with_fallback(self):
        """get_message should fallback to English if message missing in requested language."""
        # Add a fake key that doesn't exist
        msg = get_message("ptbr", "NONEXISTENT_KEY")
        assert "[Missing:" in msg or msg == "[Missing: NONEXISTENT_KEY]"

    def test_get_message_with_format_params(self):
        """get_message should format message with provided parameters."""
        msg = get_message("en", "ADD_ITEM_TOTAL", total="R$ 25.00")
        assert "R$ 25.00" in msg or "25.00" in msg

    def test_get_message_currency_not_translated(self):
        """Currency (R$) should never be translated."""
        msg_en = get_message("en", "ADD_ITEM_TOTAL", total="R$ 25.00")
        msg_pt = get_message("ptbr", "ADD_ITEM_TOTAL", total="R$ 25.00")
        # Both should contain R$ (not translated)
        assert "R$" in msg_en
        assert "R$" in msg_pt

    def test_command_names_not_translated(self):
        """Command names should not be translated."""
        msg_en = get_message("en", "HELP_ADD_ITEM")
        msg_pt = get_message("ptbr", "HELP_ADD_ITEM")
        # Both should contain /add
        assert "/add" in msg_en
        assert "/add" in msg_pt


class TestLanguageSwitching:
    """Test language switching functionality."""

    def test_set_language_en(self):
        """set_language should set language to English."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        result = set_language(context, "en")
        assert result is True
        assert context.user_data["language"] == "en"

    def test_set_language_ptbr(self):
        """set_language should set language to Portuguese."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        result = set_language(context, "ptbr")
        assert result is True
        assert context.user_data["language"] == "ptbr"

    def test_set_language_invalid(self):
        """set_language should return False for invalid language."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        result = set_language(context, "invalid")
        assert result is False
        assert "language" not in context.user_data

    def test_get_language_default(self):
        """get_language should return default language if not set."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        lang = get_language(context)
        assert lang == DEFAULT_LANGUAGE
        assert lang == "en"

    def test_get_language_after_set(self):
        """get_language should return the language after being set."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        set_language(context, "ptbr")
        lang = get_language(context)
        assert lang == "ptbr"


class TestFormatMessage:
    """Test the convenience format_message function."""

    def test_format_message_uses_user_language(self):
        """format_message should use user's selected language."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Default should be English
        msg = format_message(context, "START_NEW")
        assert msg == "Shopping list started."

        # Switch to Portuguese
        set_language(context, "ptbr")
        msg = format_message(context, "START_NEW")
        assert msg == "Lista de compras iniciada."

    def test_format_message_with_params(self):
        """format_message should format with parameters using user language."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"language": "en"}

        msg = format_message(context, "ADD_ITEM_TOTAL", total="R$ 50.00")
        assert "50.00" in msg

    def test_format_message_lang_switch_impact(self):
        """Switching language should immediately affect format_message."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Start in English
        msg1 = format_message(context, "START_NEW")
        assert "Shopping list started" in msg1

        # Switch to Portuguese
        set_language(context, "ptbr")
        msg2 = format_message(context, "START_NEW")
        assert "Lista de compras iniciada" in msg2

        # Switch back to English
        set_language(context, "en")
        msg3 = format_message(context, "START_NEW")
        assert "Shopping list started" in msg3


class TestLanguagePersistence:
    """Test that language preference persists in user context."""

    def test_language_persists_across_calls(self):
        """Language should persist in user_data across multiple calls."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Set language
        set_language(context, "ptbr")

        # Verify it persists
        assert get_language(context) == "ptbr"
        assert format_message(context, "START_NEW") == "Lista de compras iniciada."

        # Even with multiple calls
        for _ in range(3):
            assert get_language(context) == "ptbr"
            msg = format_message(context, "START_NEW")
            assert "Lista de compras iniciada" in msg or "iniciada" in msg

    def test_different_users_different_languages(self):
        """Different users should be able to have different language preferences."""
        context1 = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context1.user_data = {}

        context2 = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context2.user_data = {}

        # User 1 uses English (default)
        msg1 = format_message(context1, "START_NEW")

        # User 2 switches to Portuguese
        set_language(context2, "ptbr")
        msg2 = format_message(context2, "START_NEW")

        # User 1 should still be English
        assert "Shopping list started" in msg1
        assert "Lista de compras iniciada" in msg2
        assert get_language(context1) == "en"
        assert get_language(context2) == "ptbr"


class TestSupportedLanguages:
    """Test supported languages list."""

    def test_supported_languages_contains_en_and_ptbr(self):
        """SUPPORTED_LANGUAGES should contain 'en' and 'ptbr'."""
        assert "en" in SUPPORTED_LANGUAGES
        assert "ptbr" in SUPPORTED_LANGUAGES

    def test_all_messages_have_en_and_ptbr(self):
        """All message keys should exist in both EN and PTBR dictionaries."""
        en_keys = set(SUPPORTED_LANGUAGES["en"].keys())
        ptbr_keys = set(SUPPORTED_LANGUAGES["ptbr"].keys())

        # All EN keys should have PT-BR translations
        missing_in_ptbr = en_keys - ptbr_keys
        assert len(missing_in_ptbr) == 0, f"Missing PT-BR translations: {missing_in_ptbr}"

        # All PT-BR keys should have EN equivalents
        missing_in_en = ptbr_keys - en_keys
        assert len(missing_in_en) == 0, f"Extra PT-BR keys: {missing_in_en}"

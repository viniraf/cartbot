"""Tests for /lang command handler.

Tests cover:
- Language switching via /lang command
- Error handling for invalid languages
- Message localization based on selected language
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import lang_handler
from app.services import PurchaseService
from app.infra.repositories import SQLitePurchaseRepository
from app.infra import init_db


# Fixtures

@pytest.fixture
def test_db():
    """Fixture providing a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        init_db(db_path)
        yield db_path


@pytest.fixture
def mock_user():
    """Fixture providing a mock Telegram user."""
    user = MagicMock(spec=User)
    user.id = 12345
    user.username = "testuser"
    return user


@pytest.fixture
def mock_message(text="/lang ptbr"):
    """Fixture providing a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = text
    message.reply_text = AsyncMock()
    return message


@pytest.fixture
def mock_update(mock_user, mock_message):
    """Fixture providing a mock Telegram update."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_user
    update.message = mock_message
    return update


@pytest.fixture
def mock_context(test_db):
    """Fixture providing a mock handler context with service."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}
    context.user_data = {}

    # Inject real service with test database
    repo = SQLitePurchaseRepository(test_db)
    service = PurchaseService(repo)
    context.bot_data["service"] = service

    return context


# Tests

class TestLangHandlerSuccess:
    """Test successful /lang command handling."""

    @pytest.mark.asyncio
    async def test_lang_ptbr(self, mock_update, mock_context):
        """lang_handler should set language to Portuguese."""
        mock_update.message.text = "/lang ptbr"

        await lang_handler(mock_update, mock_context)

        # Verify language was set
        assert mock_context.user_data.get("language") == "ptbr"
        
        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_lang_en(self, mock_update, mock_context):
        """lang_handler should set language to English."""
        mock_update.message.text = "/lang en"

        await lang_handler(mock_update, mock_context)

        # Verify language was set
        assert mock_context.user_data.get("language") == "en"

        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_lang_switch_changes_language(self, mock_update, mock_context):
        """Multiple /lang commands should switch language."""
        # Start in English (default)
        assert mock_context.user_data.get("language", "en") == "en"

        # Switch to Portuguese
        mock_update.message.text = "/lang ptbr"
        await lang_handler(mock_update, mock_context)
        assert mock_context.user_data.get("language") == "ptbr"

        # Switch back to English
        mock_update.message.text = "/lang en"
        await lang_handler(mock_update, mock_context)
        assert mock_context.user_data.get("language") == "en"


class TestLangHandlerErrors:
    """Test error cases for /lang command."""

    @pytest.mark.asyncio
    async def test_lang_no_args(self, mock_update, mock_context):
        """lang_handler should show usage if no language specified."""
        mock_update.message.text = "/lang"

        await lang_handler(mock_update, mock_context)

        # Verify standardized error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "❌" in call_args

    @pytest.mark.asyncio
    async def test_lang_invalid_language(self, mock_update, mock_context):
        """lang_handler should error on invalid language."""
        mock_update.message.text = "/lang invalid"

        await lang_handler(mock_update, mock_context)

        # Verify standardized error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "❌" in call_args

        # Language should not be changed
        assert mock_context.user_data.get("language") is None


class TestLangHandlerIntegration:
    """Integration tests for /lang command."""

    @pytest.mark.asyncio
    async def test_lang_persists_across_commands(self, mock_update, mock_context):
        """Language preference should persist across multiple handler calls."""
        from app.common.messages import format_message

        # Switch language to Portuguese
        mock_update.message.text = "/lang ptbr"
        await lang_handler(mock_update, mock_context)

        # Verify language persists
        assert mock_context.user_data.get("language") == "ptbr"

        # Verify format_message uses the language
        msg_start = format_message(mock_context, "START_NEW")
        assert "iniciada" in msg_start.lower()  # Portuguese word

        # Switch to English
        mock_update.message.text = "/lang en"
        await lang_handler(mock_update, mock_context)

        # Verify language changed
        assert mock_context.user_data.get("language") == "en"

        # Verify format_message uses the new language
        msg_start = format_message(mock_context, "START_NEW")
        assert "started" in msg_start.lower()  # English word

    @pytest.mark.asyncio
    async def test_lang_case_insensitive(self, mock_update, mock_context):
        """lang_handler should accept any case."""
        # Test uppercase
        mock_update.message.text = "/lang PTBR"
        await lang_handler(mock_update, mock_context)
        assert mock_context.user_data.get("language") == "ptbr"

        # Test mixed case
        mock_update.message.text = "/lang En"
        await lang_handler(mock_update, mock_context)
        assert mock_context.user_data.get("language") == "en"

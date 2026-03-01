"""Tests for /help command handler and formatting.

Ensures command list groups appear and formatting helpers are used.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import help_handler


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}
    context.user_data = {}
    return context


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


class TestHelpHandler:
    @pytest.mark.asyncio
    async def test_help_returns_commands(self, mock_update, mock_context):
        await help_handler(mock_update, mock_context)
        assert mock_update.message.reply_text.called
        text = mock_update.message.reply_text.call_args[0][0]
        # Check for section headers
        assert "Available Commands" in text
        assert "Session" in text
        assert "Items" in text
        assert "Overview" in text
        # Check for some specific commands
        assert "/start" in text
        assert "/add_item" in text
        assert "/view_total" in text
        # Help hint appended
        assert "Need help? Use /help" in text

    @pytest.mark.asyncio
    async def test_help_formatting_consistent(self, mock_update, mock_context):
        # The text should have blank lines separating groups
        await help_handler(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        # there should be at least two consecutive newlines somewhere
        assert "\n\n" in text

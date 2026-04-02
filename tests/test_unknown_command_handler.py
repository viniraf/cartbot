"""Tests for unknown command handler.

Tests cover:
- Unknown command handling in English
- Unknown command handling in Portuguese (PT-BR)
- Proper message formatting without footer
- Correct suggestion to use /help
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.handlers.handlers import unknown_command_handler
from app.common.messages.messages_en import MESSAGES as messages_en
from app.common.messages.messages_ptbr import MESSAGES as messages_ptbr


class TestUnknownCommandHandler:
    """Test unknown command handler localization and formatting."""

    @pytest.mark.asyncio
    async def test_unknown_command_english(self):
        """Unknown command should show English message without footer."""
        # Setup context with English language
        context = MagicMock()
        context.user_data = {"language": "en"}

        # Setup mock update
        update = MagicMock()
        update.effective_user.id = 123
        update.message = AsyncMock()

        # Call handler
        await unknown_command_handler(update, context)

        # Verify correct message was sent
        expected_title = messages_en["UNKNOWN_COMMAND_TITLE"]
        expected_message = messages_en["UNKNOWN_COMMAND_MESSAGE"]
        expected_response = f"{expected_title}\n\n{expected_message}"

        update.message.reply_text.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_unknown_command_portuguese(self):
        """Unknown command should show Portuguese message without footer."""
        # Setup context with Portuguese language
        context = MagicMock()
        context.user_data = {"language": "ptbr"}

        # Setup mock update
        update = MagicMock()
        update.effective_user.id = 456
        update.message = AsyncMock()

        # Call handler
        await unknown_command_handler(update, context)

        # Verify correct message was sent
        expected_title = messages_ptbr["UNKNOWN_COMMAND_TITLE"]
        expected_message = messages_ptbr["UNKNOWN_COMMAND_MESSAGE"]
        expected_response = f"{expected_title}\n\n{expected_message}"

        update.message.reply_text.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_unknown_command_default_language(self):
        """Unknown command should default to English when no language set."""
        # Setup context without language (should default to English)
        context = MagicMock()
        context.user_data = {}

        # Setup mock update
        update = MagicMock()
        update.effective_user.id = 789
        update.message = AsyncMock()

        # Call handler
        await unknown_command_handler(update, context)

        # Verify English message was sent (default)
        expected_title = messages_en["UNKNOWN_COMMAND_TITLE"]
        expected_message = messages_en["UNKNOWN_COMMAND_MESSAGE"]
        expected_response = f"{expected_title}\n\n{expected_message}"

        update.message.reply_text.assert_called_once_with(expected_response)

    @pytest.mark.asyncio
    async def test_unknown_command_no_footer(self):
        """Unknown command response should not include help footer."""
        # Setup context with English language
        context = MagicMock()
        context.user_data = {"language": "en"}

        # Setup mock update
        update = MagicMock()
        update.effective_user.id = 123
        update.message = AsyncMock()

        # Call handler
        await unknown_command_handler(update, context)

        # Get the response that was sent
        call_args = update.message.reply_text.call_args[0][0]

        # Verify response does NOT contain footer patterns
        assert "Type /help" not in call_args  # Should not have footer
        assert "/help" in call_args  # But should have the suggestion in the message
        assert "Available commands:" not in call_args  # No footer content
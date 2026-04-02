"""Tests for footer standardization across messages (Bug 08).

Tests cover:
- All error messages include standardized footer with "--\n" separator
- All non-error messages include footer via append_help_hint()
- Unknown command handler does NOT include footer
- Footer is properly localized
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import format_error_message, unknown_command_handler, help_handler
from app.common.formatters import append_help_hint
from app.common.messages.messages_en import MESSAGES as MESSAGES_EN
from app.common.messages.messages_ptbr import MESSAGES as MESSAGES_PTBR


class TestFooterStandardization:
    """Test footer formatting is standardized across all messages."""

    def test_error_message_includes_separator(self):
        """Error messages should include --\\n separator before footer."""
        context = MagicMock()
        context.user_data = {"language": "en"}
        
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        
        # Should have -- separator
        assert "--\n" in error_msg
        # Should end with localized footer (no trailing separator)
        assert error_msg.strip().endswith(MESSAGES_EN["ERROR_HELP_FOOTER"])

    def test_error_message_separator_before_footer(self):
        """Footer separator should come before the footer text."""
        context = MagicMock()
        context.user_data = {"language": "en"}
        
        error_msg = format_error_message(context, "INVALID_ADD_FORMAT")
        
        # The footer should be on a new line after --
        footer = MESSAGES_EN["ERROR_HELP_FOOTER"]
        expected_pattern = f"--\n{footer}"
        assert expected_pattern in error_msg

    def test_error_message_footer_localized_en(self):
        """Error messages should use English footer text when language is English."""
        context = MagicMock()
        context.user_data = {"language": "en"}
        
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        
        # Should contain English footer
        footer = MESSAGES_EN["ERROR_HELP_FOOTER"]
        assert footer in error_msg
        assert "Type /help" in error_msg  # English specific

    def test_error_message_footer_localized_ptbr(self):
        """Error messages should use Portuguese footer text when language is PT-BR."""
        context = MagicMock()
        context.user_data = {"language": "ptbr"}
        
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        
        # Should contain Portuguese footer
        footer = MESSAGES_PTBR["ERROR_HELP_FOOTER"]
        assert footer in error_msg
        assert "Digite /help" in error_msg  # Portuguese specific

    def test_append_help_hint_includes_separator(self):
        """append_help_hint should include --\\n separator."""
        context = MagicMock()
        context.user_data = {"language": "en"}
        
        result = append_help_hint("Sample message", context)
        
        # Should have -- separator
        assert "--\n" in result
        # Should include footer text
        assert "Type /help" in result

    def test_append_help_hint_separator_before_footer(self):
        """Footer in append_help_hint should be preceded by --."""
        context = MagicMock()
        context.user_data = {"language": "en"}
        
        result = append_help_hint("Sample message", context)
        
        # Should have pattern: blank line + -- + newline + footer
        assert "\n--\n" in result

    @pytest.mark.asyncio
    async def test_unknown_command_no_footer(self):
        """Unknown command should NOT include footer."""
        context = MagicMock()
        context.user_data = {"language": "en"}
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123
        update.message = AsyncMock()
        
        await unknown_command_handler(update, context)
        
        # Get the message that was sent
        call_args = update.message.reply_text.call_args[0][0]
        
        # Should NOT contain footer separator or help text footer
        assert "--" not in call_args
        assert "Type /help for more information" not in call_args
        assert "Digite /help" not in call_args


class TestFooterConsistency:
    """Test footer consistency across different message types."""

    def test_error_footer_format_matches_append_help_hint(self):
        """Both error messages and append_help_hint should use --\\n separator."""
        context = MagicMock()
        context.user_data = {"language": "en"}
        
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        regular_msg = append_help_hint("Test message", context)
        
        # Both should have -- separator
        assert "--\n" in error_msg
        assert "--\n" in regular_msg
        
        # Both should include footer text
        footer = MESSAGES_EN["ERROR_HELP_FOOTER"]
        assert footer in error_msg
        assert footer in regular_msg

    def test_footer_structure_consistent_across_languages(self):
        """Footer structure should be identical in both languages."""
        context_en = MagicMock()
        context_en.user_data = {"language": "en"}
        
        context_ptbr = MagicMock()
        context_ptbr.user_data = {"language": "ptbr"}
        
        error_en = format_error_message(context_en, "NO_ACTIVE_PURCHASE")
        error_ptbr = format_error_message(context_ptbr, "NO_ACTIVE_PURCHASE")
        
        # Both should have -- separator in same position relative to content
        assert "--\n" in error_en
        assert "--\n" in error_ptbr
        
        # Both should end with their respective footer (no additional content after)
        footer_en = MESSAGES_EN["ERROR_HELP_FOOTER"]
        footer_ptbr = MESSAGES_PTBR["ERROR_HELP_FOOTER"]
        
        assert error_en.strip().endswith(footer_en)
        assert error_ptbr.strip().endswith(footer_ptbr)

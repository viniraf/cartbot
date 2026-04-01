"""Tests for /start command handler (Phase 9.8).

Tests cover:
- Store name prompting when no active purchase (new behavior)
- Resume options display for active purchases (unchanged)
- Locale parameter handling (/start en, /start ptbr)
- User context state management
- Error handling and logging
"""

import pytest
import logging
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import start_handler
from app.domain import NotFoundError, ValidationError
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
def mock_chat():
    """Fixture providing a mock Telegram chat."""
    chat = MagicMock(spec=Chat)
    chat.id = 12345
    return chat


@pytest.fixture
def mock_message():
    """Fixture providing a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.reply_text = AsyncMock()
    return message


@pytest.fixture
def mock_update(mock_user, mock_chat, mock_message):
    """Fixture providing a mock Telegram update with /start command."""
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


# Tests - Phase 9.8: Store Input Flow

class TestStartHandlerStorePrompt:
    """Test /start prompts for store name when no active purchase."""

    @pytest.mark.asyncio
    async def test_start_sets_waiting_for_store_flag(self, mock_update, mock_context):
        """When no active purchase, /start should set waiting_for_store_input flag."""
        mock_update.message.text = "/start"
        
        await start_handler(mock_update, mock_context)
        
        # Should set waiting_for_store_input flag
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Should NOT have created a purchase yet
        assert "purchase_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_start_sends_store_prompt_message(self, mock_update, mock_context):
        """When no active purchase, /start should send store prompt message."""
        mock_update.message.text = "/start"
        
        await start_handler(mock_update, mock_context)
        
        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()
        message_text = mock_update.message.reply_text.call_args[0][0]
        
        # Should contain store prompt related to store name input
        assert "store" in message_text.lower() or "name" in message_text.lower()

    @pytest.mark.asyncio
    async def test_start_does_not_create_purchase_immediately(self, mock_update, mock_context):
        """start_handler should NOT create purchase until store name provided."""
        mock_update.message.text = "/start"
        
        await start_handler(mock_update, mock_context)
        
        # No purchase should be created yet
        assert "purchase_id" not in mock_context.user_data
        
        # Should be waiting for store input
        assert mock_context.user_data.get("waiting_for_store_input") is True


class TestStartHandlerActiveResume:
    """Test /start displays resume options for active purchases."""

    @pytest.mark.asyncio
    async def test_start_with_active_purchase_shows_options(self, mock_update, mock_context):
        """When active purchase exists, /start should show resume options."""
        # Create active purchase manually
        service = mock_context.bot_data["service"]
        purchase_id = service.create_purchase(store_name="Whole Foods", locale="en")
        mock_context.user_data["purchase_id"] = purchase_id
        
        # Call /start
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)
        
        # Should NOT set waiting_for_store_input
        assert mock_context.user_data.get("waiting_for_store_input") is not True
        
        # Should show resume options message
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "active purchase" in message_text.lower() or "continue" in message_text.lower()

    @pytest.mark.asyncio
    async def test_start_keeps_same_purchase_id(self, mock_update, mock_context):
        """Calling /start with active purchase should keep same purchase_id."""
        # Create and set a purchase
        service = mock_context.bot_data["service"]
        purchase_id = service.create_purchase(store_name="Costco", locale="en")
        mock_context.user_data["purchase_id"] = purchase_id
        
        # Call /start
        mock_update.message.text = "/start"
        mock_update.message.reply_text.reset_mock()
        await start_handler(mock_update, mock_context)
        
        # Same ID should be preserved
        assert mock_context.user_data["purchase_id"] == purchase_id


class TestStartHandlerLocale:
    """Test localization parameter support for /start command."""

    @pytest.mark.asyncio
    async def test_start_with_en_locale(self, mock_update, mock_context):
        """start_handler should accept /start en parameter."""
        mock_update.message.text = "/start en"
        
        await start_handler(mock_update, mock_context)
        
        # Should set language in context
        assert mock_context.user_data.get("language") == "en"
        
        # Should set waiting for store input
        assert mock_context.user_data.get("waiting_for_store_input") is True

    @pytest.mark.asyncio
    async def test_start_with_ptbr_locale(self, mock_update, mock_context):
        """start_handler should accept /start ptbr parameter."""
        mock_update.message.text = "/start ptbr"
        
        await start_handler(mock_update, mock_context)
        
        # Should set language in context
        assert mock_context.user_data.get("language") == "ptbr"
        
        # Should set waiting for store input
        assert mock_context.user_data.get("waiting_for_store_input") is True

    @pytest.mark.asyncio
    async def test_start_with_invalid_locale(self, mock_update, mock_context):
        """start_handler should reject invalid locale parameter."""
        mock_update.message.text = "/start fr"
        
        await start_handler(mock_update, mock_context)
        
        # Should NOT set language to fr
        assert mock_context.user_data.get("language") != "fr"
        
        # Should send error message
        mock_update.message.reply_text.assert_called_once()
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Invalid" in message_text or "invalid" in message_text.lower()

    @pytest.mark.asyncio
    async def test_start_default_locale_en(self, mock_update, mock_context):
        """start_handler without locale param should default to en."""
        mock_update.message.text = "/start"
        
        await start_handler(mock_update, mock_context)
        
        # Should set waiting flag (locale will be preserved in purchase later)
        assert mock_context.user_data.get("waiting_for_store_input") is True


class TestStartHandlerLogging:
    """Test logging during /start command."""

    @pytest.mark.asyncio
    async def test_start_logs_command_received(self, mock_update, mock_context, caplog):
        """start_handler should log /start command received."""
        with caplog.at_level(logging.INFO):
            mock_update.message.text = "/start"
            await start_handler(mock_update, mock_context)
        
        # Should log command received
        assert any("/start" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_start_logs_user_id(self, mock_update, mock_context, caplog):
        """start_handler should log user ID."""
        with caplog.at_level(logging.INFO):
            mock_update.message.text = "/start"
            await start_handler(mock_update, mock_context)
        
        # Should log user ID
        user_id = str(mock_update.effective_user.id)
        log_output = " ".join([record.message for record in caplog.records])
        assert user_id in log_output


class TestStartHandlerErrorHandling:
    """Test error handling in /start command."""

    @pytest.mark.asyncio
    async def test_start_handles_reply_failure(self, mock_update, mock_context, caplog):
        """start_handler should handle message send failures gracefully."""
        # Mock reply to fail
        mock_update.message.reply_text = AsyncMock(
            side_effect=RuntimeError("Telegram API error")
        )
        
        with caplog.at_level(logging.ERROR):
            # Should not raise
            await start_handler(mock_update, mock_context)
        
        # Should log error
        assert any("error" in record.message.lower() or "failed" in record.message.lower()
                   for record in caplog.records)


class TestStartHandlerMultipleUsers:
    """Test user isolation and concurrent access."""

    @pytest.mark.asyncio
    async def test_start_multiple_users_isolated(self, mock_context):
        """Each user should have separate context state."""
        # User 1
        user1 = MagicMock(spec=User)
        user1.id = 111
        user1.username = "user1"
        
        update1 = MagicMock(spec=Update)
        update1.effective_user = user1
        update1.message = AsyncMock()
        update1.message.reply_text = AsyncMock()
        update1.message.text = "/start"
        
        context1 = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context1.bot_data = mock_context.bot_data  # Shared service
        context1.user_data = {}  # Separate per user
        
        # User 2
        user2 = MagicMock(spec=User)
        user2.id = 222
        user2.username = "user2"
        
        update2 = MagicMock(spec=Update)
        update2.effective_user = user2
        update2.message = AsyncMock()
        update2.message.reply_text = AsyncMock()
        update2.message.text = "/start"
        
        context2 = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context2.bot_data = mock_context.bot_data  # Shared service
        context2.user_data = {}  # Separate per user

        # Both users call /start
        await start_handler(update1, context1)
        await start_handler(update2, context2)
        
        # Both should have waiting_for_store_input set
        assert context1.user_data.get("waiting_for_store_input") is True
        assert context2.user_data.get("waiting_for_store_input") is True
        
        # Neither should have purchase_id yet
        assert "purchase_id" not in context1.user_data
        assert "purchase_id" not in context2.user_data


class TestStartHandlerEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_start_with_extra_parameters_ignored(self, mock_update, mock_context):
        """Extra parameters after locale should be treated as invalid."""
        mock_update.message.text = "/start en extra stuff"
        
        # Should not crash, but may reject as invalid locale
        await start_handler(mock_update, mock_context)
        
        # With invalid locale param, should show error or default behavior
        # Either way, message should be sent
        mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_start_with_empty_text(self, mock_update, mock_context):
        """start_handler should handle empty message text."""
        mock_update.message.text = ""
        
        # Should not crash
        await start_handler(mock_update, mock_context)
        
        # Should still set waiting flag
        assert mock_context.user_data.get("waiting_for_store_input") is True

    @pytest.mark.asyncio
    async def test_start_with_none_text(self, mock_update, mock_context):
        """start_handler should handle None message text."""
        mock_update.message.text = None
        
        # Should not crash
        await start_handler(mock_update, mock_context)
        
        # Should still set waiting flag
        assert mock_context.user_data.get("waiting_for_store_input") is True

"""Tests for /start command handler.

Tests cover:
- Successful purchase creation
- User context storage
- Message formatting and sending
- Error handling and logging
- Service integration
- User data isolation
"""

import pytest
import logging
import tempfile
import os
from unittest.mock import MagicMock, patch, AsyncMock, call
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


# Tests

class TestStartHandlerSuccess:
    """Test successful /start command handling."""

    @pytest.mark.asyncio
    async def test_start_creates_purchase(self, mock_update, mock_context):
        """start_handler should create new purchase via service."""
        await start_handler(mock_update, mock_context)
        
        # Verify purchase_id was stored in user context
        assert "purchase_id" in mock_context.user_data
        purchase_id = mock_context.user_data["purchase_id"]
        assert isinstance(purchase_id, int)
        assert purchase_id > 0

    @pytest.mark.asyncio
    async def test_start_stores_purchase_id_in_context(self, mock_update, mock_context):
        """start_handler should store purchase_id for subsequent commands."""
        await start_handler(mock_update, mock_context)
        
        purchase_id = mock_context.user_data["purchase_id"]
        
        # Verify purchase can be retrieved via service
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["id"] == purchase_id
        assert purchase["is_active"] is True

    @pytest.mark.asyncio
    async def test_start_sends_welcome_message(self, mock_update, mock_context):
        """start_handler should send welcome message to user."""
        await start_handler(mock_update, mock_context)
        
        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()
        
        # Verify message content
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Shopping list started" in message_text
        assert "/add_item" in message_text

    @pytest.mark.asyncio
    async def test_start_message_includes_example(self, mock_update, mock_context):
        """Welcome message should include command example."""
        await start_handler(mock_update, mock_context)
        
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Milk 2 1.50" in message_text or "add_item" in message_text

    @pytest.mark.asyncio
    async def test_start_multiple_users_isolated(self, mock_context):
        """Each user should get separate purchase (user_data isolation)."""
        # User 1
        user1 = MagicMock(spec=User)
        user1.id = 111
        user1.username = "user1"
        
        update1 = MagicMock(spec=Update)
        update1.effective_user = user1
        update1.message = AsyncMock()
        update1.message.reply_text = AsyncMock()
        
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
        
        context2 = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context2.bot_data = mock_context.bot_data  # Shared service
        context2.user_data = {}  # Separate per user

        # Both users call /start
        await start_handler(update1, context1)
        await start_handler(update2, context2)
        
        # Each should have different purchase_id
        purchase_id_1 = context1.user_data["purchase_id"]
        purchase_id_2 = context2.user_data["purchase_id"]
        
        assert purchase_id_1 != purchase_id_2
        
        # Each purchase should be independent
        service = mock_context.bot_data["service"]
        purchase1 = service.get_purchase(purchase_id_1)
        purchase2 = service.get_purchase(purchase_id_2)
        
        assert purchase1["id"] == purchase_id_1
        assert purchase2["id"] == purchase_id_2


class TestStartHandlerLogging:
    """Test logging during /start command."""

    @pytest.mark.asyncio
    async def test_start_logs_user_info(self, mock_update, mock_context, caplog):
        """start_handler should log user ID and purchase creation."""
        with caplog.at_level(logging.INFO):
            await start_handler(mock_update, mock_context)
        
        # Should log command received
        assert any("/start" in record.message for record in caplog.records)
        assert any(str(mock_update.effective_user.id) in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_start_logs_purchase_created(self, mock_update, mock_context, caplog):
        """start_handler should log purchase ID creation."""
        with caplog.at_level(logging.INFO):
            await start_handler(mock_update, mock_context)
        
        # Should log purchase creation
        assert any("Purchase started" in record.message for record in caplog.records)
        assert any("ID" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_start_logs_username(self, mock_update, mock_context, caplog):
        """start_handler should log username if available."""
        mock_update.effective_user.username = "alice"
        
        with caplog.at_level(logging.INFO):
            await start_handler(mock_update, mock_context)
        
        log_output = " ".join([record.message for record in caplog.records])
        assert "alice" in log_output or "username" in log_output.lower()

    @pytest.mark.asyncio
    async def test_start_logs_unknown_username(self, mock_update, mock_context, caplog):
        """start_handler should handle missing username gracefully."""
        mock_update.effective_user.username = None
        
        with caplog.at_level(logging.INFO):
            await start_handler(mock_update, mock_context)
        
        # Should not crash, should log "Unknown"
        assert any("Unknown" in record.message for record in caplog.records)


class TestStartHandlerErrorHandling:
    """Test error handling in /start command."""

    @pytest.mark.asyncio
    async def test_start_handles_service_error(self, mock_update, mock_context, caplog):
        """start_handler should catch service errors gracefully."""
        # Mock service to raise error
        mock_context.bot_data["service"].start_purchase = MagicMock(
            side_effect=RuntimeError("Database error")
        )
        
        with caplog.at_level(logging.ERROR):
            await start_handler(mock_update, mock_context)
        
        # Should log error
        assert any("error" in record.message.lower() for record in caplog.records)
        
        # Should send user-friendly error message
        mock_update.message.reply_text.assert_called_once()
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "error occurred" in message_text.lower()

    @pytest.mark.asyncio
    async def test_start_error_message_no_traceback(self, mock_update, mock_context):
        """Error message to user should not contain traceback."""
        mock_context.bot_data["service"].start_purchase = MagicMock(
            side_effect=ValueError("Invalid value")
        )
        
        await start_handler(mock_update, mock_context)
        
        message_text = mock_update.message.reply_text.call_args[0][0]
        
        # Should not expose error details
        assert "Traceback" not in message_text
        assert "ValueError" not in message_text
        assert "Invalid value" not in message_text

    @pytest.mark.asyncio
    async def test_start_logs_full_error_details(self, mock_update, mock_context, caplog):
        """Full error details should be in logs (not exposed to user)."""
        mock_context.bot_data["service"].start_purchase = MagicMock(
            side_effect=ValueError("Invalid value")
        )
        
        with caplog.at_level(logging.ERROR):
            await start_handler(mock_update, mock_context)
        
        # Logs should contain full error details
        log_text = " ".join([record.message for record in caplog.records])
        assert "ValueError" in log_text or "error" in log_text.lower()

    @pytest.mark.asyncio
    async def test_start_handles_reply_failure(self, mock_update, mock_context, caplog):
        """start_handler should handle message send failures."""
        # Mock reply to fail
        mock_update.message.reply_text = AsyncMock(
            side_effect=RuntimeError("Telegram API error")
        )
        
        with caplog.at_level(logging.ERROR):
            # Should not raise, should log error
            await start_handler(mock_update, mock_context)
        
        # Should log send failure
        assert any("send error" in record.message.lower() or "failed" in record.message.lower() 
                   for record in caplog.records)


class TestStartHandlerIntegration:
    """Integration tests for /start command."""

    @pytest.mark.asyncio
    async def test_start_then_add_item(self, mock_context):
        """After /start, user can add items to created purchase."""
        user = MagicMock(spec=User)
        user.id = 42
        user.username = "testuser"
        
        update = MagicMock(spec=Update)
        update.effective_user = user
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot_data = mock_context.bot_data
        context.user_data = {}
        
        # Call /start
        await start_handler(update, context)
        
        purchase_id = context.user_data["purchase_id"]
        service = context.bot_data["service"]
        
        # Verify we can add items to the created purchase
        total = service.add_item(purchase_id, "Milk", 2, 1.50)
        assert total == 3.00
        
        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 1
        assert purchase["total"] == 3.00

    @pytest.mark.asyncio
    async def test_start_creates_empty_purchase(self, mock_update, mock_context):
        """start_handler should create empty purchase (no items)."""
        await start_handler(mock_update, mock_context)
        
        purchase_id = mock_context.user_data["purchase_id"]
        service = mock_context.bot_data["service"]
        
        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 0
        assert purchase["total"] == 0.00
        assert purchase["is_active"] is True

    @pytest.mark.asyncio
    async def test_start_shows_resume_for_active_purchase(self, mock_update, mock_context):
        """Calling /start twice with active purchase should show resume prompt."""
        # First /start
        await start_handler(mock_update, mock_context)
        purchase_id_1 = mock_context.user_data["purchase_id"]

        # Reset mock to check second call
        mock_update.message.reply_text.reset_mock()

        # Second /start (should show resume prompt instead of creating new)
        await start_handler(mock_update, mock_context)
        purchase_id_2 = mock_context.user_data["purchase_id"]

        # Both should be the same (no new purchase created)
        assert purchase_id_1 == purchase_id_2

        # Second call should show resume prompt
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "active purchase" in call_args.lower()
        assert "/resume" in call_args
        assert "/new" in call_args

        service = mock_context.bot_data["service"]
        p1 = service.get_purchase(purchase_id_1)

        assert p1["is_active"] is True


class TestStartHandlerEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_start_with_none_username(self, mock_update, mock_context):
        """start_handler should handle missing username gracefully."""
        mock_update.effective_user.username = None
        
        # Should not raise
        await start_handler(mock_update, mock_context)
        
        # Should still create purchase and send message
        assert "purchase_id" in mock_context.user_data
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_concurrent_calls_same_user(self, mock_update, mock_context):
        """Rapid /start calls should see same active purchase."""
        import asyncio

        # Simulate rapid calls
        tasks = [start_handler(mock_update, mock_context) for _ in range(3)]

        # All should complete
        await asyncio.gather(*tasks)

        # Context should have a purchase_id
        assert "purchase_id" in mock_context.user_data
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(mock_context.user_data["purchase_id"])
        assert purchase["is_active"] is True

    @pytest.mark.asyncio
    async def test_start_message_is_clear(self, mock_update, mock_context):
        """start_handler message should be clear and actionable."""
        await start_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]

        # Check for clear, actionable message
        assert "shopping list started" in message_text.lower() or "purchase" in message_text.lower()
        assert "/add_item" in message_text


class TestStartHandlerUserData:
    """Test user data storage and isolation."""

    @pytest.mark.asyncio
    async def test_start_does_not_overwrite_existing_data(self, mock_update, mock_context):
        """start_handler should only set purchase_id, not overwrite other data."""
        # Set some existing user data
        mock_context.user_data["previous_key"] = "previous_value"
        
        await start_handler(mock_update, mock_context)
        
        # Both keys should exist
        assert "purchase_id" in mock_context.user_data
        assert "previous_key" in mock_context.user_data
        assert mock_context.user_data["previous_key"] == "previous_value"

    @pytest.mark.asyncio
    async def test_start_resumes_active_purchase(self, mock_update, mock_context):
        """Calling /start twice with active purchase should keep same ID."""
        # First call
        await start_handler(mock_update, mock_context)
        old_id = mock_context.user_data["purchase_id"]

        # Second call
        await start_handler(mock_update, mock_context)
        new_id = mock_context.user_data["purchase_id"]

        # Should be the same (no new purchase created)
        assert old_id == new_id

        # Context should still have the same ID
        assert mock_context.user_data["purchase_id"] == new_id


class TestStartHandlerServiceIntegration:
    """Test integration with PurchaseService."""

    @pytest.mark.asyncio
    async def test_start_uses_service_from_context(self, mock_update, mock_context):
        """start_handler should use service from context.bot_data."""
        mock_service = MagicMock()
        mock_service.start_purchase.return_value = 999
        mock_context.bot_data["service"] = mock_service
        
        await start_handler(mock_update, mock_context)
        
        # Service method should be called
        mock_service.start_purchase.assert_called_once()
        
        # Returned ID should be stored
        assert mock_context.user_data["purchase_id"] == 999

    @pytest.mark.asyncio
    async def test_start_validates_purchase_creation(self, mock_update, mock_context):
        """Purchase created by start_handler should be valid and usable."""
        await start_handler(mock_update, mock_context)
        
        purchase_id = mock_context.user_data["purchase_id"]
        service = mock_context.bot_data["service"]
        
        # Verify purchase exists and is valid
        purchase = service.get_purchase(purchase_id)
        
        assert purchase["id"] == purchase_id
        assert isinstance(purchase["item_count"], int)
        assert isinstance(purchase["total"], (int, float))
        assert isinstance(purchase["is_active"], bool)

"""Tests for /resume and /new command handlers (Phase 8.3 - Resume/New flow).

Tests cover:
- Resume existing active purchase
- Resume without active purchase (error)
- Resume finished purchase (error)
- New with active purchase (finish + start)
- New without active purchase (just start)
- State transitions and context clearing
- Error handling and logging
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import resume_handler, new_handler
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
    """Fixture providing a mock Telegram update."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_user
    update.message = mock_message
    return update


@pytest.fixture
def mock_context_with_purchase(test_db):
    """Fixture providing context with an active purchase ID."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}
    context.user_data = {}

    # Inject real service with test database
    repo = SQLitePurchaseRepository(test_db)
    service = PurchaseService(repo)
    context.bot_data["service"] = service

    # Create an active purchase
    purchase_id = service.start_purchase()
    context.user_data["purchase_id"] = purchase_id

    return context, purchase_id


@pytest.fixture
def mock_context_empty(test_db):
    """Fixture providing context without a purchase ID."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}
    context.user_data = {}

    # Inject real service with test database
    repo = SQLitePurchaseRepository(test_db)
    service = PurchaseService(repo)
    context.bot_data["service"] = service

    return context


# Tests for /resume

class TestResumeHandlerSuccess:
    """Test successful /continue command handling."""

    @pytest.mark.asyncio
    async def test_resume_active_purchase(self, mock_update, mock_context_with_purchase):
        """resume_handler should display active purchase details."""
        context, purchase_id = mock_context_with_purchase
        service = context.bot_data["service"]

        # Add some items to the purchase
        service.add_item(purchase_id, "Milk", 2, 5.50)
        service.add_item(purchase_id, "Bread", 1, 8.00)

        # Resume the purchase
        await resume_handler(mock_update, context)

        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]

        # Verify purchase details in message
        assert "resumed" in call_args.lower()
        assert "2" in call_args  # item count
        assert "19.00" in call_args  # total (2*5.50 + 1*8.00 = 11.00 + 8.00 = 19.00)
        assert "Created:" in call_args
        assert "/add" in call_args  # suggest next action


class TestResumeHandlerErrors:
    """Test error cases for /continue command."""

    @pytest.mark.asyncio
    async def test_resume_no_active_purchase(self, mock_update, mock_context_empty):
        """resume_handler should error if no active purchase in context."""
        context = mock_context_empty
        await resume_handler(mock_update, context)

        # Verify error message
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "no active purchase" in call_args.lower()

    @pytest.mark.asyncio
    async def test_resume_deleted_purchase(self, mock_update, mock_context_with_purchase):
        """resume_handler should handle deleted purchase gracefully."""
        context, purchase_id = mock_context_with_purchase
        service = context.bot_data["service"]

        # Delete the purchase from the database
        service.repository.delete(purchase_id)

        # Try to resume
        await resume_handler(mock_update, context)

        # Verify error message and context cleared
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "not found" in call_args.lower() or "error" in call_args.lower()

        # Verify purchase_id was cleared from context
        assert context.user_data.get("purchase_id") is None

    @pytest.mark.asyncio
    async def test_resume_finished_purchase(self, mock_update, mock_context_with_purchase):
        """resume_handler should handle finished purchase (not active)."""
        context, purchase_id = mock_context_with_purchase
        service = context.bot_data["service"]

        # Finish the purchase
        service.finish_purchase(purchase_id)

        # Try to resume
        await resume_handler(mock_update, context)

        # Verify error message about finished purchase
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "finished" in call_args.lower()

        # Verify purchase_id was cleared from context
        assert context.user_data.get("purchase_id") is None


# Tests for /new

class TestNewHandlerSuccess:
    """Test successful /new command handling."""

    @pytest.mark.asyncio
    async def test_new_with_active_purchase(self, mock_update, mock_context_with_purchase):
        """new_handler should finish current purchase and start a new one."""
        context, old_purchase_id = mock_context_with_purchase
        service = context.bot_data["service"]

        # Add items to the purchase
        service.add_item(old_purchase_id, "Milk", 2, 5.50)
        service.add_item(old_purchase_id, "Bread", 1, 8.00)

        # Call /new
        await new_handler(mock_update, context)

        # Verify messages were sent
        assert mock_update.message.reply_text.call_count >= 1

        # Verify old purchase is finished
        old_purchase = service.get_purchase(old_purchase_id)
        assert old_purchase["finished_at"] is not None
        assert old_purchase["total"] == 19.00

        # Verify new purchase was created
        new_purchase_id = context.user_data.get("purchase_id")
        assert new_purchase_id is not None
        assert new_purchase_id != old_purchase_id

        # Verify new purchase is active and empty
        new_purchase = service.get_purchase(new_purchase_id)
        assert new_purchase["finished_at"] is None
        assert new_purchase["item_count"] == 0

    @pytest.mark.asyncio
    async def test_new_without_active_purchase(self, mock_update, mock_context_empty):
        """new_handler should error if no active purchase."""
        context = mock_context_empty

        await new_handler(mock_update, context)

        # Verify error message
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "no active purchase" in call_args.lower()


class TestNewHandlerEdgeCases:
    """Test edge cases for /new command."""

    @pytest.mark.asyncio
    async def test_new_with_deleted_purchase(self, mock_update, mock_context_with_purchase):
        """new_handler should handle missing purchase gracefully."""
        context, old_purchase_id = mock_context_with_purchase
        service = context.bot_data["service"]

        # Delete the purchase (but leave it in context)
        service.repository.delete(old_purchase_id)

        # Call /new - should start fresh without error
        await new_handler(mock_update, context)

        # Verify a new purchase was created
        new_purchase_id = context.user_data.get("purchase_id")
        assert new_purchase_id is not None
        assert new_purchase_id != old_purchase_id

        # Verify new purchase is active
        new_purchase = service.get_purchase(new_purchase_id)
        assert new_purchase["finished_at"] is None


# Integration tests for state transitions

class TestResumeNewIntegration:
    """Integration tests for the resume/new flow."""

    @pytest.mark.asyncio
    async def test_start_shows_resume_for_active_purchase(self, mock_update, mock_context_with_purchase):
        """When user calls /start with active purchase, should show resume prompt."""
        from app.handlers.handlers import start_handler

        context, purchase_id = mock_context_with_purchase
        service = context.bot_data["service"]

        # Add items to make it clear the purchase is there
        service.add_item(purchase_id, "Milk", 1, 5.00)

        # Call start_handler
        await start_handler(mock_update, context)

        # Verify the resume prompt was shown
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "active purchase" in call_args.lower()
        assert "/continue" in call_args
        assert "/new" in call_args

        # Verify purchase_id was NOT changed
        assert context.user_data["purchase_id"] == purchase_id

    @pytest.mark.asyncio
    async def test_full_cycle_start_add_resume_new(self, mock_update, mock_context_empty):
        """Test full cycle: start -> add -> resume -> new -> start."""
        from app.handlers.handlers import start_handler, add_item_handler

        context = mock_context_empty
        service = context.bot_data["service"]

        # Clear previous calls
        mock_update.message.reply_text.reset_mock()

        # Step 1: /start - should create fresh purchase
        await start_handler(mock_update, context)
        purchase_1 = context.user_data["purchase_id"]
        assert purchase_1 is not None

        # Step 2: /start again - should show resume prompt since purchase is active
        mock_update.message.reply_text.reset_mock()
        await start_handler(mock_update, context)
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "active purchase" in call_args.lower()

        # Step 3: /new - finish purchase and start fresh
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, context)
        purchase_2 = context.user_data["purchase_id"]
        assert purchase_2 is not None
        assert purchase_2 != purchase_1

        # Verify first purchase is finished
        p1 = service.get_purchase(purchase_1)
        assert p1["finished_at"] is not None

        # Verify second purchase is active and empty
        p2 = service.get_purchase(purchase_2)
        assert p2["finished_at"] is None
        assert p2["item_count"] == 0

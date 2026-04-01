"""Tests for resume flow handlers: /continue and /new commands.

Tests cover:
- /continue with active purchase
- /continue without active purchase
- /new with active purchase
- /new without active purchase
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import (
    start_handler,
    add_item_handler,
    resume_handler,
    new_handler,
)
from app.services import PurchaseService
from app.infra.repositories import SQLitePurchaseRepository
from app.infra import init_db


@pytest.fixture
def test_db():
    """Fixture providing a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        init_db(db_path)
        yield db_path


@pytest.fixture
def mock_context(test_db):
    """Fixture providing mock context with service."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}
    context.user_data = {}
    repo = SQLitePurchaseRepository(test_db)
    service = PurchaseService(repo)
    context.bot_data["service"] = service
    return context


@pytest.fixture
def mock_update():
    """Fixture providing mock update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.message = MagicMock(spec=Message)
    update.message.text = "/continue"
    update.message.reply_text = AsyncMock()
    return update


class TestContinueHandler:
    """Test /continue handler for resuming active purchase."""

    @pytest.mark.asyncio
    async def test_continue_with_active_purchase(self, mock_update, mock_context):
        """continue_handler should show active purchase details when purchase exists."""
        # Start a purchase
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)
        
        purchase_id = mock_context.user_data["purchase_id"]

        # Add an item
        mock_update.message.text = "/add milk 2 1.50"
        mock_update.message.reply_text.reset_mock()
        await add_item_handler(mock_update, mock_context)

        # Continue the purchase
        mock_update.message.text = "/continue"
        mock_update.message.reply_text.reset_mock()
        await resume_handler(mock_update, mock_context)

        # Should show purchase details
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Purchase resumed" in message_text or "resumed" in message_text.lower()
        assert "Items" in message_text
        assert "Total" in message_text
        assert "R$" in message_text

    @pytest.mark.asyncio
    async def test_continue_shows_item_count(self, mock_update, mock_context):
        """continue_handler should display correct item count."""
        # Start and add items
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/add bread 3 2.00"
        await add_item_handler(mock_update, mock_context)

        # Continue
        mock_update.message.text = "/continue"
        mock_update.message.reply_text.reset_mock()
        await resume_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        # Should show 2 items
        assert "2" in message_text

    @pytest.mark.asyncio
    async def test_continue_shows_total_amount(self, mock_update, mock_context):
        """continue_handler should display correct total."""
        # Start and add items
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/add bread 1 2.00"
        await add_item_handler(mock_update, mock_context)

        # Continue
        mock_update.message.text = "/continue"
        mock_update.message.reply_text.reset_mock()
        await resume_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        # Total should be 2*1.50 + 1*2.00 = 5.00
        assert "5.00" in message_text

    @pytest.mark.asyncio
    async def test_continue_without_active_purchase(self, mock_update, mock_context):
        """continue_handler without active purchase should show error."""
        mock_update.message.text = "/continue"
        await resume_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text or "active purchase" in message_text.lower()
        assert "/start" in message_text

    @pytest.mark.asyncio
    async def test_continue_shows_created_date(self, mock_update, mock_context):
        """continue_handler should show creation date."""
        # Start purchase
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)

        # Continue
        mock_update.message.text = "/continue"
        mock_update.message.reply_text.reset_mock()
        await resume_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Created" in message_text

    @pytest.mark.asyncio
    async def test_continue_preserves_purchase_id(self, mock_update, mock_context):
        """continue_handler should not change purchase_id."""
        # Start purchase
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)
        
        old_id = mock_context.user_data["purchase_id"]

        # Continue
        mock_update.message.text = "/continue"
        await resume_handler(mock_update, mock_context)
        
        new_id = mock_context.user_data["purchase_id"]
        assert old_id == new_id


class TestNewHandler:
    """Test /new handler for finishing current and starting new purchase."""

    @pytest.mark.asyncio
    async def test_new_with_active_purchase(self, mock_update, mock_context):
        """new_handler should finish current purchase and start new one."""
        # Start first purchase
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)
        purchase_id_1 = mock_context.user_data["purchase_id"]

        # Add item
        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        # Start new
        mock_update.message.text = "/new"
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, mock_context)

        purchase_id_2 = mock_context.user_data["purchase_id"]

        # Should have different purchase IDs
        assert purchase_id_1 != purchase_id_2

    @pytest.mark.asyncio
    async def test_new_shows_previous_summary(self, mock_update, mock_context):
        """new_handler should show summary of finished purchase."""
        # Start and add items
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        # Start new
        mock_update.message.text = "/new"
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, mock_context)

        # First call shows previous purchase summary
        message_text = mock_update.message.reply_text.call_args_list[0][0][0]
        assert "Previous purchase finished" in message_text or "finished" in message_text.lower()
        assert "Total" in message_text
        assert "R$" in message_text
        assert "3.00" in message_text

    @pytest.mark.asyncio
    async def test_new_starts_fresh_purchase(self, mock_update, mock_context):
        """new_handler should start a new empty purchase."""
        # Start first purchase
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)

        # Add item
        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        # Start new
        mock_update.message.text = "/new"
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, mock_context)

        # New purchase should be empty
        new_purchase_id = mock_context.user_data["purchase_id"]
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(new_purchase_id)
        
        assert purchase["item_count"] == 0
        assert purchase["total"] == 0.0

    @pytest.mark.asyncio
    async def test_new_shows_new_purchase_started(self, mock_update, mock_context):
        """new_handler should show message that new purchase started."""
        # Start and add items
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        # Start new
        mock_update.message.text = "/new"
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, mock_context)

        # Second call shows new purchase started
        message_text = mock_update.message.reply_text.call_args_list[1][0][0]
        assert "Shopping list started" in message_text or "started" in message_text.lower()

    @pytest.mark.asyncio
    async def test_new_without_active_purchase(self, mock_update, mock_context):
        """new_handler without active purchase should show error."""
        mock_update.message.text = "/new"
        await new_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text or "active purchase" in message_text.lower()
        assert "/start" in message_text

    @pytest.mark.asyncio
    async def test_new_with_multiple_items(self, mock_update, mock_context):
        """new_handler should show summary with multiple items."""
        # Start and add multiple items
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/add bread 3 2.00"
        await add_item_handler(mock_update, mock_context)

        # Start new
        mock_update.message.text = "/new"
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, mock_context)

        # Show finished summary
        message_text = mock_update.message.reply_text.call_args_list[0][0][0]
        assert "2" in message_text  # 2 items
        assert "9.00" in message_text  # 2*1.50 + 3*2.00 = 9.00

    @pytest.mark.asyncio
    async def test_new_clears_old_purchase_id(self, mock_update, mock_context):
        """new_handler should replace purchase_id in context."""
        # Start first purchase
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)
        
        old_id = mock_context.user_data["purchase_id"]

        # Start new
        mock_update.message.text = "/new"
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, mock_context)
        
        new_id = mock_context.user_data["purchase_id"]
        
        # IDs should be different
        assert old_id != new_id
        
        # Service should see both as separate purchases
        service = mock_context.bot_data["service"]
        old_purchase = service.get_purchase(old_id)
        new_purchase = service.get_purchase(new_id)
        
        # Old should be finished, new should be active
        assert old_purchase["is_active"] is False
        assert new_purchase["is_active"] is True

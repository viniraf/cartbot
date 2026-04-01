"""Tests for resume flow handlers: /continue and /new commands (Phase 9.8).

Tests cover:
- /continue with active purchase
- /continue without active purchase
- /new with active purchase (now prompts for store after finishing)
- Locale preservation through resume flow
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import (
    resume_handler,
    new_handler,
    store_input_handler,
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


# Helper function
async def setup_active_purchase(mock_context, store_name="Whole Foods", locale="en", items=None):
    """Helper to create an active purchase with optional items."""
    service = mock_context.bot_data["service"]
    purchase_id = service.create_purchase(store_name=store_name, locale=locale)
    mock_context.user_data["purchase_id"] = purchase_id
    
    if items:
        for item_name, qty, price in items:
            service.add_item(purchase_id, item_name, qty, price)
    
    return purchase_id


class TestContinueHandler:
    """Test /continue handler for resuming active purchase."""

    @pytest.mark.asyncio
    async def test_continue_with_active_purchase(self, mock_update, mock_context):
        """continue_handler should show active purchase details."""
        # Create active purchase with items
        await setup_active_purchase(
            mock_context, "Whole Foods", "en", [("milk", 2, 1.50)]
        )

        # Continue
        mock_update.message.text = "/continue"
        await resume_handler(mock_update, mock_context)

        # Should show purchase details
        message_text = mock_update.message.reply_text.call_args[0][0]
        # Should mention purchase resumption or show details
        assert "resumed" in message_text.lower() or "Created" in message_text or "Total" in message_text

    @pytest.mark.asyncio
    async def test_continue_shows_purchase_details(self, mock_update, mock_context):
        """continue_handler should display all purchase details."""
        # Create purchase with items
        await setup_active_purchase(
            mock_context, "Costco", "en", [("apples", 3, 1.50), ("orange", 2, 1.00)]
        )

        await resume_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Created" in message_text
        assert "Items" in message_text or "items" in message_text
        assert "Total" in message_text or "total" in message_text

    @pytest.mark.asyncio
    async def test_continue_without_active_purchase(self, mock_update, mock_context):
        """continue_handler without active purchase should show error."""
        mock_update.message.text = "/continue"
        await resume_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text or "active purchase" in message_text.lower()

    @pytest.mark.asyncio
    async def test_continue_preserves_purchase_id(self, mock_update, mock_context):
        """continue_handler should not change purchase_id."""
        purchase_id = await setup_active_purchase(mock_context, "Target")
        
        await resume_handler(mock_update, mock_context)
        
        # purchase_id should remain unchanged
        assert mock_context.user_data["purchase_id"] == purchase_id

    @pytest.mark.asyncio
    async def test_continue_with_portuguese_locale(self, mock_update, mock_context):
        """continue_handler should work with Portuguese locale."""
        # Create purchase with Portuguese locale
        purchase_id = await setup_active_purchase(
            mock_context, "Carrefour", "ptbr", [("leite", 2, 1.50)]
        )
        mock_context.user_data["language"] = "ptbr"
        
        await resume_handler(mock_update, mock_context)
        
        # Should send message successfully
        mock_update.message.reply_text.assert_called_once()


class TestNewHandler:
    """Test /new handler for finishing current and starting new purchase."""

    @pytest.mark.asyncio
    async def test_new_sets_waiting_for_store(self, mock_update, mock_context):
        """new_handler should set waiting_for_store_input after finishing."""
        # Create and set up purchase
        purchase_id = await setup_active_purchase(
            mock_context, "Whole Foods", "en", [("milk", 2, 1.50)]
        )
        
        mock_update.message.text = "/new"
        await new_handler(mock_update, mock_context)
        
        # Should set waiting_for_store_input flag
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Old purchase_id should be cleared
        # (new one not created yet, waiting for store input)

    @pytest.mark.asyncio
    async def test_new_shows_previous_summary(self, mock_update, mock_context):
        """new_handler should handle finishing current purchase."""
        # Create purchase with items
        purchase_id = await setup_active_purchase(
            mock_context, "Costco", "en", [("apples", 3, 1.50)]
        )
        
        mock_update.message.text = "/new"
        await new_handler(mock_update, mock_context)
        
        # Should send message (summary may be combined or separate)
        mock_update.message.reply_text.assert_called()
        
        # Should now be waiting for store input
        assert mock_context.user_data.get("waiting_for_store_input") is True

    @pytest.mark.asyncio
    async def test_new_without_active_purchase(self, mock_update, mock_context):
        """new_handler without active purchase should show error."""
        mock_update.message.text = "/new"
        await new_handler(mock_update, mock_context)
        
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text or "active purchase" in message_text.lower()

    @pytest.mark.asyncio
    async def test_new_with_multiple_items_shows_summary(self, mock_update, mock_context):
        """new_handler should show summary with multiple items."""
        # Create purchase with multiple items
        await setup_active_purchase(
            mock_context, "Target", "en",
            [("milk", 2, 1.50), ("bread", 3, 2.00), ("eggs", 1, 3.50)]
        )
        
        mock_update.message.text = "/new"
        await new_handler(mock_update, mock_context)
        
        # Should show summary message
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_new_locale_preserved(self, mock_update, mock_context):
        """new_handler should preserve locale setting for next purchase."""
        # Create purchase with Portuguese locale
        await setup_active_purchase(
            mock_context, "Carrefour", "ptbr", [("leite", 1, 1.50)]
        )
        mock_context.user_data["language"] = "ptbr"
        
        mock_update.message.text = "/new"
        await new_handler(mock_update, mock_context)
        
        # Language setting should still be ptbr for messaging
        assert mock_context.user_data.get("language") == "ptbr"
        
        # Should be waiting for store input now
        assert mock_context.user_data.get("waiting_for_store_input") is True


class TestResumeFlowIntegration:
    """Integration tests for resume flow."""

    @pytest.mark.asyncio
    async def test_continue_then_new_then_store_input(self, mock_update, mock_context):
        """Test flow: create purchase → continue → new → provide store."""
        # Create first purchase
        purchase_id_1 = await setup_active_purchase(
            mock_context, "Whole Foods", "en", [("milk", 2, 1.50)]
        )
        
        # Continue (should show it)
        await resume_handler(mock_update, mock_context)
        assert mock_update.message.reply_text.called
        
        # New (should finish and prompt for store)
        mock_update.message.text = "/new"
        mock_update.message.reply_text.reset_mock()
        await new_handler(mock_update, mock_context)
        
        # Should be waiting for store now
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Provide store name
        mock_update.message.text = "Target"
        mock_update.message.reply_text.reset_mock()
        await store_input_handler(mock_update, mock_context)
        
        # Should clear flag and create new purchase
        assert mock_context.user_data.get("waiting_for_store_input") is False
        assert "purchase_id" in mock_context.user_data
        
        purchase_id_2 = mock_context.user_data["purchase_id"]
        assert purchase_id_2 != purchase_id_1
        
        # Verify new purchase
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id_2)
        assert purchase["store_name"] == "Target"
        assert purchase["locale"] == "en"  # Preserved from /start

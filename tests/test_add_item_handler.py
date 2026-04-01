"""Tests for /add command handler (Phase 9.9 - Comma-Based Format).

Tests cover:
- Comma-based format parsing (inline and batch)
- Successful item addition
- Input validation
- Error handling (no active purchase, invalid format, etc.)
- Rejection of old pipe format
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import start_handler, add_item_handler, store_input_handler
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
    """Fixture providing mock context with service and empty user_data."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {}
    context.user_data = {}
    repo = SQLitePurchaseRepository(test_db)
    service = PurchaseService(repo)
    context.bot_data["service"] = service
    return context


@pytest.fixture
def mock_update():
    """Fixture providing mock update - message.text set per test."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


# Helper to setup active purchase
async def setup_active_purchase(mock_context):
    """Create an active purchase in context."""
    service = mock_context.bot_data["service"]
    purchase_id = service.create_purchase(store_name="Teste", locale="en")
    mock_context.user_data["purchase_id"] = purchase_id
    return purchase_id


class TestAddItemInlineCommaFormat:
    """Test /add with inline comma-based format."""

    @pytest.mark.asyncio
    async def test_add_item_inline_price_name(self, mock_update, mock_context):
        """Add item inline: /add price,name (qty defaults to 1)."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add 19.90,feijao"
        await add_item_handler(mock_update, mock_context)
        
        # Should respond with success
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "✓" in response or "added" in response.lower()
        
        # Verify item was added
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 1
        assert purchase["total"] == 19.90

    @pytest.mark.asyncio
    async def test_add_item_inline_price_qty_name(self, mock_update, mock_context):
        """Add item inline: /add price,qty,name."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add 20.50,2,file de frango"
        await add_item_handler(mock_update, mock_context)
        
        # Should respond with success
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "✓" in response or "added" in response.lower()
        
        # Verify item was added with correct quantity
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 1
        assert purchase["total"] == 41.00  # 20.50 * 2

    @pytest.mark.asyncio
    async def test_add_item_inline_multiword_name(self, mock_update, mock_context):
        """Add item inline with multiword name."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add 15.99,3,suco de laranja natural"
        await add_item_handler(mock_update, mock_context)
        
        # Should respond with success
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "✓" in response or "added" in response.lower()


class TestAddItemBatchCommaFormat:
    """Test /add with batch (multiline) comma-based format."""

    @pytest.mark.asyncio
    async def test_add_item_batch_multiple_lines(self, mock_update, mock_context):
        """Add multiple items as batch."""
        purchase_id = await setup_active_purchase(mock_context)
        
        batch_input = """/add
19.90,feijao
20.50,2,file de frango
5.30,miojo"""
        
        mock_update.message.text = batch_input
        await add_item_handler(mock_update, mock_context)
        
        # Should respond with success
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "✓" in response or "added" in response.lower()
        assert "3 item" in response  # Should show 3 items added
        
        # Verify all items were added
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 3
        # Total: 19.90 + (20.50 * 2) + 5.30 = 66.20
        assert abs(purchase["total"] - 66.20) < 0.01

    @pytest.mark.asyncio
    async def test_add_item_batch_single_line(self, mock_update, mock_context):
        """Batch format with one item on second line."""
        purchase_id = await setup_active_purchase(mock_context)
        
        batch_input = """/add
19.90,feijao"""
        
        mock_update.message.text = batch_input
        await add_item_handler(mock_update, mock_context)
        
        # Should work fine
        mock_update.message.reply_text.assert_called_once()
        
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 1


class TestAddItemErrors:
    """Test error handling in /add command."""

    @pytest.mark.asyncio
    async def test_add_item_no_content(self, mock_update, mock_context):
        """Just /add with no content should show usage."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add"
        await add_item_handler(mock_update, mock_context)
        
        # Should show usage message
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "Inline format" in response or "format" in response.lower()

    @pytest.mark.asyncio
    async def test_add_item_rejects_pipe_format(self, mock_update, mock_context):
        """Pipe format should be rejected."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add milk | 2 | 1.50"
        await add_item_handler(mock_update, mock_context)
        
        # Should reject with error message
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "no longer supported" in response.lower()
        assert "comma" in response.lower()

    @pytest.mark.asyncio
    async def test_add_item_invalid_format(self, mock_update, mock_context):
        """Invalid comma format should show error."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add abc"  # No comma
        await add_item_handler(mock_update, mock_context)
        
        # Should show error
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "Error" in response or "error" in response.lower()

    @pytest.mark.asyncio
    async def test_add_item_without_active_purchase(self, mock_update, mock_context):
        """Adding item without active purchase should fail."""
        mock_update.message.text = "/add 19.90,feijao"
        await add_item_handler(mock_update, mock_context)
        
        # Should show "no active purchase"
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in response or "start" in response.lower()

    @pytest.mark.asyncio
    async def test_add_item_invalid_price(self, mock_update, mock_context):
        """Invalid price should show error."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add abc,feijao"
        await add_item_handler(mock_update, mock_context)
        
        # Should show error
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "Error" in response

    @pytest.mark.asyncio
    async def test_add_item_invalid_quantity(self, mock_update, mock_context):
        """Invalid quantity should show error."""
        purchase_id = await setup_active_purchase(mock_context)
        
        mock_update.message.text = "/add 19.90,abc,feijao"
        await add_item_handler(mock_update, mock_context)
        
        # Should show error
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "Error" in response


class TestAddItemAccumulation:
    """Test adding multiple items and accumulation."""

    @pytest.mark.asyncio
    async def test_add_multiple_items_inline(self, mock_update, mock_context):
        """Add multiple items in separate inline commands."""
        purchase_id = await setup_active_purchase(mock_context)
        service = mock_context.bot_data["service"]
        
        # Add first item
        mock_update.message.text = "/add 10.00,2,item1"
        await add_item_handler(mock_update, mock_context)
        
        # Add second item
        mock_update.message.text = "/add 5.00,item2"
        await add_item_handler(mock_update, mock_context)
        
        # Verify both items
        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 2
        assert abs(purchase["total"] - 25.00) < 0.01  # 10*2 + 5*1

    @pytest.mark.asyncio
    async def test_add_batch_with_errors(self, mock_update, mock_context):
        """Batch with some valid and invalid items."""
        purchase_id = await setup_active_purchase(mock_context)
        
        batch_input = """/add
19.90,feijao
invalid_line
20.50,2,file de frango"""
        
        mock_update.message.text = batch_input
        await add_item_handler(mock_update, mock_context)
        
        # Should show partial success with errors
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        # Should indicate some items were added and some failed
        assert "✓" in response or "added" in response.lower()
        assert "Error" in response or "⚠" in response


class TestAddItemWaitingForStore:
    """Test flow lock: /add blocked when waiting for store."""

    @pytest.mark.asyncio
    async def test_add_blocked_when_waiting_for_store(self, mock_update, mock_context):
        """Cannot add items when waiting for store name."""
        # Start handler, should set waiting_for_store_input
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)
        
        # Now try to add item
        mock_update.message.reply_text.reset_mock()
        mock_update.message.text = "/add 19.90,feijao"
        await add_item_handler(mock_update, mock_context)
        
        # Should be blocked with store prompt
        mock_update.message.reply_text.assert_called_once()
        response = mock_update.message.reply_text.call_args[0][0]
        assert "store" in response.lower()

    @pytest.mark.asyncio
    async def test_add_works_after_store_provided(self, mock_update, mock_context):
        """Can add items after providing store name."""
        # Start and provide store
        mock_update.message.text = "/start"
        await start_handler(mock_update, mock_context)
        
        mock_update.message.text = "Supermarket"
        await store_input_handler(mock_update, mock_context)
        
        # Now add should work
        mock_update.message.reply_text.reset_mock()
        mock_update.message.text = "/add 19.90,feijao"
        await add_item_handler(mock_update, mock_context)
        
        # Should succeed
        response = mock_update.message.reply_text.call_args[0][0]
        assert "✓" in response or "added" in response.lower()
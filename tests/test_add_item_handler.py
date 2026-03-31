"""Tests for /add_item command handler.

Tests cover:
- Successful item addition
- Input validation (usage, invalid quantity/price)
- No active purchase (no /start)
- Multiple items accumulation
- Error handling
"""

import pytest
import logging
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import start_handler, add_item_handler
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


class TestAddItemSuccess:
    """Test successful /add handling."""

    @pytest.mark.asyncio
    async def test_add_item_responds_with_total(self, mock_update, mock_context):
        """add_item_handler should add item and respond with total."""
        # First /start to create purchase
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add milk 2 1.50"

        await add_item_handler(mock_update, mock_context)

        mock_update.message.reply_text.assert_called()
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Item added" in message_text
        assert "R$" in message_text
        assert "3.00" in message_text

    @pytest.mark.asyncio
    async def test_add_item_multiple_items_accumulate(self, mock_update, mock_context):
        """Multiple items should accumulate total correctly."""
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/add bread 1 2.00"
        await add_item_handler(mock_update, mock_context)

        service = mock_context.bot_data["service"]
        purchase_id = mock_context.user_data["purchase_id"]
        purchase = service.get_purchase(purchase_id)

        assert purchase["item_count"] == 2
        assert purchase["total"] == 5.00  # 3.00 + 2.00

    @pytest.mark.asyncio
    async def test_add_item_multiword_name(self, mock_update, mock_context):
        """add_item should accept multi-word item names."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add organic milk 1 2.50"

        await add_item_handler(mock_update, mock_context)

        service = mock_context.bot_data["service"]
        purchase_id = mock_context.user_data["purchase_id"]
        purchase = service.get_purchase(purchase_id)
        items = purchase.get("items", [])
        assert len(items) == 1
        assert items[0]["name"] == "organic milk"
        assert items[0]["quantity"] == 1
        assert items[0]["unit_price"] == 2.50

    @pytest.mark.asyncio
    async def test_add_item_pipe_format(self, mock_update, mock_context):
        """New pipe-separated syntax should be accepted."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add Milk | 2 | 1.50"

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Item added" in message_text
        assert "R$" in message_text
        assert "3.00" in message_text



class TestAddItemValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_add_item_no_args_shows_usage(self, mock_update, mock_context):
        """add_item with no args should show usage message."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add"

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in message_text
        assert "/add" in message_text
        assert "Example" in message_text

    @pytest.mark.asyncio
    async def test_add_item_two_args_shows_usage(self, mock_update, mock_context):
        """add_item with only 2 args should show usage."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add milk 2"

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in message_text or "Example" in message_text

    @pytest.mark.asyncio
    async def test_add_item_invalid_pipe_format(self, mock_update, mock_context):
        """Malformed pipe syntax should prompt format error."""
        await start_handler(mock_update, mock_context)
        # missing one segment
        mock_update.message.text = "/add Milk | 2"

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Invalid format" in message_text
        assert "/add Name | qty | price" in message_text

    @pytest.mark.asyncio
    async def test_add_item_invalid_quantity_rejects(self, mock_update, mock_context):
        """add_item with non-numeric quantity should reject."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add milk abc 1.50"

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Invalid" in message_text or "Error" in message_text

    @pytest.mark.asyncio
    async def test_add_item_invalid_price_rejects(self, mock_update, mock_context):
        """add_item with non-numeric price should reject."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add milk 2 xyz"

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Invalid" in message_text or "Error" in message_text


class TestAddItemNoPurchase:
    """Test add_item when no active purchase."""

    @pytest.mark.asyncio
    async def test_add_item_without_start_shows_message(self, mock_update, mock_context):
        """add_item without /start should prompt to use /start."""
        mock_update.message.text = "/add milk 2 1.50"
        # No start_handler call - user_data has no purchase_id

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text
        assert "/start" in message_text


class TestAddItemDomainErrors:
    """Test domain exception handling."""

    @pytest.mark.asyncio
    async def test_add_item_negative_quantity_validation_error(self, mock_update, mock_context):
        """add_item with negative quantity should send Error message."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add milk -1 1.50"

        await add_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Error" in message_text or "error" in message_text.lower()
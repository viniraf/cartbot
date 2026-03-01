"""Tests for Phase 6 CRUD handlers: view_total, list_items, edit_item, delete_item."""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import (
    start_handler,
    add_item_handler,
    view_total_handler,
    list_items_handler,
    edit_item_handler,
    delete_item_handler,
    finish_handler,
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
    update.message.reply_text = AsyncMock()
    return update


class TestViewTotalHandler:
    """Test /view_total handler."""

    @pytest.mark.asyncio
    async def test_view_total_shows_total_and_count(self, mock_update, mock_context):
        """view_total_handler should display total and item count."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/view_total"
        await view_total_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Total" in message_text
        assert "R$" in message_text
        assert "3.00" in message_text
        assert "Items" in message_text
        assert "1" in message_text

    @pytest.mark.asyncio
    async def test_view_total_empty_purchase(self, mock_update, mock_context):
        """view_total with no items should show 0."""
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/view_total"
        await view_total_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "R$" in message_text
        assert "0.00" in message_text
        assert "Items" in message_text

    @pytest.mark.asyncio
    async def test_view_total_without_start(self, mock_update, mock_context):
        """view_total without /start should prompt to use /start."""
        mock_update.message.text = "/view_total"
        await view_total_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text
        assert "/start" in message_text


class TestListItemsHandler:
    """Test /list_items handler."""

    @pytest.mark.asyncio
    async def test_list_items_shows_all_items(self, mock_update, mock_context):
        """list_items_handler should show formatted items with 1-based indices."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item milk 2 1.50"
        await add_item_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item bread 1 2.00"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/list_items"
        await list_items_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "1." in message_text
        assert "milk" in message_text.lower()
        assert "2." in message_text
        assert "bread" in message_text.lower()
        assert "R$" in message_text  # milk subtotal
        assert "3.00" in message_text
        assert "R$" in message_text  # bread subtotal
        assert "2.00" in message_text

    @pytest.mark.asyncio
    async def test_list_items_empty_shows_no_items(self, mock_update, mock_context):
        """list_items with no items should show 'No items yet'."""
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/list_items"
        await list_items_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No items yet" in message_text

    @pytest.mark.asyncio
    async def test_list_items_without_start(self, mock_update, mock_context):
        """list_items without /start should prompt to use /start."""
        mock_update.message.text = "/list_items"
        await list_items_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text


class TestDeleteItemHandler:
    """Test /delete_item handler."""

    @pytest.mark.asyncio
    async def test_delete_item_removes_and_updates_total(self, mock_update, mock_context):
        """delete_item_handler should remove item and show new total."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item milk 2 1.50"
        await add_item_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item bread 1 2.00"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/delete_item 2"
        await delete_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Item deleted" in message_text
        assert "R$" in message_text  # Only milk left
        assert "3.00" in message_text

    @pytest.mark.asyncio
    async def test_delete_item_first_item(self, mock_update, mock_context):
        """delete_item 1 should remove first item."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item milk 1 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/delete_item 1"
        await delete_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Item deleted" in message_text
        assert "R$" in message_text
        assert "0.00" in message_text

    @pytest.mark.asyncio
    async def test_delete_item_no_args_shows_usage(self, mock_update, mock_context):
        """delete_item with no args should show usage."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/delete_item"

        await delete_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in message_text
        assert "delete_item" in message_text

    @pytest.mark.asyncio
    async def test_delete_item_without_start(self, mock_update, mock_context):
        """delete_item without /start should prompt to use /start."""
        mock_update.message.text = "/delete_item 1"
        await delete_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text


class TestEditItemHandler:
    """Test /edit_item handler."""

    @pytest.mark.asyncio
    async def test_edit_item_updates_and_shows_total(self, mock_update, mock_context):
        """edit_item_handler should update item and show new total."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/edit_item 1 3 2.00"
        await edit_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Item updated" in message_text
        assert "R$" in message_text  # 3 * 2.00
        assert "6.00" in message_text

    @pytest.mark.asyncio
    async def test_edit_item_list_shows_updated(self, mock_update, mock_context):
        """After edit, list_items should show updated values."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item milk 1 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/edit_item 1 5 2.00"
        await edit_item_handler(mock_update, mock_context)

        mock_update.message.text = "/list_items"
        await list_items_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "5" in message_text
        assert "R$" in message_text
        assert "2.00" in message_text
        assert "R$" in message_text
        assert "10.00" in message_text

    @pytest.mark.asyncio
    async def test_edit_item_no_args_shows_usage(self, mock_update, mock_context):
        """edit_item with insufficient args should show usage."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/edit_item"

        await edit_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in message_text
        assert "edit_item" in message_text

    @pytest.mark.asyncio
    async def test_edit_item_without_start(self, mock_update, mock_context):
        """edit_item without /start should prompt to use /start."""
        mock_update.message.text = "/edit_item 1 2 1.50"
        await edit_item_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text


class TestFinishHandler:
    """Test /finish handler."""

    @pytest.mark.asyncio
    async def test_finish_shows_summary_and_clears_state(self, mock_update, mock_context):
        """finish_handler should show summary, clear purchase_id, and prompt for /start."""
        await start_handler(mock_update, mock_context)
        mock_update.message.text = "/add_item milk 2 1.50"
        await add_item_handler(mock_update, mock_context)

        mock_update.message.text = "/finish"
        await finish_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Purchase finished" in message_text
        assert "Total" in message_text
        assert "R$" in message_text
        assert "3.00" in message_text
        assert "Items" in message_text
        assert "1" in message_text
        assert "/start" in message_text

        assert "purchase_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_finish_resets_for_new_purchase(self, mock_update, mock_context):
        """After /finish, /start should create fresh purchase with new ID."""
        await start_handler(mock_update, mock_context)
        purchase_id_1 = mock_context.user_data["purchase_id"]
        mock_update.message.text = "/finish"
        await finish_handler(mock_update, mock_context)

        await start_handler(mock_update, mock_context)
        purchase_id_2 = mock_context.user_data["purchase_id"]

        assert purchase_id_1 != purchase_id_2

    @pytest.mark.asyncio
    async def test_finish_empty_purchase(self, mock_update, mock_context):
        """finish_handler should work with empty purchase (0 items, $0 total)."""
        await start_handler(mock_update, mock_context)

        mock_update.message.text = "/finish"
        await finish_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "Purchase finished" in message_text
        assert "R$" in message_text
        assert "0.00" in message_text
        assert "Items" in message_text
        assert "0" in message_text
        assert "purchase_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_finish_without_start(self, mock_update, mock_context):
        """finish without /start should prompt to use /start."""
        mock_update.message.text = "/finish"
        await finish_handler(mock_update, mock_context)

        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "No active purchase" in message_text
        assert "/start" in message_text

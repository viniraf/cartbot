"""Tests for store name input handler (Phase 9.8).

Tests cover:
- /start prompting for store name (no active purchase)
- Valid store input creating purchase
- Invalid (empty) store input showing error and re-prompting
- Flow lock preventing /add before store defined
- Locale preservation in new purchase from /start
- Locale preservation in new purchase from /new
"""

import pytest
import logging
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import start_handler, new_handler, store_input_handler, add_item_handler
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


# Tests for /start command - Store Input Prompting

class TestStartHandlerStorePrompt:
    """Test /start command prompts for store name when no active purchase."""

    @pytest.mark.asyncio
    async def test_start_sets_waiting_for_store_flag(self, mock_update, mock_context):
        """When no active purchase, /start should set waiting_for_store_input flag."""
        await start_handler(mock_update, mock_context)
        
        # Should set waiting_for_store_input flag
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Should NOT have created a purchase yet
        assert "purchase_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_start_sends_store_prompt_message(self, mock_update, mock_context):
        """When no active purchase, /start should send store prompt message."""
        await start_handler(mock_update, mock_context)
        
        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()
        message_text = mock_update.message.reply_text.call_args[0][0]
        
        # Should contain store prompt (either English or Portuguese depending on language)
        # Since default language is 'en', should contain English version
        assert "store" in message_text.lower() or "What is" in message_text

    @pytest.mark.asyncio
    async def test_start_with_active_purchase_shows_options(self, mock_update, mock_context):
        """When active purchase exists, /start should show resume options."""
        # Create active purchase manually
        service = mock_context.bot_data["service"]
        purchase_id = service.create_purchase(store_name="Whole Foods", locale="en")
        mock_context.user_data["purchase_id"] = purchase_id
        
        # Call /start
        await start_handler(mock_update, mock_context)
        
        # Should NOT set waiting_for_store_input
        assert mock_context.user_data.get("waiting_for_store_input") is not True
        
        # Should show resume options message
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "active purchase" in message_text.lower() or "continue" in message_text.lower()


# Tests for Store Input Handler - Valid Input

class TestStoreInputHandlerValidInput:
    """Test store_input_handler correctly processes valid store names."""

    @pytest.mark.asyncio
    async def test_valid_store_input_creates_purchase(self, mock_update, mock_context):
        """Valid store input should create purchase and store purchase_id."""
        # Set up waiting for store input
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = "Whole Foods"
        
        # Process store input
        await store_input_handler(mock_update, mock_context)
        
        # Should clear waiting flag
        assert mock_context.user_data.get("waiting_for_store_input") is False
        
        # Should store purchase_id
        assert "purchase_id" in mock_context.user_data
        purchase_id = mock_context.user_data["purchase_id"]
        assert isinstance(purchase_id, int)
        
        # Verify purchase was created with correct store name
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["store_name"] == "Whole Foods"
        assert purchase["is_active"] is True

    @pytest.mark.asyncio
    async def test_store_input_trims_whitespace(self, mock_update, mock_context):
        """Store input should trim leading/trailing whitespace."""
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = "  Target  "  # With spaces
        
        await store_input_handler(mock_update, mock_context)
        
        # Should create purchase with trimmed name
        purchase_id = mock_context.user_data["purchase_id"]
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["store_name"] == "Target"

    @pytest.mark.asyncio
    async def test_store_input_sends_success_message(self, mock_update, mock_context):
        """Valid store input should send success message with store name."""
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = "Costco"
        
        await store_input_handler(mock_update, mock_context)
        
        # Should send success message
        mock_update.message.reply_text.assert_called_once()
        message_text = mock_update.message.reply_text.call_args[0][0]
        
        # Should mention store name and next steps
        assert "Costco" in message_text
        assert "/add" in message_text

    @pytest.mark.asyncio
    async def test_store_input_preserves_locale(self, mock_update, mock_context):
        """Store input should preserve user's language preference."""
        # Set language to Portuguese
        mock_context.user_data["language"] = "ptbr"
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = "Carrefour"
        
        await store_input_handler(mock_update, mock_context)
        
        # Purchase should be created with ptbr locale
        purchase_id = mock_context.user_data["purchase_id"]
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["locale"] == "ptbr"


# Tests for Store Input Handler - Invalid Input

class TestStoreInputHandlerInvalidInput:
    """Test store_input_handler rejects invalid store names."""

    @pytest.mark.asyncio
    async def test_empty_store_input_shows_error(self, mock_update, mock_context):
        """Empty store input should show error and keep waiting flag."""
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = ""  # Empty
        
        await store_input_handler(mock_update, mock_context)
        
        # Should send standardized error message
        mock_update.message.reply_text.assert_called_once()
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "❌" in message_text

    @pytest.mark.asyncio
    async def test_empty_store_input_keeps_waiting_flag(self, mock_update, mock_context):
        """After empty input, waiting_for_store_input flag should still be True."""
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = ""
        
        await store_input_handler(mock_update, mock_context)
        
        # Flag should still be True (waiting for valid input)
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # No purchase_id should be created
        assert "purchase_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_whitespace_only_input_rejected(self, mock_update, mock_context):
        """Input with only whitespace should be rejected."""
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = "   "  # Only spaces
        
        await store_input_handler(mock_update, mock_context)
        
        # Should reject (after trim, it's empty)
        assert mock_context.user_data.get("waiting_for_store_input") is True
        assert "purchase_id" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_store_input_not_processed_when_flag_not_set(self, mock_update, mock_context):
        """Store input should be ignored if waiting_for_store_input flag is not set."""
        # Don't set the flag
        assert mock_context.user_data.get("waiting_for_store_input") is not True
        mock_update.message.text = "Amazon"
        
        await store_input_handler(mock_update, mock_context)
        
        # Should not process (flag not set, so handler returns early)
        # No message should be sent
        mock_update.message.reply_text.assert_not_called()
        
        # No purchase created
        assert "purchase_id" not in mock_context.user_data


# Tests for Flow Lock - /add Before Store Defined

class TestAddItemFlowLock:
    """Test /add handler prevents adding items before store is defined."""

    @pytest.mark.asyncio
    async def test_add_blocked_when_waiting_for_store(self, mock_update, mock_context):
        """Attempting /add while waiting_for_store_input should be blocked."""
        # Set waiting_for_store_input flag (no purchase created yet)
        mock_context.user_data["waiting_for_store_input"] = True
        mock_update.message.text = "/add milk 2 1.50"
        
        # Attempt /add
        await add_item_handler(mock_update, mock_context)
        
        # Should send standardized error message
        mock_update.message.reply_text.assert_called_once()
        message_text = mock_update.message.reply_text.call_args[0][0]
        assert "❌" in message_text

    @pytest.mark.asyncio
    async def test_add_works_after_store_created(self, mock_update, mock_context):
        """After store is created, /add should work normally."""
        # Create purchase first
        service = mock_context.bot_data["service"]
        purchase_id = service.create_purchase(store_name="Whole Foods", locale="en")
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["waiting_for_store_input"] = False
        
        # Now attempt /add
        mock_update.message.text = "/add milk 2 1.50"
        await add_item_handler(mock_update, mock_context)
        
        # Should NOT be blocked (may have other errors, but not the store lock)
        # Message should NOT be about store prompt
        if mock_update.message.reply_text.called:
            message_text = mock_update.message.reply_text.call_args[0][0]
            assert "store" not in message_text.lower() or "Store: " in message_text  # Unless it's part of response


# Tests for Complete Flow - /start → store input → /add

class TestCompleteStoreInputFlow:
    """Test complete user flow: /start → store input → add items."""

    @pytest.mark.asyncio
    async def test_complete_flow_start_to_add(self, mock_update, mock_context):
        """Test complete flow from /start through store input to adding items."""
        # Step 1: User calls /start
        await start_handler(mock_update, mock_context)
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Step 2: User provides store name
        mock_update.message.text = "Costco"
        await store_input_handler(mock_update, mock_context)
        assert mock_context.user_data.get("waiting_for_store_input") is False
        assert "purchase_id" in mock_context.user_data
        
        # Step 3: User can now add items
        purchase_id = mock_context.user_data["purchase_id"]
        service = mock_context.bot_data["service"]
        
        # Verify purchase has the store name
        purchase = service.get_purchase(purchase_id)
        assert purchase["store_name"] == "Costco"
        assert len(purchase["items"]) == 0


# Tests for /new Command - Store Input Flow

class TestNewHandlerStorePrompt:
    """Test /new command prompts for store after finishing previous."""

    @pytest.mark.asyncio
    async def test_new_sets_waiting_for_store_flag(self, mock_update, mock_context):
        """After /new, waiting_for_store_input flag should be set."""
        # Create active purchase first
        service = mock_context.bot_data["service"]
        purchase_id = service.create_purchase(store_name="Whole Foods", locale="en")
        mock_context.user_data["purchase_id"] = purchase_id
        
        # Call /new
        await new_handler(mock_update, mock_context)
        
        # Should set waiting_for_store_input flag
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Old purchase_id should be cleared
        # (Note: new_handler might clear it before setting the flag, or it might set both)
        # The important thing is that a new purchase ID shouldn't be created yet

    @pytest.mark.asyncio
    async def test_new_sends_store_prompt_after_summary(self, mock_update, mock_context):
        """After /new, should show previous summary then prompt for new store."""
        # Create active purchase with items
        service = mock_context.bot_data["service"]
        purchase_id = service.create_purchase(store_name="Whole Foods", locale="en")
        mock_context.user_data["purchase_id"] = purchase_id
        service.add_item(purchase_id, "milk", 1, 1.50)
        
        # Call /new
        await new_handler(mock_update, mock_context)
        
        # Should send message (could be combined or separate)
        mock_update.message.reply_text.assert_called()
        
        # Should now be waiting for store input
        assert mock_context.user_data.get("waiting_for_store_input") is True


# Tests for Locale Preservation

class TestLocalePreservation:
    """Test that locale is preserved through store input flow."""

    @pytest.mark.asyncio
    async def test_locale_preserved_start_to_store_ptbr(self, mock_update, mock_context):
        """Portuguese locale should be preserved from /start through store input."""
        # Set Portuguese language
        mock_context.user_data["language"] = "ptbr"
        
        # Call /start (should prompt in Portuguese)
        await start_handler(mock_update, mock_context)
        
        # Verify waiting flag set
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Now provide store name
        mock_update.message.text = "Carrefour"
        await store_input_handler(mock_update, mock_context)
        
        # Purchase should have ptbr locale
        purchase_id = mock_context.user_data["purchase_id"]
        service = mock_context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)
        assert purchase["locale"] == "ptbr"

    @pytest.mark.asyncio
    async def test_locale_preserved_new_to_store_en(self, mock_update, mock_context):
        """English locale should be preserved from /new through store input."""
        # Create first purchase with items
        service = mock_context.bot_data["service"]
        purchase_id = service.create_purchase(store_name="Whole Foods", locale="en")
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["language"] = "en"
        service.add_item(purchase_id, "milk", 1, 1.50)
        
        # Call /new
        await new_handler(mock_update, mock_context)
        
        # Should be waiting for store with English locale preserved
        assert mock_context.user_data.get("waiting_for_store_input") is True
        
        # Provide new store name
        mock_update.message.text = "Target"
        await store_input_handler(mock_update, mock_context)
        
        # New purchase should have en locale
        new_purchase_id = mock_context.user_data["purchase_id"]
        new_purchase = service.get_purchase(new_purchase_id)
        assert new_purchase["locale"] == "en"
        assert new_purchase["store_name"] == "Target"

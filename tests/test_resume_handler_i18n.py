"""Tests for /continue (resume) handler localization (Bug 07).

Tests cover:
- Resume message displayed in correct language (EN)
- Resume message displayed in correct language (PT-BR)
- Active purchase display respects language preference
- Store name and totals interpolate correctly
"""

import pytest
import logging
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from app.handlers.handlers import resume_handler, start_handler
from app.domain import NotFoundError, ValidationError
from app.services import PurchaseService
from app.infra.repositories import SQLitePurchaseRepository
from app.infra import init_db
from app.common.messages.messages_en import MESSAGES as MESSAGES_EN
from app.common.messages.messages_ptbr import MESSAGES as MESSAGES_PTBR


# Fixtures

@pytest.fixture
def test_db():
    """Fixture providing a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        init_db(db_path)
        yield db_path


@pytest.fixture
def mock_update():
    """Fixture providing a mock Telegram Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = 123
    update.effective_user.username = "testuser"
    update.message = AsyncMock()
    update.message.text = "/continue"  # Default for resume tests
    return update


@pytest.fixture
def mock_update_start():
    """Fixture providing a mock Telegram Update for /start command."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = 123
    update.effective_user.username = "testuser"
    update.message = AsyncMock()
    update.message.text = "/start"  # For start handler tests
    return update


@pytest.fixture
def mock_context(test_db):
    """Fixture providing a mock context with service."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    
    # Set up service
    repository = SQLitePurchaseRepository(test_db)
    service = PurchaseService(repository)
    context.bot_data = {"service": service}
    
    return context


class TestResumeHandlerEnglish:
    """Test resume handler displays messages in English."""

    @pytest.mark.asyncio
    async def test_resume_active_purchase_english(self, mock_update, mock_context):
        """Resume should display active purchase details in English."""
        # Setup: Create active purchase and set English language
        service = mock_context.bot_data["service"]
        purchase_id = service.start_purchase()
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["language"] = "en"
        
        # Execute
        await resume_handler(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        
        # Should contain English messages
        assert MESSAGES_EN["RESUME_TITLE"] in call_args
        assert "Created:" in call_args  # English label
        assert "Items:" in call_args  # English label
        assert "Total:" in call_args  # English label
        assert "Actions:" in call_args  # English label

    @pytest.mark.asyncio
    async def test_resume_finished_purchase_english(self, mock_update, mock_context):
        """Resume finished purchase should show English message."""
        # Setup: Create finished purchase
        service = mock_context.bot_data["service"]
        purchase_id = service.start_purchase()
        service.finish_purchase(purchase_id)
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["language"] = "en"
        
        # Execute
        await resume_handler(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        
        # Should contain English "finished" message
        assert MESSAGES_EN["RESUME_FINISHED"] in call_args


class TestResumeHandlerPortuguese:
    """Test resume handler displays messages in Portuguese."""

    @pytest.mark.asyncio
    async def test_resume_active_purchase_portuguese(self, mock_update, mock_context):
        """Resume should display active purchase details in Portuguese."""
        # Setup: Create active purchase and set Portuguese language
        service = mock_context.bot_data["service"]
        purchase_id = service.start_purchase()
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["language"] = "ptbr"
        
        # Execute
        await resume_handler(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        
        # Should contain Portuguese messages (NOT English)
        assert MESSAGES_PTBR["RESUME_TITLE"] in call_args
        assert "Criada em:" in call_args  # Portuguese label
        assert "Itens:" in call_args  # Portuguese label (not "Items:")
        assert "Total:" in call_args  # Used in both languages
        assert "Ações:" in call_args  # Portuguese label (not "Actions:")

    @pytest.mark.asyncio
    async def test_resume_finished_purchase_portuguese(self, mock_update, mock_context):
        """Resume finished purchase should show Portuguese message."""
        # Setup: Create finished purchase
        service = mock_context.bot_data["service"]
        purchase_id = service.start_purchase()
        service.finish_purchase(purchase_id)
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["language"] = "ptbr"
        
        # Execute
        await resume_handler(mock_update, mock_context)
        
        # Verify
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        
        # Should contain Portuguese "finished" message
        assert MESSAGES_PTBR["RESUME_FINISHED"] in call_args


class TestStartHandlerActivePreservesLanguage:
    """Test start handler shows active purchase in correct language."""

    @pytest.mark.asyncio
    async def test_start_active_purchase_english(self, mock_update_start, mock_context):
        """Start with active purchase should display in English."""
        # Setup: Create active purchase and set English
        service = mock_context.bot_data["service"]
        purchase_id = service.start_purchase()
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["language"] = "en"
        
        # Execute
        await start_handler(mock_update_start, mock_context)
        
        # Verify
        mock_update_start.message.reply_text.assert_called_once()
        call_args = mock_update_start.message.reply_text.call_args[0][0]
        
        # Should show English messages for active purchase
        assert MESSAGES_EN["START_ACTIVE"] in call_args
        assert "Created:" in call_args  # English label

    @pytest.mark.asyncio
    async def test_start_active_purchase_portuguese(self, mock_update_start, mock_context):
        """Start with active purchase should display in Portuguese."""
        # Setup: Create active purchase and set Portuguese
        service = mock_context.bot_data["service"]
        purchase_id = service.start_purchase()
        mock_context.user_data["purchase_id"] = purchase_id
        mock_context.user_data["language"] = "ptbr"
        
        # Execute
        await start_handler(mock_update_start, mock_context)
        
        # Verify
        mock_update_start.message.reply_text.assert_called_once()
        call_args = mock_update_start.message.reply_text.call_args[0][0]
        
        # Should show Portuguese messages for active purchase
        assert MESSAGES_PTBR["START_ACTIVE"] in call_args
        assert "Criada em:" in call_args  # Portuguese label (not "Created:")

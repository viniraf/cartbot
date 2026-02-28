"""Telegram bot initialization and bootstrap.

This module sets up the Telegram bot application, handlers, and polling loop.
It follows the modular monolith pattern, keeping handlers thin and delegating
to the service layer for business logic.
"""

import logging
from telegram.ext import Application, ContextTypes

from app.infra import Config
from app.services import PurchaseService
from app.infra.repositories import SQLitePurchaseRepository


logger = logging.getLogger(__name__)


def create_app() -> Application:
    """Create and configure the Telegram bot Application.

    Sets up:
    - Application instance with the bot token
    - Context settings for user and bot data storage
    - Service layer in bot context (dependency injection)

    Returns:
        Application: Configured bot application instance.

    Raises:
        ValueError: If TELEGRAM_TOKEN is invalid or missing.
    """
    logger.info("Initializing Telegram bot application...")

    # Create application with token from config
    app = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # Wire up service layer (dependency injection via bot context)
    # Repository uses database from config
    repository = SQLitePurchaseRepository(Config.DATABASE_PATH)
    service = PurchaseService(repository)

    # Store service in bot context for all handlers to access
    # Handlers retrieve via: context.bot_data['service']
    app.bot_data["service"] = service

    logger.info("Bot application initialized successfully")
    return app


def setup_handlers(app: Application) -> None:
    """Register all handlers with the bot application.

    Handlers are added in order of priority:
    1. Command handlers (/start, /add_item, etc.)
    2. Message handlers (fallback)
    3. Error handler (catches all exceptions)

    Args:
        app: The Application instance to configure.

    Note:
        This is a placeholder for Phase 5.2+.
        Handlers will be imported and registered incrementally.
    """
    logger.info("Setting up handlers...")
    # Handlers will be registered here in Phase 5.2+
    # from app.handlers.handlers import (
    #     start_handler,
    #     add_item_handler,
    #     # ... other handlers
    # )
    # app.add_handler(CommandHandler("start", start_handler))
    # app.add_handler(CommandHandler("add_item", add_item_handler))
    logger.info("Handler setup complete (no handlers registered yet)")


def run_bot(app: Application) -> None:
    """Start the bot polling loop.

    Runs the bot in polling mode (long-polling, suitable for development).
    Sets drop_pending_updates=True to ignore messages while bot was offline.

    Handles graceful shutdown on Ctrl+C.

    Args:
        app: The Application instance to run.

    Note:
        For production, consider:
        - Webhook mode (faster, requires public IP/domain)
        - Proxy configuration if behind firewall
    """
    logger.info("Starting bot polling...")
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal (Ctrl+C)")
    finally:
        logger.info("Bot stopped")

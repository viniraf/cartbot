"""Telegram command handlers for CartBot.

This module contains all command handlers that respond to user interactions.
Handlers are thin wrappers that:
1. Extract user/message data from Telegram update
2. Delegate business logic to the service layer
3. Format and send responses back to user
4. Log operations for debugging

Each handler follows the pattern:
    async def handler(update, context):
        service = context.bot_data['service']
        # Use service (stateless, framework-agnostic)
        # Reply to user
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.domain import NotFoundError, ValidationError


logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - initialize new shopping list.

    Responds to /start command by:
    1. Creating a new purchase via service
    2. Storing purchase_id in user context for future commands
    3. Sending welcome message to user
    4. Logging operation for debugging

    Args:
        update: Telegram update containing message and user info
        context: Handler context with bot_data (service) and user_data storage

    User flow:
        User: /start
        Bot: "Shopping list started. /add_item to begin."
        (Purchase ID is stored in context.user_data['purchase_id'])

    Error handling:
        - Service errors → "An error occurred. Please try again."
        - Full error logged for debugging
    """
    try:
        # Extract user information
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        logger.info(f"[User {user_id}] /start command received (username: {username})")

        # Get service from bot context (injected during create_app)
        service = context.bot_data["service"]

        # Create new purchase via stateless service
        purchase_id = service.start_purchase()

        # Store purchase_id in user context for subsequent commands
        # context.user_data is per-user storage (separate for each Telegram user)
        context.user_data["purchase_id"] = purchase_id

        logger.info(f"[User {user_id}] Purchase started with ID {purchase_id}")

        # Send welcome message to user
        await update.message.reply_text(
            f"🛒 Shopping list started!\n"
            f"Use /add_item to add items.\n"
            f"Example: /add_item Milk 2 1.50"
        )

    except Exception as e:
        # Log full error for debugging
        logger.error(f"[User {update.effective_user.id}] /start handler error: {type(e).__name__}: {str(e)}")

        # Send user-friendly error message (no traceback exposed)
        try:
            await update.message.reply_text(
                "❌ An error occurred. Please try again later."
            )
        except Exception as send_error:
            logger.error(f"Failed to send error message to user {update.effective_user.id}: {send_error}")


async def add_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add_item command - add item to active purchase.

    Parses input: /add_item [name] [quantity] [unit_price]
    Requires purchase_id in context (from /start).
    """
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /add_item command received")

        # Check for active purchase
        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(
                "No active purchase. Use /start to begin."
            )
            return

        # Parse arguments: /add_item name quantity unit_price
        text = (update.message.text or "").strip()
        args = text.split()[1:]  # Skip command

        if len(args) < 3:
            await update.message.reply_text(
                "Usage: /add_item [name] [quantity] [unit_price]\n"
                "Example: /add_item milk 2 1.50"
            )
            return

        # Parse quantity and unit_price (last two args); name is the rest
        try:
            quantity = int(args[-2])
            unit_price = float(args[-1])
            name = " ".join(args[:-2])
        except (ValueError, IndexError):
            await update.message.reply_text(
                "Invalid input. Quantity must be a whole number, price a number.\n"
                "Example: /add_item milk 2 1.50"
            )
            return

        if not name:
            await update.message.reply_text(
                "Item name cannot be empty.\n"
                "Example: /add_item milk 2 1.50"
            )
            return

        # Call service
        service = context.bot_data["service"]
        total = service.add_item(purchase_id, name, quantity, unit_price)

        logger.info(f"[User {user_id}] Item '{name}' x{quantity} added to purchase {purchase_id}")

        await update.message.reply_text(
            f"Item added. Total: ${total:.2f}"
        )

    except NotFoundError as e:
        logger.warning(f"[User {update.effective_user.id}] /add_item NotFoundError: {e}")
        await update.message.reply_text(f"Error: {e}")
    except ValidationError as e:
        logger.warning(f"[User {update.effective_user.id}] /add_item ValidationError: {e}")
        await update.message.reply_text(f"Error: {e}")
    except Exception as e:
        logger.error(f"[User {update.effective_user.id}] /add_item handler error: {type(e).__name__}: {e}")
        try:
            await update.message.reply_text("An error occurred. Please try again later.")
        except Exception:
            pass

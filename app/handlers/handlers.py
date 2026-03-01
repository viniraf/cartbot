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

import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.domain import NotFoundError, ValidationError
from app.common.formatters import format_currency, append_help_hint, format_command_block
from app.common.validators import parse_add_item_input


logger = logging.getLogger(__name__)

# User-facing messages (Phase 7.3 - UX consistency)
MSG_NO_ACTIVE_PURCHASE = "No active purchase. Use /start to begin."
MSG_ERROR_GENERIC = "An error occurred. Please try again later."
MSG_ADD_ITEM_USAGE = "Usage: /add_item [name] [quantity] [unit_price]\nExample: /add_item milk 2 1.50"
MSG_DELETE_ITEM_USAGE = "Usage: /delete_item [index]\nExample: /delete_item 1"
MSG_EDIT_ITEM_USAGE = "Usage: /edit_item [index] [new_quantity] [new_price]\nExample: /edit_item 1 3 2.00"


def safe_handler(func):
    """Decorator that catches unhandled exceptions and sends user-friendly message.

    Logs exception at ERROR level with traceback. Sends generic error message to user.
    Handlers should catch NotFoundError and ValidationError for specific messages.
    """

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except (NotFoundError, ValidationError):
            raise  # Let handler provide specific message
        except Exception as e:
            logger.exception(
                "Unhandled exception in %s: %s: %s",
                func.__name__,
                type(e).__name__,
                e,
            )
            try:
                if update and update.message:
                    error_msg = MSG_ERROR_GENERIC
                    await update.message.reply_text(append_help_hint(error_msg))
            except Exception as send_err:
                logger.error("Failed to send error message to user: %s", send_err)

    return wrapper


@safe_handler
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
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"

    logger.info("[User %s] /start command received (username: %s)", user_id, username)

    service = context.bot_data["service"]
    purchase_id = service.start_purchase()

    context.user_data["purchase_id"] = purchase_id

    logger.info("[User %s] Purchase started with ID %s", user_id, purchase_id)

    msg = "Shopping list started."
    commands = ["", "Use /add_item to add items", "Use /list_items to see all items"]
    await update.message.reply_text(append_help_hint(msg + "\n" + format_command_block(commands)))


@safe_handler
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
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        text = (update.message.text or "").strip()
        # drop the command itself
        body = text[len("/add_item") :].strip()

        # try new pipe-based syntax first
        if "|" in body:
            try:
                name, quantity, unit_price = parse_add_item_input(body)
            except ValueError as err:
                logger.warning("[User %s] /add_item pipe parse error: %s", user_id, err)
                msg_lines = [
                    "Invalid format.",
                    "",
                    "Use:",
                    "/add_item Name | qty | price",
                    "",
                    "Example:",
                    "/add_item Milk | 2 | 5.50",
                ]
                await update.message.reply_text(append_help_hint(format_command_block(msg_lines)))
                return
        else:
            # fallback to original whitespace-separated parser for backwards compatibility
            args = body.split()
            if len(args) < 3:
                logger.warning("[User %s] /add_item invalid args: %s", user_id, args)
                await update.message.reply_text(append_help_hint(MSG_ADD_ITEM_USAGE))
                return
            try:
                quantity = int(args[-2])
                unit_price = float(args[-1])
                name = " ".join(args[:-2])
            except (ValueError, IndexError):
                logger.warning("[User %s] /add_item invalid input: %s", user_id, args)
                msg_lines = [
                    "Invalid input. Quantity must be a whole number, price a number.",
                    "",
                    "Use:",
                    MSG_ADD_ITEM_USAGE.split("Usage:")[1].strip() if "Usage:" in MSG_ADD_ITEM_USAGE else MSG_ADD_ITEM_USAGE,
                ]
                await update.message.reply_text(append_help_hint(format_command_block(msg_lines)))
                return

            if not name:
                msg_lines = [
                    "Item name cannot be empty.",
                    "",
                    "Use:",
                    MSG_ADD_ITEM_USAGE.split("Usage:")[1].strip() if "Usage:" in MSG_ADD_ITEM_USAGE else MSG_ADD_ITEM_USAGE,
                ]
                await update.message.reply_text(append_help_hint(format_command_block(msg_lines)))
                return

        # Call service
        service = context.bot_data["service"]
        total = service.add_item(purchase_id, name, quantity, unit_price)

        logger.info(f"[User {user_id}] Item '{name}' x{quantity} added to purchase {purchase_id}")

        text = "Item added.\n\nTotal: " + format_currency(total) + "\n\nUse /list_items to see all items."
        await update.message.reply_text(append_help_hint(text))

    except NotFoundError as e:
        logger.warning("[User %s] /add_item NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))
    except ValidationError as e:
        logger.warning("[User %s] /add_item ValidationError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))


@safe_handler
async def view_total_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /view_total command - show current total and item count."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /view_total command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        service = context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)

        total = purchase["total"]
        count = purchase["item_count"]

        text = "Total: " + format_currency(total) + "\n\nItems: " + str(count)
        await update.message.reply_text(append_help_hint(text))

    except NotFoundError as e:
        logger.warning("[User %s] /view_total NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)


@safe_handler
async def list_items_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list_items command - show all items in current purchase."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /list_items command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        service = context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)

        items = purchase.get("items", [])
        if not items:
            await update.message.reply_text(append_help_hint("No items yet. Use /add_item to add items."))
            return

        item_lines = ["Items", ""]
        for i, item in enumerate(items, start=1):
            name = item["name"]
            qty = item["quantity"]
            price = item["unit_price"]
            subtotal = qty * price
            item_lines.append(
                f"{i}. {name} × {qty} @ {format_currency(price)} = {format_currency(subtotal)}"
            )

        total = sum(item["quantity"] * item["unit_price"] for item in items)
        item_lines.append("")
        item_lines.append(f"Total: {format_currency(total)}")
        item_lines.append("")
        item_lines.append("Actions:")
        item_lines.append("/delete_item N — remove item")
        item_lines.append("/edit_item N qty price — modify item")
        
        await update.message.reply_text(append_help_hint(format_command_block(item_lines)))

    except NotFoundError as e:
        logger.warning("[User %s] /list_items NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)


@safe_handler
async def delete_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /delete_item command - remove item by index (1-based)."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /delete_item command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        text = (update.message.text or "").strip()
        args = text.split()[1:]

        if len(args) < 1:
            logger.warning("[User %s] /delete_item missing args", user_id)
            await update.message.reply_text(MSG_DELETE_ITEM_USAGE)
            return

        try:
            user_index = int(args[0])
        except ValueError:
            logger.warning("[User %s] /delete_item invalid index: %s", user_id, args)
            await update.message.reply_text(append_help_hint("Invalid index. Use a number.\n\n" + MSG_DELETE_ITEM_USAGE))
            return

        if user_index < 1:
            await update.message.reply_text(append_help_hint("Index must be 1 or greater.\n\n" + MSG_DELETE_ITEM_USAGE))
            return

        # Convert 1-based (user) to 0-based (internal)
        item_index = user_index - 1

        service = context.bot_data["service"]
        total = service.remove_item(purchase_id, item_index)

        logger.info(f"[User {user_id}] Item {user_index} deleted from purchase {purchase_id}")

        await update.message.reply_text(append_help_hint(f"Item deleted.\n\nNew total: {format_currency(total)}"))

    except NotFoundError as e:
        logger.warning("[User %s] /delete_item NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))


@safe_handler
async def edit_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /edit_item command - modify item quantity or price by index (1-based)."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /edit_item command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        text = (update.message.text or "").strip()
        args = text.split()[1:]

        if len(args) < 3:
            logger.warning("[User %s] /edit_item invalid args: %s", user_id, args)
            await update.message.reply_text(MSG_EDIT_ITEM_USAGE)
            return

        try:
            user_index = int(args[0])
            quantity = int(args[1])
            unit_price = float(args[2])
        except (ValueError, IndexError):
            logger.warning("[User %s] /edit_item invalid input: %s", user_id, args)
            await update.message.reply_text(
                "Invalid input. Index and quantity must be whole numbers, price a number.\n" + MSG_EDIT_ITEM_USAGE
            )
            return

        if user_index < 1:
            await update.message.reply_text(append_help_hint("Index must be 1 or greater.\n\n" + MSG_EDIT_ITEM_USAGE))
            return

        item_index = user_index - 1

        service = context.bot_data["service"]
        total = service.edit_item(purchase_id, item_index, quantity=quantity, unit_price=unit_price)

        logger.info(f"[User {user_id}] Item {user_index} edited in purchase {purchase_id}")

        await update.message.reply_text(append_help_hint(f"Item updated.\n\nNew total: {format_currency(total)}"))

    except NotFoundError as e:
        logger.warning("[User %s] /edit_item NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))
    except ValidationError as e:
        logger.warning("[User %s] /edit_item ValidationError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))


@safe_handler
async def finish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /finish command - complete purchase and show final summary."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /finish command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        service = context.bot_data["service"]
        result = service.finish_purchase(purchase_id)

        total = result["total"]
        count = result["item_count"]

        logger.info("[User %s] Purchase %s finished (total=%.2f, items=%s)", user_id, purchase_id, total, count)

        summary_lines = [
            "Purchase finished.",
            "",
            f"Total: {format_currency(total)}",
            f"Items: {count}",
            "",
            "/start — begin a new purchase",
        ]
        text = format_command_block(summary_lines)
        await update.message.reply_text(append_help_hint(text))

        # Clear purchase_id so next /start creates fresh purchase
        context.user_data.pop("purchase_id", None)

    except NotFoundError as e:
        logger.warning("[User %s] /finish NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)


@safe_handler
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command by displaying all available commands.

    Message is sectioned into Session, Items, and Overview groups.  Uses
    formatting helpers for consistency and appends the standard help hint.
    """
    # Build the help text with blank lines separating sections
    lines = [
        "Available Commands",
        "",
        "Session",
        "/start — start or resume a purchase",
        "/finish — finish current purchase",
        "",
        "Items",
        "/add_item Name | qty | price",
        "/edit_item index qty price",
        "/delete_item index",
        "",
        "Overview",
        "/view_total — show total",
        "/list_items — show all items",
    ]
    text = format_command_block(lines)
    await update.message.reply_text(append_help_hint(text))

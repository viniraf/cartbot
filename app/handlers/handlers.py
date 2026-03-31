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
from app.common.messages import format_message, set_language, get_language


logger = logging.getLogger(__name__)

# User-facing messages (Phase 7.3 - UX consistency)
MSG_NO_ACTIVE_PURCHASE = "No active purchase. Use /start to begin."
MSG_ERROR_GENERIC = "An error occurred. Please try again later."
MSG_ADD_ITEM_USAGE = "Usage: /add [name] [quantity] [unit_price]\nExample: /add milk 2 1.50"
MSG_DELETE_ITEM_USAGE = "Usage: /delete [index]\nExample: /delete 1"
MSG_EDIT_ITEM_USAGE = "Usage: /edit [index] [new_quantity] [new_price]\nExample: /edit 1 3 2.00"


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
    """Handle /start command - initialize new shopping list or resume existing.

    Responds to /start command by:
    1. Checking if user has an active (unfinished) purchase in context
    2. If active purchase exists: show resume/new prompt
    3. If no active purchase: create new purchase
    4. Storing purchase_id in user context for future commands
    5. Logging operation for debugging

    Args:
        update: Telegram update containing message and user info
        context: Handler context with bot_data (service) and user_data storage

    User flows:
        Case 1: No active purchase
            User: /start
            Bot: "Shopping list started. /add_item to begin."

        Case 2: Active purchase exists
            User: /start
            Bot: "You have an active purchase..."
                 "/resume — continue this purchase"
                 "/new — finish and start a new one"

    Error handling:
        - Service errors ÔåÆ "An error occurred. Please try again."
        - Full error logged for debugging
    """
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"

    logger.info("[User %s] /start command received (username: %s)", user_id, username)

    service = context.bot_data["service"]

    # Check if user has an active purchase
    current_purchase_id = context.user_data.get("purchase_id")
    if current_purchase_id is not None:
        try:
            active_purchase = service.get_active_purchase(current_purchase_id)
            if active_purchase is not None:
                # Purchase is active - show resume/new prompt
                logger.info("[User %s] Found active purchase %s", user_id, current_purchase_id)

                total = active_purchase.get("total", 0)
                created_at = active_purchase.get("created_at", "Unknown")
                item_count = active_purchase.get("item_count", 0)

                prompt_lines = [
                    "You have an active purchase.",
                    "",
                    f"Created: {created_at[:10]}",
                    f"Items: {item_count}",
                    f"Total: {format_currency(total)}",
                    "",
                    "Options:",
                    "/continue — continue this purchase",
                    "/new — finish and start a new one",
                ]
                await update.message.reply_text(append_help_hint(format_command_block(prompt_lines)))
                return
        except NotFoundError:
            # Purchase was deleted or doesn't exist - clear context and continue
            logger.warning("[User %s] Active purchase %s not found, clearing context", user_id, current_purchase_id)
            context.user_data.pop("purchase_id", None)

    # No active purchase - create new one
    purchase_id = service.start_purchase()
    context.user_data["purchase_id"] = purchase_id

    logger.info("[User %s] New purchase started with ID %s", user_id, purchase_id)

    msg = "Shopping list started."
    commands = ["", "Use /add to add items", "Use /list to see all items"]
    await update.message.reply_text(append_help_hint(msg + "\n" + format_command_block(commands)))


@safe_handler
async def add_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add command - add item to active purchase.

    Parses input: /add [name] [quantity] [unit_price]
    Requires purchase_id in context (from /start).
    """
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /add command received")

        # Check for active purchase
        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        text = (update.message.text or "").strip()
        # drop the command itself
        body = text[len("/add") :].strip()

        # try new pipe-based syntax first
        if "|" in body:
            try:
                name, quantity, unit_price = parse_add_item_input(body)
            except ValueError as err:
                logger.warning("[User %s] /add pipe parse error: %s", user_id, err)
                msg_lines = [
                    "Invalid format.",
                    "",
                    "Use:",
                    "/add Name | qty | price",
                    "",
                    "Example:",
                    "/add Milk | 2 | 5.50",
                ]
                await update.message.reply_text(append_help_hint(format_command_block(msg_lines)))
                return
        else:
            # fallback to original whitespace-separated parser for backwards compatibility
            args = body.split()
            if len(args) < 3:
                logger.warning("[User %s] /add invalid args: %s", user_id, args)
                await update.message.reply_text(append_help_hint(MSG_ADD_ITEM_USAGE))
                return
            try:
                quantity = int(args[-2])
                unit_price = float(args[-1])
                name = " ".join(args[:-2])
            except (ValueError, IndexError):
                logger.warning("[User %s] /add invalid input: %s", user_id, args)
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

        text = "Item added.\n\nTotal: " + format_currency(total) + "\n\nUse /list to see all items."
        await update.message.reply_text(append_help_hint(text))

    except NotFoundError as e:
        logger.warning("[User %s] /add NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))
    except ValidationError as e:
        logger.warning("[User %s] /add ValidationError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))


@safe_handler
async def view_total_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /total command - show current total and item count."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /total command received")

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
        logger.warning("[User %s] /total NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)


@safe_handler
async def list_items_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command - show all items in current purchase."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /list command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        service = context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)

        items = purchase.get("items", [])
        if not items:
            await update.message.reply_text(append_help_hint("No items yet. Use /add to add items."))
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
        item_lines.append("/delete N — remove item")
        item_lines.append("/edit N qty price — modify item")
        
        await update.message.reply_text(append_help_hint(format_command_block(item_lines)))

    except NotFoundError as e:
        logger.warning("[User %s] /list NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)


@safe_handler
async def delete_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /delete command - remove item by index (1-based)."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /delete command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        text = (update.message.text or "").strip()
        args = text.split()[1:]

        if len(args) < 1:
            logger.warning("[User %s] /delete missing args", user_id)
            await update.message.reply_text(MSG_DELETE_ITEM_USAGE)
            return

        try:
            user_index = int(args[0])
        except ValueError:
            logger.warning("[User %s] /delete invalid index: %s", user_id, args)
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
        logger.warning("[User %s] /delete NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))


@safe_handler
async def edit_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /edit command - modify item quantity or price by index (1-based)."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /edit command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(MSG_NO_ACTIVE_PURCHASE)
            return

        text = (update.message.text or "").strip()
        args = text.split()[1:]

        if len(args) < 3:
            logger.warning("[User %s] /edit invalid args: %s", user_id, args)
            await update.message.reply_text(MSG_EDIT_ITEM_USAGE)
            return

        try:
            user_index = int(args[0])
            quantity = int(args[1])
            unit_price = float(args[2])
        except (ValueError, IndexError):
            logger.warning("[User %s] /edit invalid input: %s", user_id, args)
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
        logger.warning("[User %s] /edit NotFoundError: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(f"Error: {e}"))
    except ValidationError as e:
        logger.warning("[User %s] /edit ValidationError: %s", update.effective_user.id, e)
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
async def resume_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /continue command - continue an existing active purchase.

    Displays the current purchase details and confirms the session is active.
    Requires user to have called /start which found an active purchase.

    Args:
        update: Telegram update containing message and user info
        context: Handler context with purchase_id in user_data

    User flow:
        User: /start (sees active purchase prompt)
        User: /resume
        Bot: Shows purchase details, items, and total

    Edge cases:
        - Resume without active purchase: "No active purchase. Use /start to begin."
        - Resume with deleted purchase: "Purchase not found."
    """
    try:
        user_id = update.effective_user.id
        logger.info("[User %s] /continue command received", user_id)

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(append_help_hint(MSG_NO_ACTIVE_PURCHASE))
            return

        service = context.bot_data["service"]

        try:
            purchase = service.get_active_purchase(purchase_id)
        except NotFoundError:
            logger.warning("[User %s] /resume Purchase %s not found", user_id, purchase_id)
            context.user_data.pop("purchase_id", None)
            await update.message.reply_text(append_help_hint("Purchase not found."))
            return

        if purchase is None:
            # Purchase was found but is finished (not active)
            logger.info("[User %s] /resume Purchase %s is finished", user_id, purchase_id)
            context.user_data.pop("purchase_id", None)
            await update.message.reply_text(
                append_help_hint(
                    "This purchase is finished. Use /start to begin a new purchase."
                )
            )
            return

        # Purchase is active - show details
        total = purchase.get("total", 0)
        item_count = purchase.get("item_count", 0)
        created_at = purchase.get("created_at", "Unknown")

        logger.info("[User %s] Resumed purchase %s (items=%s, total=%.2f)", user_id, purchase_id, item_count, total)

        summary_lines = [
            "Purchase resumed.",
            "",
            f"Created: {created_at[:10]}",
            f"Items: {item_count}",
            f"Total: {format_currency(total)}",
            "",
            "Actions:",
            "/add — add item",
            "/list — show all items",
            "/finish — complete purchase",
        ]
        await update.message.reply_text(append_help_hint(format_command_block(summary_lines)))

    except Exception as e:
        logger.exception("[User %s] /continue error: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(MSG_ERROR_GENERIC))


@safe_handler
async def new_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new command - finish current purchase and start a new one.

    Completes the active purchase and initializes a fresh purchase.
    Provides final summary of the finished purchase.

    Args:
        update: Telegram update containing message and user info
        context: Handler context with purchase_id in user_data

    User flow:
        User: /start (sees active purchase prompt)
        User: /new
        Bot: Shows summary of finished purchase, then starts new one

    Edge cases:
        - /new without active purchase: "No active purchase. Use /start to begin."
        - /new with deleted purchase: Clean context and start fresh
    """
    try:
        user_id = update.effective_user.id
        logger.info("[User %s] /new command received", user_id)

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            await update.message.reply_text(append_help_hint(MSG_NO_ACTIVE_PURCHASE))
            return

        service = context.bot_data["service"]

        try:
            # Finish the current purchase
            result = service.finish_purchase(purchase_id)

            total = result.get("total", 0)
            count = result.get("item_count", 0)

            logger.info("[User %s] Purchase %s finished (total=%.2f, items=%s)", user_id, purchase_id, total, count)

            # Show summary of finished purchase
            summary_lines = [
                "Previous purchase finished.",
                "",
                f"Total: {format_currency(total)}",
                f"Items: {count}",
            ]
            await update.message.reply_text(format_command_block(summary_lines))

        except NotFoundError:
            logger.warning("[User %s] /new Purchase %s not found, starting fresh", user_id, purchase_id)

        # Clear old purchase and start new one
        context.user_data.pop("purchase_id", None)
        new_purchase_id = service.start_purchase()
        context.user_data["purchase_id"] = new_purchase_id

        logger.info("[User %s] New purchase started with ID %s", user_id, new_purchase_id)

        # Announce new purchase
        msg = "Shopping list started."
        commands = ["", "Use /add to add items", "Use /list to see all items"]
        await update.message.reply_text(append_help_hint(msg + "\n" + format_command_block(commands)))

    except Exception as e:
        logger.exception("[User %s] /new error: %s", update.effective_user.id, e)
        await update.message.reply_text(append_help_hint(MSG_ERROR_GENERIC))


@safe_handler
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command by displaying all available commands.

    Message is sectioned into Session, Items, and Overview groups. Uses
    message system for localization and formatting helpers for consistency.
    """
    lines = [
        format_message(context, "HELP_TITLE"),
        "",
        format_message(context, "HELP_SESSION_TITLE"),
        format_message(context, "HELP_START"),
        format_message(context, "HELP_RESUME"),
        format_message(context, "HELP_NEW"),
        format_message(context, "HELP_FINISH"),
        "",
        format_message(context, "HELP_ITEMS_TITLE"),
        format_message(context, "HELP_ADD_ITEM"),
        format_message(context, "HELP_EDIT_ITEM"),
        format_message(context, "HELP_DELETE_ITEM"),
        "",
        format_message(context, "HELP_OVERVIEW_TITLE"),
        format_message(context, "HELP_VIEW_TOTAL"),
        format_message(context, "HELP_LIST_ITEMS"),
    ]
    text = format_command_block(lines)
    await update.message.reply_text(append_help_hint(text))


@safe_handler
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /lang command - switch language preference.

    Allows user to switch between English and Portuguese (Brazil).
    Language preference is stored per user in context.user_data.

    Args:
        update: Telegram update containing message and user info
        context: Handler context with user_data for language storage

    User flows:
        User: /lang ptbr
        Bot: "Idioma alterado para Portugu├¬s."

        User: /lang en
        Bot: "Language set to English."

        User: /lang invalid
        Bot: "Invalid language. Use: /lang en or /lang ptbr"
    """
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /lang command received")

        text = (update.message.text or "").strip()
        args = text.split()[1:]

        if len(args) < 1:
            logger.warning(f"[User {user_id}] /lang missing args")
            msg = format_message(context, "LANG_USAGE")
            await update.message.reply_text(append_help_hint(msg))
            return

        requested_language = args[0].lower()

        # Try to set the language
        if set_language(context, requested_language):
            logger.info(f"[User {user_id}] Language changed to {requested_language}")

            # Show confirmation based on language set
            if requested_language == "en":
                msg = format_message(context, "LANG_SET_EN")
            else:
                msg = format_message(context, "LANG_SET_PTBR")

            await update.message.reply_text(append_help_hint(msg))
        else:
            logger.warning(f"[User {user_id}] Invalid language: {requested_language}")
            msg = format_message(context, "LANG_INVALID")
            await update.message.reply_text(append_help_hint(msg))

    except Exception as e:
        logger.exception(f"[User {update.effective_user.id}] /lang error: {e}")
        msg = format_message(context, "ERROR_GENERIC")
        await update.message.reply_text(append_help_hint(msg))

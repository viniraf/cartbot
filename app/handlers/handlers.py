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
from app.common.validators import parse_add_item_input, parse_add_input
from app.common.messages import format_message, set_language, get_language


logger = logging.getLogger(__name__)


def format_error_message(context, error_type: str) -> str:
    """Format a standardized error message with title, explanation, example, and help footer.

    Error structure (Phase 9.13):
    ❌ Title
    
    Explanation.
    
    Correct format: /command example
    
    Type /help for more information.

    Args:
        context: Handler context with user language preference
        error_type: Error type (e.g., "NO_ACTIVE_PURCHASE", "INVALID_ADD_FORMAT")

    Returns:
        Formatted multi-line error message
    """
    title = format_message(context, f"ERROR_{error_type}_TITLE")
    explanation = format_message(context, f"ERROR_{error_type}_EXPLANATION")
    example = format_message(context, f"ERROR_{error_type}_EXAMPLE")
    footer = format_message(context, "ERROR_HELP_FOOTER")
    
    return f"{title}\n\n{explanation}\n\n{example}\n\n{footer}"



def safe_handler(func):
    """Decorator that catches unhandled exceptions and sends user-friendly message.

    Logs exception at ERROR level with traceback. Sends standardized error message to user.
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
                    error_msg = format_error_message(context, "GENERIC")
                    await update.message.reply_text(error_msg)
            except Exception as send_err:
                logger.error("Failed to send error message to user: %s", send_err)

    return wrapper


@safe_handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - initialize new shopping list or resume existing.

    Supports localization parameters:
    - /start → use current or default locale
    - /start en → set EN-US
    - /start ptbr → set PT-BR
    - /start [other] → error

    Responds to /start command by:
    1. Parsing optional locale parameter
    2. Validating locale and setting user language
    3. Checking if user has an active (unfinished) purchase in context
    4. If active purchase exists: show resume/new prompt
    5. If no active purchase: create new purchase with locale
    6. Storing purchase_id in user context for future commands
    7. Logging operation for debugging

    Args:
        update: Telegram update containing message and user info
        context: Handler context with bot_data (service) and user_data storage

    User flows:
        Case 1: No active purchase, no locale param
            User: /start
            Bot: "Shopping list started. /add to begin."

        Case 2: No active purchase, with locale param
            User: /start ptbr
            Bot: "Shopping list started. /add para adicionar itens."

        Case 3: Invalid locale param
            User: /start fr
            Bot: "Error: Invalid locale. Supported: en, ptbr"

    Error handling:
        - Service errors → "An error occurred. Please try again."
        - Invalid locale → "Error: Invalid locale. Supported: en, ptbr"
        - Full error logged for debugging
    """
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"

    logger.info("[User %s] /start command received (username: %s)", user_id, username)

    service = context.bot_data["service"]
    
    # Parse optional locale parameter from command
    text = update.message.text if update.message.text else ""
    if isinstance(text, str):
        text = text.strip()
    else:
        text = ""
    
    locale = None
    
    if text and len(text) > len("/start"):
        # Extract locale parameter (if present)
        param = text[len("/start"):].strip()
        
        if param:
            # Validate locale
            if param not in ["en", "ptbr"]:
                error_msg = format_error_message(context, "INVALID_LOCALE")
                logger.warning("[User %s] Invalid locale param: %s", user_id, param)
                await update.message.reply_text(error_msg)
                return
            
            locale = param
    
    # Use current or default locale if not specified
    if locale is None:
        locale = get_language(context)
    else:
        # Set language in user context
        set_language(context, locale)
        logger.info("[User %s] Language set to %s", user_id, locale)

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
                await update.message.reply_text(append_help_hint(format_command_block(prompt_lines), context))
                return
        except NotFoundError:
            # Purchase was deleted or doesn't exist - clear context and continue
            logger.warning("[User %s] Active purchase %s not found, clearing context", user_id, current_purchase_id)
            context.user_data.pop("purchase_id", None)

    # No active purchase - request store name
    context.user_data["waiting_for_store_input"] = True
    logger.info("[User %s] Prompting for store name", user_id)
    
    prompt_msg = format_message(context, "STORE_PROMPT")
    await update.message.reply_text(append_help_hint(prompt_msg, context))


@safe_handler
async def add_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add command - add items to active purchase (Phase 9.10).

    Supports two formats:
    
    Inline:
        /add 19.90,feijao
        /add 19.90,3,feijao
    
    Batch (multiline):
        /add
        19.90,feijao
        20.50,2,file de frango
        5.30,miojo
    
    Requires purchase_id in context (from /start).
    Uses dedicated parser from validators.parse_add_input.
    """
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /add command received")

        # Check if waiting for store input (flow lock - must define store first)
        if context.user_data.get("waiting_for_store_input"):
            logger.info(f"[User {user_id}] /add blocked: waiting for store input")
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        # Check for active purchase
        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        text = (update.message.text or "").strip()
        
        # Reject pipe-based format (old format)
        if "|" in text:
            logger.warning("[User %s] /add pipe format rejected (old format)", user_id)
            error_msg = format_error_message(context, "INVALID_ADD_FORMAT")
            await update.message.reply_text(error_msg)
            return
        
        # Parse input using dedicated parser (validates all items before returning)
        try:
            parsed_items = parse_add_input(text)
        except ValueError as e:
            logger.warning(f"[User {user_id}] /add parse error: {e}")
            error_msg = format_error_message(context, "INVALID_ADD_FORMAT")
            await update.message.reply_text(error_msg)
            return
        
        # Process items (all validated at this point)
        service = context.bot_data["service"]
        
        items_added = 0
        total_physical_units = 0
        
        for parsed_item in parsed_items:
            name = parsed_item["name"]
            qty = parsed_item["quantity"]
            price = parsed_item["price"]
            
            try:
                service.add_item(purchase_id, name, qty, price)
                items_added += 1
                total_physical_units += qty
                logger.info(f"[User {user_id}] Item '{name}' x{qty} added to purchase {purchase_id}")
            except (NotFoundError, ValidationError) as e:
                logger.error(f"[User {user_id}] /add service error: {e}")
                await update.message.reply_text(append_help_hint(f"Error adding item: {e}", context))
                return
        
        # Build success response with locale-aware messages
        purchase = service.get_purchase(purchase_id)
        final_total = purchase["total"]
        final_item_count = purchase["item_count"]
        
        items_added_msg = format_message(context, "ADD_ITEMS_COUNT", count=total_physical_units)
        total_items_msg = format_message(context, "ADD_TOTAL_ITEMS", item_count=final_item_count)
        total_amount_msg = format_message(context, "ADD_TOTAL_AMOUNT", total=format_currency(final_total))
        
        response_lines = [
            items_added_msg,
            "",
            total_items_msg,
            total_amount_msg,
        ]
        
        await update.message.reply_text(append_help_hint("\n".join(response_lines), context))

    except NotFoundError as e:
        logger.warning("[User %s] /add NotFoundError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        await update.message.reply_text(error_msg)
    except ValidationError as e:
        logger.warning("[User %s] /add ValidationError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "INVALID_ADD_FORMAT")
        await update.message.reply_text(error_msg)


@safe_handler
async def view_total_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /total command - show current total and item count."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /total command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        service = context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)

        total = purchase["total"]
        count = purchase["item_count"]

        text = "Total: " + format_currency(total) + "\n\nItems: " + str(count)
        await update.message.reply_text(append_help_hint(text, context))

    except NotFoundError as e:
        logger.warning("[User %s] /total NotFoundError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        await update.message.reply_text(error_msg)


@safe_handler
async def list_items_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list command - show all items in current purchase."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /list command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        service = context.bot_data["service"]
        purchase = service.get_purchase(purchase_id)

        items = purchase.get("items", [])
        if not items:
            await update.message.reply_text(append_help_hint("No items yet. Use /add to add items.", context))
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
        
        await update.message.reply_text(append_help_hint(format_command_block(item_lines), context))

    except NotFoundError as e:
        logger.warning("[User %s] /list NotFoundError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        await update.message.reply_text(error_msg)


@safe_handler
async def delete_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /delete command - remove item by index (1-based)."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /delete command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        text = (update.message.text or "").strip()
        args = text.split()[1:]

        if len(args) < 1:
            logger.warning("[User %s] /delete missing args", user_id)
            error_msg = format_error_message(context, "INVALID_DELETE_INDEX")
            await update.message.reply_text(error_msg)
            return

        try:
            user_index = int(args[0])
        except ValueError:
            logger.warning("[User %s] /delete invalid index: %s", user_id, args)
            error_msg = format_error_message(context, "INVALID_DELETE_INDEX")
            await update.message.reply_text(error_msg)
            return

        if user_index < 1:
            error_msg = format_error_message(context, "INVALID_DELETE_INDEX")
            await update.message.reply_text(error_msg)
            return

        # Convert 1-based (user) to 0-based (internal)
        item_index = user_index - 1

        service = context.bot_data["service"]
        total = service.remove_item(purchase_id, item_index)

        logger.info(f"[User {user_id}] Item {user_index} deleted from purchase {purchase_id}")

        await update.message.reply_text(append_help_hint(f"Item deleted.\n\nNew total: {format_currency(total)}", context))

    except NotFoundError as e:
        logger.warning("[User %s] /delete NotFoundError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        await update.message.reply_text(error_msg)


@safe_handler
async def edit_item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /edit command - modify item quantity or price by index (1-based)."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /edit command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        text = (update.message.text or "").strip()
        args = text.split()[1:]

        if len(args) < 3:
            logger.warning("[User %s] /edit invalid args: %s", user_id, args)
            error_msg = format_error_message(context, "INVALID_EDIT_INPUT")
            await update.message.reply_text(error_msg)
            return

        try:
            user_index = int(args[0])
            quantity = int(args[1])
            unit_price = float(args[2])
        except (ValueError, IndexError):
            logger.warning("[User %s] /edit invalid input: %s", user_id, args)
            error_msg = format_error_message(context, "INVALID_EDIT_INPUT")
            await update.message.reply_text(error_msg)
            return

        if user_index < 1:
            error_msg = format_error_message(context, "INVALID_EDIT_INPUT")
            await update.message.reply_text(error_msg)
            return

        item_index = user_index - 1

        service = context.bot_data["service"]
        total = service.edit_item(purchase_id, item_index, quantity=quantity, unit_price=unit_price)

        logger.info(f"[User {user_id}] Item {user_index} edited in purchase {purchase_id}")

        await update.message.reply_text(append_help_hint(f"Item updated.\n\nNew total: {format_currency(total)}", context))

    except NotFoundError as e:
        logger.warning("[User %s] /edit NotFoundError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        await update.message.reply_text(error_msg)
    except ValidationError as e:
        logger.warning("[User %s] /edit ValidationError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "INVALID_EDIT_INPUT")
        await update.message.reply_text(error_msg)


@safe_handler
async def finish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /finish command - complete purchase and show final summary with store name."""
    try:
        user_id = update.effective_user.id
        logger.info(f"[User {user_id}] /finish command received")

        purchase_id = context.user_data.get("purchase_id")
        if purchase_id is None:
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        service = context.bot_data["service"]
        result = service.finish_purchase(purchase_id)

        total = result["total"]
        count = result["item_count"]
        store_name = result.get("store_name", "Unknown")

        logger.info("[User %s] Purchase %s finished (store=%s, total=%.2f, items=%s)", user_id, purchase_id, store_name, total, count)

        # Build response using localized messages with store name
        title = format_message(context, "FINISH_TITLE")
        store = format_message(context, "FINISH_STORE", store_name=store_name)
        total_items = format_message(context, "FINISH_TOTAL_ITEMS", item_count=count)
        total_amount = format_message(context, "FINISH_TOTAL_AMOUNT", total=format_currency(total))
        next_action = format_message(context, "FINISH_NEW_PURCHASE")

        summary_lines = [
            title,
            "",
            store,
            total_items,
            total_amount,
            "",
            next_action,
        ]
        text = format_command_block(summary_lines)
        await update.message.reply_text(append_help_hint(text, context))

        # Clear purchase_id so next /start creates fresh purchase
        context.user_data.pop("purchase_id", None)

    except NotFoundError as e:
        logger.warning("[User %s] /finish NotFoundError: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
        await update.message.reply_text(error_msg)


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
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        service = context.bot_data["service"]

        try:
            purchase = service.get_active_purchase(purchase_id)
        except NotFoundError:
            logger.warning("[User %s] /resume Purchase %s not found", user_id, purchase_id)
            context.user_data.pop("purchase_id", None)
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
            return

        if purchase is None:
            # Purchase was found but is finished (not active)
            logger.info("[User %s] /resume Purchase %s is finished", user_id, purchase_id)
            context.user_data.pop("purchase_id", None)
            await update.message.reply_text(
                append_help_hint(
                    "This purchase is finished. Use /start to begin a new purchase.", context
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
        await update.message.reply_text(append_help_hint(format_command_block(summary_lines), context))

    except Exception as e:
        logger.exception("[User %s] /continue error: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "GENERIC")
        await update.message.reply_text(error_msg)


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
            error_msg = format_error_message(context, "NO_ACTIVE_PURCHASE")
            await update.message.reply_text(error_msg)
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

        # Clear old purchase and request store name for new one
        context.user_data.pop("purchase_id", None)
        context.user_data["waiting_for_store_input"] = True
        
        logger.info("[User %s] Prompting for store name for new purchase", user_id)
        
        prompt_msg = format_message(context, "STORE_PROMPT")
        await update.message.reply_text(append_help_hint(prompt_msg, context))

    except Exception as e:
        logger.exception("[User %s] /new error: %s", update.effective_user.id, e)
        error_msg = format_error_message(context, "GENERIC")
        await update.message.reply_text(error_msg)


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
    await update.message.reply_text(append_help_hint(text, context))


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
            error_msg = format_error_message(context, "INVALID_LANG")
            await update.message.reply_text(error_msg)
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

            await update.message.reply_text(append_help_hint(msg, context))
        else:
            logger.warning(f"[User {user_id}] Invalid language: {requested_language}")
            error_msg = format_error_message(context, "INVALID_LANG")
            await update.message.reply_text(error_msg)

    except Exception as e:
        logger.exception(f"[User {update.effective_user.id}] /lang error: {e}")
        error_msg = format_error_message(context, "GENERIC")
        await update.message.reply_text(error_msg)


@safe_handler
async def store_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text input for store name when waiting_for_store_input flag is set.

    This handler processes user text input when the bot is waiting for a store name.
    It validates the input (non-empty, trimmed) and creates a purchase with that store name.

    Args:
        update: Telegram update containing message text
        context: Handler context with user_data for state management

    User flow:
        Bot: "What is the store name?"
        User: "Whole Foods"
        Bot: "Store: Whole Foods"
    """
    try:
        user_id = update.effective_user.id

        # Only process if waiting for store input
        if not context.user_data.get("waiting_for_store_input"):
            logger.debug(f"[User {user_id}] Received text but not waiting for store, ignoring")
            return

        logger.info(f"[User {user_id}] Processing store input")

        # Get and validate store name
        store_name = (update.message.text or "").strip() if update.message.text else ""

        if not store_name:
            logger.info(f"[User {user_id}] Empty store name provided")
            error_msg = format_error_message(context, "STORE_EMPTY")
            await update.message.reply_text(error_msg)
            return

        # Create purchase with store name
        try:
            service = context.bot_data["service"]
            locale = get_language(context)
            purchase_id = service.create_purchase(store_name=store_name, locale=locale)

            # Clear waiting flag and store purchase_id
            context.user_data["waiting_for_store_input"] = False
            context.user_data["purchase_id"] = purchase_id

            logger.info(f"[User {user_id}] Purchase created with store '{store_name}', id={purchase_id}")

            # Show success with store name
            success_msg = format_message(context, "STORE_CREATED", store_name=store_name)
            next_steps_lines = [
                success_msg,
                "",
                format_message(context, "STORE_NEXT_STEPS_TITLE"),
                format_message(context, "STORE_ADD_GUIDE"),
                format_message(context, "STORE_LIST_GUIDE"),
                format_message(context, "STORE_FINISH_GUIDE"),
            ]
            await update.message.reply_text(
                append_help_hint(format_command_block(next_steps_lines), context)
            )

        except (NotFoundError, ValidationError) as e:
            logger.error(f"[User {user_id}] Failed to create purchase: {e}")
            error_msg = format_error_message(context, "GENERIC")
            await update.message.reply_text(error_msg)

    except Exception as e:
        logger.exception(f"[User {update.effective_user.id}] Store input error: {e}")
        error_msg = format_error_message(context, "GENERIC")
        await update.message.reply_text(error_msg)


@safe_handler
async def unknown_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown/invalid commands.

    Responds to commands that don't match any registered handler.
    Provides localized error message with /help suggestion.
    No footer is appended for this specific case.

    Args:
        update: Telegram update containing the unknown command
        context: Handler context with user language preference
    """
    title = format_message(context, "UNKNOWN_COMMAND_TITLE")
    message = format_message(context, "UNKNOWN_COMMAND_MESSAGE")

    # Combine title and message without footer (as per bug report)
    response = f"{title}\n\n{message}"

    await update.message.reply_text(response)

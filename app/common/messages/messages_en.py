"""English message strings for CartBot.

All user-facing messages are centralized here for:
1. Consistency across the bot
2. Easy translation to other languages
3. Easier maintenance and updates

Currency (R$) is NOT translated - always displayed as R$ in all languages.
Command names (/start, /add_item, etc.) are also NOT translated.
"""

MESSAGES = {
    # /start command
    "START_NEW": "Shopping list started.",
    "START_NEW_HELP": "Use /add_item to add items | Use /list_items to see all items",
    "START_ACTIVE": "You have an active purchase.",
    "START_ACTIVE_CREATED": "Created: {created_at}",
    "START_ACTIVE_ITEMS": "Items: {item_count}",
    "START_ACTIVE_TOTAL": "Total: {total}",
    "START_ACTIVE_OPTIONS": "Options:",
    "START_ACTIVE_RESUME": "/resume - continue this purchase",
    "START_ACTIVE_NEW": "/new - finish and start a new one",

    # /resume command
    "RESUME_TITLE": "Purchase resumed.",
    "RESUME_CREATED": "Created: {created_at}",
    "RESUME_ITEMS": "Items: {item_count}",
    "RESUME_TOTAL": "Total: {total}",
    "RESUME_ACTIONS": "Actions:",
    "RESUME_ADD_ITEM": "/add_item - add item",
    "RESUME_LIST_ITEMS": "/list_items - show all items",
    "RESUME_FINISH": "/finish - complete purchase",
    "RESUME_NO_PURCHASE": "No active purchase. Use /start to begin.",
    "RESUME_NOT_FOUND": "Purchase not found.",
    "RESUME_FINISHED": "This purchase is finished. Use /start to begin a new purchase.",

    # /new command
    "NEW_PREVIOUS_FINISHED": "Previous purchase finished.",
    "NEW_TOTAL": "Total: {total}",
    "NEW_ITEMS": "Items: {item_count}",
    "NEW_STARTED": "Shopping list started.",
    "NEW_HELP": "Use /add_item to add items | Use /list_items to see all items",
    "NEW_ERROR": "An error occurred. Please try again later.",
    "NEW_NO_PURCHASE": "No active purchase. Use /start to begin.",

    # /add_item command
    "ADD_ITEM_SUCCESS": "Item added.",
    "ADD_ITEM_TOTAL": "Total: {total}",
    "ADD_ITEM_USAGE": "Use:\n/add_item Name | qty | price\n\nExample:\n/add_item Milk | 2 | 5.50",
    "ADD_ITEM_NO_PURCHASE": "No active purchase. Use /start to begin.",
    "ADD_ITEM_INVALID_FORMAT": "Invalid format.",
    "ADD_ITEM_INVALID_FORMAT_HELP": "Use:\n/add_item Name | qty | price\n\nExample:\n/add_item Milk | 2 | 5.50",

    # /add command (Phase 9.12)
    "ADD_ITEMS_COUNT": "{count} items added.",
    "ADD_TOTAL_ITEMS": "Total items: {item_count}",
    "ADD_TOTAL_AMOUNT": "Total amount: {total}",

    # /list_items command
    "LIST_ITEMS_TITLE": "Items",
    "LIST_ITEMS_EMPTY": "No items yet.",
    "LIST_ITEMS_EMPTY_HELP": "Use /add_item to add your first item.",
    "LIST_ITEMS_NO_PURCHASE": "No active purchase. Use /start to begin.",
    "LIST_ITEMS_TOTAL": "Total: {total}",
    "LIST_ITEMS_ACTIONS": "Actions:",
    "LIST_ITEMS_DELETE_ITEM": "/delete_item N - remove item",
    "LIST_ITEMS_EDIT_ITEM": "/edit_item N qty price - modify item",

    # /view_total command
    "VIEW_TOTAL_PREFIX": "Total: {total}",
    "VIEW_TOTAL_ITEMS": "Items: {item_count}",
    "VIEW_TOTAL_NO_PURCHASE": "No active purchase. Use /start to begin.",

    # /delete_item command
    "DELETE_ITEM_SUCCESS": "Item deleted.",
    "DELETE_ITEM_NEW_TOTAL": "New total: {total}",
    "DELETE_ITEM_USAGE": "Usage: /delete_item [index]\nExample: /delete_item 1",
    "DELETE_ITEM_INVALID_INDEX": "Invalid index. Use a number.",
    "DELETE_ITEM_INVALID_INDEX_HELP": "Index must be 1 or greater.",
    "DELETE_ITEM_NO_PURCHASE": "No active purchase. Use /start to begin.",
    "DELETE_ITEM_NOT_FOUND": "Error: {error}",

    # /edit_item command
    "EDIT_ITEM_SUCCESS": "Item updated.",
    "EDIT_ITEM_NEW_TOTAL": "New total: {total}",
    "EDIT_ITEM_USAGE": "Usage: /edit_item [index] [new_quantity] [new_price]\nExample: /edit_item 1 3 2.00",
    "EDIT_ITEM_INVALID_INPUT": "Invalid input. Index and quantity must be whole numbers, price a number.",
    "EDIT_ITEM_INVALID_INDEX": "Index must be 1 or greater.",
    "EDIT_ITEM_NO_PURCHASE": "No active purchase. Use /start to begin.",
    "EDIT_ITEM_NOT_FOUND": "Error: {error}",

    # /finish command
    "FINISH_TITLE": "Purchase finished.",
    "FINISH_TOTAL": "Total: {total}",
    "FINISH_ITEMS": "Items: {item_count}",
    "FINISH_NEW_PURCHASE": "/start - begin a new purchase",
    "FINISH_NO_PURCHASE": "No active purchase. Use /start to begin.",

    # /help command
    "HELP_TITLE": "Available Commands",
    "HELP_SESSION_TITLE": "Session",
    "HELP_START": "/start - start or resume a purchase",
    "HELP_RESUME": "/continue - continue active purchase",
    "HELP_NEW": "/new - finish and start new purchase",
    "HELP_FINISH": "/finish - finish current purchase",
    "HELP_LANG": "/lang [en|ptbr] - change language",
    "HELP_ITEMS_TITLE": "Items",
    "HELP_ADD_ITEM": "/add Name | qty | price",
    "HELP_EDIT_ITEM": "/edit index qty price",
    "HELP_DELETE_ITEM": "/delete index",
    "HELP_OVERVIEW_TITLE": "Overview",
    "HELP_VIEW_TOTAL": "/total - show total",
    "HELP_LIST_ITEMS": "/list - show all items",

    # /lang command
    "LANG_SET_EN": "Language set to English.",
    "LANG_SET_PTBR": "Idioma alterado para Português.",
    "LANG_INVALID": "Invalid language. Use: /lang en or /lang ptbr",
    "LANG_USAGE": "Usage: /lang [en|ptbr]\n\nExample:\n/lang ptbr - switch to Portuguese\n/lang en - switch to English",

    # Store name input
    "STORE_PROMPT": "What is the store name?",
    "STORE_INVALID": "Store name cannot be empty. Please try again.",
    "STORE_CREATED": "Store: {store_name}",

    # General/errors
    "ERROR_GENERIC": "An error occurred. Please try again later.",
    "HELP_HINT": "Need help? Use /help",
}

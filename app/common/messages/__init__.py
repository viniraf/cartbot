"""Language management for CartBot.

Handles:
1. Language selection (default: EN)
2. Message retrieval based on language
3. Language persistence in user context
4. Fallback to English if translation missing
"""

from app.common.messages.messages_en import MESSAGES as MESSAGES_EN
from app.common.messages.messages_ptbr import MESSAGES as MESSAGES_PTBR

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": MESSAGES_EN,
    "ptbr": MESSAGES_PTBR,
}

DEFAULT_LANGUAGE = "en"


def get_message(language: str, key: str, **kwargs) -> str:
    """Get a localized message by key.

    Args:
        language: Language code ('en' or 'ptbr')
        key: Message key (e.g., 'START_NEW')
        **kwargs: Format parameters for the message

    Returns:
        Localized message string. Falls back to English if not found.

    Example:
        msg = get_message('ptbr', 'START_NEW')
        msg = get_message('en', 'ADD_ITEM_TOTAL', total='R$ 25.00')
    """
    # Get message dictionary for language (fallback to EN)
    messages = SUPPORTED_LANGUAGES.get(language, MESSAGES_EN)

    # Get message (fallback to EN if not found in requested language)
    if key not in messages:
        messages = MESSAGES_EN

    message = messages.get(key, f"[Missing: {key}]")

    # Format message with provided kwargs
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError as e:
            return f"[Format error in {key}: missing {e}]"

    return message


def set_language(context, language: str) -> bool:
    """Set the language for a user.

    Args:
        context: Telegram context with user_data
        language: Language code ('en' or 'ptbr')

    Returns:
        True if language was set successfully, False if invalid language.
    """
    if language not in SUPPORTED_LANGUAGES:
        return False

    context.user_data["language"] = language
    return True


def get_language(context) -> str:
    """Get the current language for a user.

    Args:
        context: Telegram context with user_data

    Returns:
        Language code (defaults to 'en' if not set).
    """
    return context.user_data.get("language", DEFAULT_LANGUAGE)


def format_message(context, key: str, **kwargs) -> str:
    """Get a localized message using the user's current language.

    Convenience function that combines get_language() and get_message().

    Args:
        context: Telegram context with user_data
        key: Message key
        **kwargs: Format parameters

    Returns:
        Localized and formatted message string.

    Example:
        msg = format_message(context, 'START_NEW')
        msg = format_message(context, 'ADD_ITEM_TOTAL', total='R$ 25.00')
    """
    language = get_language(context)
    return get_message(language, key, **kwargs)

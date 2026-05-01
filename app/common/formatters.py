"""Reusable formatting helpers for user-facing messages.

This module centralizes all text formatting so that handlers remain
lightweight and consistent. It's intentionally very small and contains
no dependencies beyond the Python stdlib.

Functions:
    format_currency(value: float) -> str
    format_command_block(lines: list[str]) -> str
    append_help_hint(message: str, context: any = None) -> str
"""

from typing import List, Any


def format_currency(value: float, context: Any = None, *, language: str | None = None) -> str:
    """Format a numeric value as currency.

    If a context is provided, the currency symbol is selected based on the
    user's language preference:
      - English = $
      - Portuguese = R$

    If no context or language is provided, the helper defaults to Brazilian
    Real for backward compatibility.

    Args:
        value: Numeric amount (int or float).
        context: Optional handler context used to infer language.
        language: Optional explicit language code.
    Returns:
        A string like "R$ 3.50" or "$ 3.50".
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0

    if language is None and context is not None:
        try:
            from app.common.messages import get_language
            language = get_language(context)
        except Exception:
            language = None

    symbol = "$" if language == "en" else "R$"
    return f"{symbol} {amount:,.2f}"  # comma for thousands if ever needed


def format_command_block(lines: List[str]) -> str:
    """Take a list of command description lines and format them.

    Each entry will appear on its own line. This is just a simple
    helper to keep handlers free of manual joins.
    """
    return "\n".join(lines)


def append_help_hint(message: str, context: Any = None) -> str:
    """Append a standard help hint footer to a message.

    The footer is separated by a horizontal rule and instructs the user
    how to access /help. Uses localized text when context is provided.

    Args:
        message: The original user message.
        context: Handler context for localization (optional for backward compatibility).
    Returns:
        The message with footer appended, ensuring there are blank lines
        before the hint.
    """
    if context is not None:
        # Import here to avoid circular imports
        from app.common.messages import format_message
        hint = f"--\n{format_message(context, 'ERROR_HELP_FOOTER')}"
    else:
        # Fallback for backward compatibility (should not be used in production)
        hint = "--\nNeed help? Use /help"
    
    # ensure exactly one blank line before the hint
    if not message.endswith("\n"):
        message = message + "\n"
    return f"{message}\n{hint}"
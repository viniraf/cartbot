"""Domain-level custom exceptions.

Exceptions raised by domain logic for invariant violations and not-found conditions.
Services and handlers can catch these to provide appropriate user feedback.
"""


class DomainError(Exception):
    """Base exception for all domain-level errors.

    Signals a violation of business logic or domain invariants.
    """

    pass


class ValidationError(DomainError):
    """Raised when domain invariants are violated.

    Examples:
    - Quantity must be > 0
    - Unit price must be > 0
    - Cannot remove non-existent item
    """

    pass


class NotFoundError(DomainError):
    """Raised when an expected entity is not found.

    Examples:
    - Purchase with given ID doesn't exist
    - Item at given index not found in purchase
    """

    pass

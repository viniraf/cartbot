"""Base repository interface.

Defines the contract that all repositories must follow.
No implementation details here - just abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseRepository(ABC):
    """Abstract base class for all repositories.

    Repositories are responsible for persisting and retrieving domain entities.
    """

    @abstractmethod
    def save(self, entity: Any) -> None:
        """Save an entity (create or update).

        Args:
            entity: The entity to save.

        Raises:
            Exception: Implementation-specific exceptions for storage errors.
        """
        pass

    @abstractmethod
    def get_by_id(self, entity_id: Any) -> Optional[Any]:
        """Retrieve an entity by ID.

        Args:
            entity_id: The ID of the entity to retrieve.

        Returns:
            The entity if found, None otherwise.
        """
        pass

    @abstractmethod
    def delete(self, entity_id: Any) -> None:
        """Delete an entity by ID.

        Args:
            entity_id: The ID of the entity to delete.

        Raises:
            Exception: Implementation-specific exceptions for storage errors.
        """
        pass

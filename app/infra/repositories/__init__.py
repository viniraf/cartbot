"""Repository module - contains data persistence abstractions."""

from .base import BaseRepository
from .purchase_repository import SQLitePurchaseRepository

__all__ = ["BaseRepository", "SQLitePurchaseRepository"]

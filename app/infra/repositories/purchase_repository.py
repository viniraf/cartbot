"""SQLite repository for Purchase entities.

Implements BaseRepository interface for persisting and retrieving purchases
and their associated items from SQLite.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from .base import BaseRepository
from app.infra.database import get_db_connection
from app.infra.config import Config

logger = logging.getLogger(__name__)


class SQLitePurchaseRepository(BaseRepository):
    """SQLite implementation of purchase persistence.

    Handles all database operations for purchases and purchase_items.
    Works with dict-based purchase objects (until domain layer is defined).
    """

    def __init__(self, db_path: str = None):
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database. Defaults to Config.DATABASE_PATH.
        """
        self.db_path = db_path or Config.DATABASE_PATH

    def save(self, entity: Any) -> None:
        """Save a purchase (create or update) and its items.

        Args:
            entity: Purchase dict with structure:
                    {
                        'id': int or None,
                        'created_at': ISO timestamp string,
                        'finished_at': ISO timestamp string or None,
                        'items': [
                            {'name': str, 'quantity': int, 'unit_price': float},
                            ...
                        ]
                    }

        If purchase.id is None, inserts new row and sets ID on entity.
        If purchase.id exists, updates the purchase and replaces all items.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()

            if entity.get('id') is None:
                # Insert new purchase
                cursor.execute(
                    """
                    INSERT INTO purchases (created_at, finished_at)
                    VALUES (?, ?)
                    """,
                    (
                        entity.get('created_at') or datetime.now().isoformat(),
                        entity.get('finished_at'),
                    ),
                )
                entity['id'] = cursor.lastrowid
                logger.info(f"Created purchase {entity['id']}")
            else:
                # Update existing purchase
                cursor.execute(
                    """
                    UPDATE purchases
                    SET finished_at = ?
                    WHERE id = ?
                    """,
                    (entity.get('finished_at'), entity['id']),
                )
                logger.info(f"Updated purchase {entity['id']}")

            # Delete existing items for this purchase (if any)
            cursor.execute("DELETE FROM purchase_items WHERE purchase_id = ?", (entity['id'],))

            # Insert new items
            items = entity.get('items', [])
            for item in items:
                cursor.execute(
                    """
                    INSERT INTO purchase_items (purchase_id, item_name, quantity, unit_price, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        entity['id'],
                        item['name'],
                        item['quantity'],
                        item['unit_price'],
                        item.get('created_at') or datetime.now().isoformat(),
                    ),
                )
            logger.info(f"Saved {len(items)} items for purchase {entity['id']}")

            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving purchase: {e}")
            raise
        finally:
            conn.close()

    def get_by_id(self, entity_id: Any) -> Optional[Any]:
        """Retrieve a purchase by ID with all its items.

        Args:
            entity_id: Purchase ID to retrieve.

        Returns:
            Purchase dict with items, or None if not found.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()

            # Get purchase
            cursor.execute(
                """
                SELECT id, created_at, finished_at
                FROM purchases
                WHERE id = ?
                """,
                (entity_id,),
            )
            row = cursor.fetchone()
            if not row:
                logger.debug(f"Purchase {entity_id} not found")
                return None

            purchase = {
                'id': row[0],
                'created_at': row[1],
                'finished_at': row[2],
                'items': [],
            }

            # Get items
            cursor.execute(
                """
                SELECT item_name, quantity, unit_price, created_at
                FROM purchase_items
                WHERE purchase_id = ?
                ORDER BY created_at ASC
                """,
                (entity_id,),
            )
            items = cursor.fetchall()
            for item_row in items:
                purchase['items'].append(
                    {
                        'name': item_row[0],
                        'quantity': item_row[1],
                        'unit_price': item_row[2],
                        'created_at': item_row[3],
                    }
                )

            logger.debug(f"Retrieved purchase {entity_id} with {len(items)} items")
            return purchase

        except Exception as e:
            logger.error(f"Error retrieving purchase {entity_id}: {e}")
            raise
        finally:
            conn.close()

    def delete(self, entity_id: Any) -> None:
        """Delete a purchase and all its items.

        Args:
            entity_id: Purchase ID to delete.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()

            # Delete items first (foreign key constraint)
            cursor.execute("DELETE FROM purchase_items WHERE purchase_id = ?", (entity_id,))
            items_deleted = cursor.rowcount

            # Delete purchase
            cursor.execute("DELETE FROM purchases WHERE id = ?", (entity_id,))
            purchase_deleted = cursor.rowcount

            if purchase_deleted == 0:
                logger.warning(f"Purchase {entity_id} not found for deletion")
            else:
                logger.info(f"Deleted purchase {entity_id} and {items_deleted} items")

            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting purchase {entity_id}: {e}")
            raise
        finally:
            conn.close()

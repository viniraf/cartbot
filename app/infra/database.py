"""Database initialization and connection management."""

import sqlite3
import logging
from pathlib import Path
from app.infra.config import Config

logger = logging.getLogger(__name__)


def init_db(db_path=None):
    """
    Initialize the SQLite database with required tables.
    
    Creates the database file and tables if they don't exist.
    This function is idempotent and safe to call multiple times.
    
    Args:
        db_path: Path to the SQLite database file.
                 Defaults to Config.DATABASE_PATH.
    
    Returns:
        None
    
    Raises:
        sqlite3.Error: If database operations fail.
    """
    if db_path is None:
        db_path = Config.DATABASE_PATH
    
    # Ensure db_path is a string
    db_path = str(db_path)
    
    # Create data directory if it doesn't exist
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create purchases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP NULL,
                store_name TEXT NOT NULL DEFAULT 'Unknown'
            )
        """)

        # Migration: add store_name to existing databases
        # SQLite doesn't support adding constraints to existing columns, so we ensure
        # the column exists as NOT NULL with a default/backfill value.
        cursor.execute("PRAGMA table_info(purchases)")
        purchases_columns = {row[1]: row for row in cursor.fetchall()}
        if "store_name" not in purchases_columns:
            cursor.execute(
                """
                ALTER TABLE purchases
                ADD COLUMN store_name TEXT NOT NULL DEFAULT 'Unknown'
                """
            )
        else:
            # If the column exists, we still backfill any unexpected NULLs.
            cursor.execute("UPDATE purchases SET store_name = 'Unknown' WHERE store_name IS NULL")
        
        # Create purchase_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        logger.info(f"Database initialized at {db_path}")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()


def get_db_connection(db_path=None):
    """
    Get a connection to the SQLite database.
    
    Args:
        db_path: Path to the SQLite database file.
                 Defaults to Config.DATABASE_PATH.
    
    Returns:
        sqlite3.Connection: Open database connection.
    
    Raises:
        sqlite3.Error: If connection fails.
    """
    if db_path is None:
        db_path = Config.DATABASE_PATH
    
    db_path = str(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        # Enable row factory for dict-like access
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

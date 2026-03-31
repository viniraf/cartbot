"""Unit tests for database initialization using pytest."""

import sqlite3
import os
import tempfile
from pathlib import Path
import pytest
from app.infra.database import init_db, get_db_connection


class TestDatabaseInitialization:
    """Test database initialization and connection."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            yield db_path
            # Cleanup
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_init_db_creates_database_file(self, temp_db_path):
        """init_db() should create the database file if it doesn't exist."""
        assert not os.path.exists(temp_db_path)
        init_db(db_path=temp_db_path)
        assert os.path.exists(temp_db_path)

    def test_init_db_creates_data_directory(self):
        """init_db() should create data directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "subdir", "test.db")
            assert not os.path.exists(os.path.dirname(db_path))
            init_db(db_path=db_path)
            assert os.path.exists(os.path.dirname(db_path))

    def test_init_db_creates_purchases_table(self, temp_db_path):
        """init_db() should create purchases table."""
        init_db(db_path=temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='purchases'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None

    def test_init_db_creates_purchase_items_table(self, temp_db_path):
        """init_db() should create purchase_items table."""
        init_db(db_path=temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='purchase_items'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None

    def test_init_db_purchases_table_has_correct_columns(self, temp_db_path):
        """purchases table should have required columns."""
        init_db(db_path=temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(purchases)")
        columns = {row[1]: row for row in cursor.fetchall()}
        conn.close()
        
        assert "id" in columns
        assert "created_at" in columns
        assert "finished_at" in columns
        assert "store_name" in columns

    def test_init_db_purchase_items_table_has_correct_columns(self, temp_db_path):
        """purchase_items table should have required columns."""
        init_db(db_path=temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(purchase_items)")
        columns = {row[1]: row for row in cursor.fetchall()}
        conn.close()
        
        assert "id" in columns
        assert "purchase_id" in columns
        assert "item_name" in columns
        assert "quantity" in columns
        assert "unit_price" in columns
        assert "created_at" in columns

    def test_init_db_is_idempotent(self, temp_db_path):
        """init_db() should be safe to call multiple times."""
        init_db(db_path=temp_db_path)
        file_size_1 = os.path.getsize(temp_db_path)
        
        # Call again
        init_db(db_path=temp_db_path)
        file_size_2 = os.path.getsize(temp_db_path)
        
        # Sizes might differ slightly but should be close (not exponential growth)
        assert abs(file_size_1 - file_size_2) < 1000

    def test_init_db_foreign_key_constraint(self, temp_db_path):
        """Foreign key constraint should be enforced in get_db_connection()."""
        init_db(db_path=temp_db_path)
        conn = get_db_connection(db_path=temp_db_path)
        
        try:
            cursor = conn.cursor()
            # Try to insert item with non-existent purchase_id
            cursor.execute(
                "INSERT INTO purchase_items (purchase_id, item_name, quantity, unit_price) "
                "VALUES (999, 'test', 1, 1.0)"
            )
            conn.commit()
            # Should fail due to foreign key constraint
            pytest.fail("Foreign key constraint not enforced")
        except sqlite3.IntegrityError:
            # Expected: foreign key constraint violated
            pass
        finally:
            conn.close()

    def test_get_db_connection_returns_connection(self, temp_db_path):
        """get_db_connection() should return a valid connection."""
        init_db(db_path=temp_db_path)
        conn = get_db_connection(db_path=temp_db_path)
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_db_connection_can_execute_queries(self, temp_db_path):
        """Connection should be able to execute queries."""
        init_db(db_path=temp_db_path)
        conn = get_db_connection(db_path=temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM purchases")
        result = cursor.fetchone()
        conn.close()
        assert result is not None
        assert result[0] == 0

    def test_get_db_connection_enables_foreign_keys(self, temp_db_path):
        """Connections should have foreign keys enabled."""
        init_db(db_path=temp_db_path)
        conn = get_db_connection(db_path=temp_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        conn.close()
        assert result[0] == 1  # 1 means foreign keys are ON

    def test_init_db_with_path_object(self, temp_db_path):
        """init_db() should handle Path objects."""
        path_obj = Path(temp_db_path)
        init_db(db_path=path_obj)
        assert os.path.exists(temp_db_path)

    def test_get_db_connection_with_path_object(self, temp_db_path):
        """get_db_connection() should handle Path objects."""
        init_db(db_path=temp_db_path)
        path_obj = Path(temp_db_path)
        conn = get_db_connection(db_path=path_obj)
        assert conn is not None
        conn.close()

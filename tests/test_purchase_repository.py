"""Tests for SQLitePurchaseRepository."""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from app.infra.repositories import SQLitePurchaseRepository
from app.infra.database import init_db


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cartbot.db")
        init_db(db_path)
        yield db_path


@pytest.fixture
def repo(temp_db):
    """Create a repository instance with temp database."""
    return SQLitePurchaseRepository(db_path=temp_db)


class TestSQLitePurchaseRepositorySave:
    """Test save() method."""

    def test_save_new_purchase(self, repo):
        """Should create a new purchase and assign ID."""
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [],
        }

        repo.save(purchase)

        assert purchase['id'] is not None
        assert isinstance(purchase['id'], int)
        assert purchase['id'] > 0

    def test_save_purchase_with_items(self, repo):
        """Should save purchase with items."""
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [
                {'name': 'Milk', 'quantity': 2, 'unit_price': 1.50, 'created_at': datetime.now().isoformat()},
                {'name': 'Bread', 'quantity': 1, 'unit_price': 2.00, 'created_at': datetime.now().isoformat()},
            ],
        }

        repo.save(purchase)

        assert purchase['id'] is not None
        assert len(purchase['items']) == 2

    def test_save_updates_existing_purchase(self, repo):
        """Should update an existing purchase."""
        # Create initial purchase
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [{'name': 'Milk', 'quantity': 1, 'unit_price': 1.50, 'created_at': datetime.now().isoformat()}],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        # Update with different finished_at
        purchase['finished_at'] = datetime.now().isoformat()
        purchase['items'] = [
            {'name': 'Bread', 'quantity': 2, 'unit_price': 2.00, 'created_at': datetime.now().isoformat()},
        ]
        repo.save(purchase)

        # Verify update
        retrieved = repo.get_by_id(purchase_id)
        assert retrieved['finished_at'] is not None
        assert len(retrieved['items']) == 1
        assert retrieved['items'][0]['name'] == 'Bread'

    def test_save_replaces_items_on_update(self, repo):
        """Should replace all items when updating purchase."""
        # Create with 2 items
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [
                {'name': 'Item1', 'quantity': 1, 'unit_price': 1.0, 'created_at': datetime.now().isoformat()},
                {'name': 'Item2', 'quantity': 1, 'unit_price': 2.0, 'created_at': datetime.now().isoformat()},
            ],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        # Update with 1 item
        purchase['items'] = [
            {'name': 'Item3', 'quantity': 3, 'unit_price': 3.0, 'created_at': datetime.now().isoformat()},
        ]
        repo.save(purchase)

        # Verify replacement
        retrieved = repo.get_by_id(purchase_id)
        assert len(retrieved['items']) == 1
        assert retrieved['items'][0]['name'] == 'Item3'


class TestSQLitePurchaseRepositoryGetById:
    """Test get_by_id() method."""

    def test_get_by_id_returns_purchase(self, repo):
        """Should retrieve a saved purchase."""
        # Save purchase
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [{'name': 'Test Item', 'quantity': 5, 'unit_price': 9.99, 'created_at': datetime.now().isoformat()}],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        # Retrieve
        retrieved = repo.get_by_id(purchase_id)

        assert retrieved is not None
        assert retrieved['id'] == purchase_id
        assert len(retrieved['items']) == 1
        assert retrieved['items'][0]['name'] == 'Test Item'
        assert retrieved['items'][0]['quantity'] == 5
        assert retrieved['items'][0]['unit_price'] == 9.99

    def test_get_by_id_returns_none_for_missing_purchase(self, repo):
        """Should return None if purchase not found."""
        result = repo.get_by_id(999999)
        assert result is None

    def test_get_by_id_returns_empty_items_for_purchase_without_items(self, repo):
        """Should return purchase with empty items list."""
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        retrieved = repo.get_by_id(purchase_id)

        assert retrieved is not None
        assert retrieved['items'] == []

    def test_get_by_id_preserves_item_order(self, repo):
        """Should retrieve items in creation order."""
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [
                {'name': 'First', 'quantity': 1, 'unit_price': 1.0, 'created_at': datetime.now().isoformat()},
                {'name': 'Second', 'quantity': 2, 'unit_price': 2.0, 'created_at': datetime.now().isoformat()},
                {'name': 'Third', 'quantity': 3, 'unit_price': 3.0, 'created_at': datetime.now().isoformat()},
            ],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        retrieved = repo.get_by_id(purchase_id)

        names = [item['name'] for item in retrieved['items']]
        assert names == ['First', 'Second', 'Third']


class TestSQLitePurchaseRepositoryDelete:
    """Test delete() method."""

    def test_delete_removes_purchase(self, repo):
        """Should delete a purchase."""
        # Create and save
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        # Delete
        repo.delete(purchase_id)

        # Verify gone
        retrieved = repo.get_by_id(purchase_id)
        assert retrieved is None

    def test_delete_removes_items_with_purchase(self, repo):
        """Should delete items when deleting purchase."""
        # Create with items
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [
                {'name': 'Item1', 'quantity': 1, 'unit_price': 1.0, 'created_at': datetime.now().isoformat()},
                {'name': 'Item2', 'quantity': 2, 'unit_price': 2.0, 'created_at': datetime.now().isoformat()},
            ],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        # Delete
        repo.delete(purchase_id)

        # Verify items are gone too
        retrieved = repo.get_by_id(purchase_id)
        assert retrieved is None

    def test_delete_non_existent_purchase_does_not_error(self, repo):
        """Should handle deletion of non-existent purchase gracefully."""
        # Should not raise
        repo.delete(999999)

    def test_delete_only_affects_target_purchase(self, repo):
        """Should only delete specified purchase, not others."""
        # Create two purchases
        purchase1 = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [{'name': 'Item1', 'quantity': 1, 'unit_price': 1.0, 'created_at': datetime.now().isoformat()}],
        }
        purchase2 = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [{'name': 'Item2', 'quantity': 2, 'unit_price': 2.0, 'created_at': datetime.now().isoformat()}],
        }
        repo.save(purchase1)
        repo.save(purchase2)

        # Delete first
        repo.delete(purchase1['id'])

        # Verify second still exists
        assert repo.get_by_id(purchase1['id']) is None
        assert repo.get_by_id(purchase2['id']) is not None


class TestSQLitePurchaseRepositoryIntegration:
    """Integration tests for full CRUD cycle."""

    def test_full_lifecycle(self, repo):
        """Test complete create-read-update-delete lifecycle."""
        # Create
        purchase = {
            'id': None,
            'created_at': datetime.now().isoformat(),
            'finished_at': None,
            'items': [
                {'name': 'Milk', 'quantity': 1, 'unit_price': 1.50, 'created_at': datetime.now().isoformat()},
            ],
        }
        repo.save(purchase)
        purchase_id = purchase['id']

        # Read
        retrieved = repo.get_by_id(purchase_id)
        assert retrieved['items'][0]['name'] == 'Milk'

        # Update
        purchase['items'].append({'name': 'Bread', 'quantity': 2, 'unit_price': 2.00, 'created_at': datetime.now().isoformat()})
        purchase['finished_at'] = datetime.now().isoformat()
        repo.save(purchase)

        # Read again
        retrieved = repo.get_by_id(purchase_id)
        assert len(retrieved['items']) == 2
        assert retrieved['finished_at'] is not None

        # Delete
        repo.delete(purchase_id)
        assert repo.get_by_id(purchase_id) is None

    def test_multiple_purchases_independent(self, repo):
        """Should handle multiple independent purchases."""
        purchases = []
        for i in range(3):
            p = {
                'id': None,
                'created_at': datetime.now().isoformat(),
                'finished_at': None,
                'items': [
                    {'name': f'Item{i}', 'quantity': i + 1, 'unit_price': float(i + 1), 'created_at': datetime.now().isoformat()},
                ],
            }
            repo.save(p)
            purchases.append(p)

        # Verify all are independent
        for i, p in enumerate(purchases):
            retrieved = repo.get_by_id(p['id'])
            assert retrieved['items'][0]['name'] == f'Item{i}'
            assert retrieved['items'][0]['quantity'] == i + 1

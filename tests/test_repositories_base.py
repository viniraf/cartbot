"""Tests for BaseRepository abstract base class."""

import pytest
from abc import ABC
from app.infra.repositories.base import BaseRepository


class TestBaseRepository:
    """Test BaseRepository contract and abstract nature."""

    def test_base_repository_is_abstract(self):
        """BaseRepository should be an abstract class."""
        assert issubclass(BaseRepository, ABC)

    def test_base_repository_cannot_be_instantiated(self):
        """Should raise TypeError when trying to instantiate BaseRepository directly."""
        with pytest.raises(TypeError, match="abstract"):
            BaseRepository()

    def test_base_repository_requires_save_implementation(self):
        """Subclass must implement save() method."""
        with pytest.raises(TypeError, match="abstract"):

            class IncompleteRepository(BaseRepository):
                def get_by_id(self, entity_id):
                    return None

                def delete(self, entity_id):
                    pass

            IncompleteRepository()

    def test_base_repository_requires_get_by_id_implementation(self):
        """Subclass must implement get_by_id() method."""
        with pytest.raises(TypeError, match="abstract"):

            class IncompleteRepository(BaseRepository):
                def save(self, entity):
                    pass

                def delete(self, entity_id):
                    pass

            IncompleteRepository()

    def test_base_repository_requires_delete_implementation(self):
        """Subclass must implement delete() method."""
        with pytest.raises(TypeError, match="abstract"):

            class IncompleteRepository(BaseRepository):
                def save(self, entity):
                    pass

                def get_by_id(self, entity_id):
                    return None

            IncompleteRepository()

    def test_concrete_implementation_can_be_instantiated(self):
        """Concrete subclass implementing all methods can be instantiated."""

        class ConcreteRepository(BaseRepository):
            def save(self, entity):
                pass

            def get_by_id(self, entity_id):
                return None

            def delete(self, entity_id):
                pass

        repo = ConcreteRepository()
        assert isinstance(repo, BaseRepository)
        assert callable(repo.save)
        assert callable(repo.get_by_id)
        assert callable(repo.delete)

    def test_concrete_implementation_methods_are_callable(self):
        """All repository methods should be callable on concrete implementation."""

        class ConcreteRepository(BaseRepository):
            def save(self, entity):
                return "saved"

            def get_by_id(self, entity_id):
                return {"id": entity_id}

            def delete(self, entity_id):
                return True

        repo = ConcreteRepository()

        # Methods should execute without error
        result_save = repo.save({"name": "test"})
        assert result_save == "saved"

        result_get = repo.get_by_id(123)
        assert result_get == {"id": 123}

        result_delete = repo.delete(123)
        assert result_delete is True

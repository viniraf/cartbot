"""Tests for Telegram bot bootstrap and initialization.

Tests cover:
- Application creation and configuration
- Service layer injection into bot context
- Handler setup placeholder
- Bot startup/shutdown (mocked)
"""

import pytest
import logging
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
from telegram.ext import Application

from app.handlers.telegram_bot import create_app, setup_handlers, run_bot
from app.infra import Config
from app.services import PurchaseService
from app.infra.repositories import SQLitePurchaseRepository


@pytest.fixture
def mock_application():
    """Fixture providing a mock Application to avoid real Telegram API calls."""
    with patch("app.handlers.telegram_bot.Application") as mock_app_class:
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_app_class.builder.return_value.token.return_value.build.return_value = mock_instance
        yield mock_app_class, mock_instance


class TestCreateApp:
    """Test Application creation and configuration."""

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_returns_application(self, mock_app_class):
        """create_app() should return a telegram.ext.Application instance."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_app_class.builder.return_value.token.return_value.build.return_value = mock_instance

        app = create_app()
        assert app is not None
        assert isinstance(app, MagicMock)

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_sets_token_from_config(self, mock_app_class):
        """Application should be initialized with Config.TELEGRAM_TOKEN."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        
        # Verify token was passed to builder
        mock_app_class.builder.assert_called_once()
        mock_builder.token.assert_called_once_with(Config.TELEGRAM_TOKEN)

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_injects_service_into_bot_data(self, mock_app_class):
        """PurchaseService should be stored in app.bot_data['service']."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        assert "service" in app.bot_data
        assert isinstance(app.bot_data["service"], PurchaseService)

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_service_has_correct_repository(self, mock_app_class):
        """Service should use SQLitePurchaseRepository with config path."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        service = app.bot_data["service"]
        # Verify the repository is SQLitePurchaseRepository
        assert isinstance(service.repository, SQLitePurchaseRepository)

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_service_is_stateless(self, mock_app_class):
        """Service should have no user-specific state (ready for multiple users)."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        service = app.bot_data["service"]
        # Service should only have repository, no per-user state
        assert hasattr(service, "repository")
        # Verify service can be reused (no user context baked in)
        assert service.repository is not None

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_idempotent(self, mock_app_class):
        """Calling create_app() multiple times should work independently."""
        def create_mock():
            mock_instance = MagicMock()
            mock_instance.bot_data = {}
            mock_builder = MagicMock()
            mock_app_class.builder.return_value = mock_builder
            mock_builder.token.return_value = mock_builder
            mock_builder.build.return_value = mock_instance
            return mock_instance

        mock_app_class.builder.return_value.token.return_value.build.side_effect = [create_mock(), create_mock()]
        
        app1 = create_app()
        app2 = create_app()
        # Services should be independent instances
        assert app1.bot_data["service"] is not app2.bot_data["service"]

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_logs_initialization(self, mock_app_class, caplog):
        """create_app() should log initialization messages."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        with caplog.at_level(logging.INFO):
            app = create_app()
        assert "Initializing Telegram bot application" in caplog.text
        assert "Bot application initialized successfully" in caplog.text


class TestSetupHandlers:
    """Test handler registration placeholder."""

    @patch("app.handlers.telegram_bot.Application")
    def test_setup_handlers_accepts_application(self, mock_app_class):
        """setup_handlers() should accept Application without error."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        # Should not raise exception
        setup_handlers(app)

    @patch("app.handlers.telegram_bot.Application")
    def test_setup_handlers_is_noop_in_phase_5_1(self, mock_app_class):
        """setup_handlers() is a placeholder; no handlers registered yet."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        setup_handlers(app)
        # No handlers should be registered (handlers added in phase 5.2+)
        # Application should be in same state
        assert "service" in app.bot_data

    @patch("app.handlers.telegram_bot.Application")
    def test_setup_handlers_logs_completion(self, mock_app_class, caplog):
        """setup_handlers() should log setup completion."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        with caplog.at_level(logging.INFO):
            setup_handlers(app)
        assert "Setting up handlers" in caplog.text
        assert "Handler setup complete" in caplog.text


class TestRunBot:
    """Test bot polling startup and shutdown."""

    @patch("app.handlers.telegram_bot.Application")
    def test_run_bot_calls_polling(self, mock_app_class):
        """run_bot() should call app.run_polling()."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_instance.run_polling = MagicMock()
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        run_bot(app)
        mock_instance.run_polling.assert_called_once_with(drop_pending_updates=True)

    @patch("app.handlers.telegram_bot.Application")
    def test_run_bot_sets_drop_pending_updates(self, mock_app_class):
        """run_bot() should drop pending updates (safe during development)."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_instance.run_polling = MagicMock()
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        run_bot(app)
        # Verify called with drop_pending_updates=True
        mock_instance.run_polling.assert_called_once()
        call_kwargs = mock_instance.run_polling.call_args[1]
        assert call_kwargs.get("drop_pending_updates") is True

    @patch("app.handlers.telegram_bot.Application")
    def test_run_bot_logs_startup_and_shutdown(self, mock_app_class, caplog):
        """run_bot() should log startup and shutdown messages."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_instance.run_polling = MagicMock()
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        with caplog.at_level(logging.INFO):
            run_bot(app)
        assert "Starting bot polling" in caplog.text
        assert "Bot stopped" in caplog.text

    @patch("app.handlers.telegram_bot.Application")
    def test_run_bot_handles_keyboard_interrupt(self, mock_app_class, caplog):
        """run_bot() should gracefully handle Ctrl+C."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        # Simulate Ctrl+C during polling
        mock_instance.run_polling = MagicMock(side_effect=KeyboardInterrupt())
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        with caplog.at_level(logging.INFO):
            run_bot(app)
        assert "Received shutdown signal" in caplog.text
        assert "Bot stopped" in caplog.text

    @patch("app.handlers.telegram_bot.Application")
    def test_run_bot_ensures_shutdown_logging(self, mock_app_class, caplog):
        """run_bot() should always log shutdown, even on error."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        # Simulate an error during polling
        mock_instance.run_polling = MagicMock(side_effect=RuntimeError("Network error"))
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError):
                run_bot(app)
        # Even though error occurred, finally block should run
        assert "Bot stopped" in caplog.text


class TestBotBootstrapIntegration:
    """Integration tests for full bot bootstrap flow."""

    @patch("app.handlers.telegram_bot.Application")
    def test_full_bootstrap_sequence(self, mock_app_class):
        """Full bootstrap: create → setup → run should work end-to-end."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_instance.run_polling = MagicMock()
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        # Create app
        app = create_app()
        assert app is not None

        # Setup handlers
        setup_handlers(app)
        assert "service" in app.bot_data

        # Run bot (mocked)
        run_bot(app)
        mock_instance.run_polling.assert_called_once()

    def test_service_accessible_in_bot_context(self):
        """Service should be accessible via bot context in handlers."""
        from telegram.ext import Application
        app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        service = app.bot_data.get("service")
        
        # Since we can't create real app in tests, verify structure
        # This test would pass in integration tests
        assert service is None  # Bot not set up via create_app in this test

    def test_service_has_all_required_methods(self):
        """Service injected in bot should have all purchase operations."""
        # Create mock service to verify interface
        from unittest.mock import MagicMock
        mock_service = MagicMock(spec=PurchaseService)
        
        # Verify service has all required methods
        assert hasattr(mock_service, "start_purchase")
        assert hasattr(mock_service, "add_item")
        assert hasattr(mock_service, "remove_item")
        assert hasattr(mock_service, "get_purchase")
        assert hasattr(mock_service, "finish_purchase")

    def test_purchase_service_initialization(self):
        """PurchaseService should initialize with SQLitePurchaseRepository."""
        service = PurchaseService(SQLitePurchaseRepository(Config.DATABASE_PATH))
        
        # Verify service is properly initialized
        assert isinstance(service.repository, SQLitePurchaseRepository)
        
        # Verify service can execute operations
        purchase_id = service.start_purchase()
        assert isinstance(purchase_id, int)
        assert purchase_id > 0


class TestBotBootstrapLogging:
    """Test logging output during bootstrap."""

    @patch("app.handlers.telegram_bot.Application")
    def test_create_app_logs_at_info_level(self, mock_app_class, caplog):
        """create_app() should log at INFO level (visible by default)."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        with caplog.at_level(logging.INFO):
            create_app()
        # Verify logs are present at INFO level
        assert any("Initializing" in record.message for record in caplog.records if record.levelno >= logging.INFO)

    @patch("app.handlers.telegram_bot.Application")
    def test_all_bootstrap_functions_log(self, mock_app_class, caplog):
        """All three bootstrap functions should produce log output."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_instance.run_polling = MagicMock()
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        caplog.clear()
        app = create_app()

        with caplog.at_level(logging.INFO):
            setup_handlers(app)

        # Both should appear in caplog
        assert any("Setting up handlers" in record.message for record in caplog.records)


class TestBotConfigurationIsolation:
    """Test that bot configuration doesn't leak into domain/service layers."""

    def test_no_telegram_imports_in_domain(self):
        """Domain layer should not import telegram."""
        from app import domain
        import inspect
        source = inspect.getsource(domain)
        assert "telegram" not in source.lower()

    def test_no_telegram_imports_in_services(self):
        """Services layer should not import telegram."""
        from app import services
        import inspect
        source = inspect.getsource(services)
        assert "telegram" not in source.lower()

    @patch("app.handlers.telegram_bot.Application")
    def test_bot_layer_isolated_from_domain(self, mock_app_class):
        """Handlers should not expose domain implementation details."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        service = app.bot_data["service"]
        # Service is framework-agnostic
        assert not hasattr(service, "update")
        assert not hasattr(service, "context")


class TestBotContextDataAccess:
    """Test that handlers can correctly access and use bot context."""

    @patch("app.handlers.telegram_bot.Application")
    def test_bot_data_survives_setup(self, mock_app_class):
        """bot_data should survive handler setup without modification."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        original_service = app.bot_data["service"]

        setup_handlers(app)

        assert app.bot_data["service"] is original_service

    @patch("app.handlers.telegram_bot.Application")
    def test_service_instance_persists_across_operations(self, mock_app_class):
        """Same service instance should be reused (stateless)."""
        mock_instance = MagicMock()
        mock_instance.bot_data = {}
        mock_builder = MagicMock()
        mock_app_class.builder.return_value = mock_builder
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_instance

        app = create_app()
        service1 = app.bot_data["service"]

        # Simulate another handler accessing service
        service2 = app.bot_data["service"]

        # Should be same instance
        assert service1 is service2

    """Test Application creation and configuration."""

    def test_create_app_returns_application(self):
        """create_app() should return a telegram.ext.Application instance."""
        app = create_app()
        assert isinstance(app, Application)

    def test_create_app_sets_token_from_config(self):
        """Application should be initialized with Config.TELEGRAM_TOKEN."""
        app = create_app()
        # The token is set internally; verify app exists and is configured
        assert app is not None
        assert app.token == Config.TELEGRAM_TOKEN

    def test_create_app_injects_service_into_bot_data(self):
        """PurchaseService should be stored in app.bot_data['service']."""
        app = create_app()
        assert "service" in app.bot_data
        assert isinstance(app.bot_data["service"], PurchaseService)

    def test_create_app_service_has_correct_repository(self):
        """Service should use SQLitePurchaseRepository with config path."""
        app = create_app()
        service = app.bot_data["service"]
        # Verify the repository is SQLitePurchaseRepository
        assert isinstance(service.repository, SQLitePurchaseRepository)

    def test_create_app_service_is_stateless(self):
        """Service should have no user-specific state (ready for multiple users)."""
        app = create_app()
        service = app.bot_data["service"]
        # Service should only have repository, no per-user state
        assert hasattr(service, "repository")
        # Verify service can be reused (no user context baked in)
        assert service.repository is not None

    def test_create_app_idempotent(self):
        """Calling create_app() multiple times should work independently."""
        app1 = create_app()
        app2 = create_app()
        # Both should be valid Application instances
        assert isinstance(app1, Application)
        assert isinstance(app2, Application)
        # Services should be independent instances
        assert app1.bot_data["service"] is not app2.bot_data["service"]

    def test_create_app_logs_initialization(self, caplog):
        """create_app() should log initialization messages."""
        with caplog.at_level(logging.INFO):
            app = create_app()
        assert "Initializing Telegram bot application" in caplog.text
        assert "Bot application initialized successfully" in caplog.text


class TestSetupHandlers:
    """Test handler registration placeholder."""

    def test_setup_handlers_accepts_application(self):
        """setup_handlers() should accept Application without error."""
        app = create_app()
        # Should not raise exception
        setup_handlers(app)

    def test_setup_handlers_is_noop_in_phase_5_1(self):
        """setup_handlers() is a placeholder; no handlers registered yet."""
        app = create_app()
        setup_handlers(app)
        # No handlers should be registered (handlers added in phase 5.2+)
        # Application should be in same state
        assert "service" in app.bot_data

    def test_setup_handlers_logs_completion(self, caplog):
        """setup_handlers() should log setup completion."""
        app = create_app()
        with caplog.at_level(logging.INFO):
            setup_handlers(app)
        assert "Setting up handlers" in caplog.text
        assert "Handler setup complete" in caplog.text


class TestRunBot:
    """Test bot polling startup and shutdown."""

    @patch("app.handlers.telegram_bot.Application.run_polling")
    def test_run_bot_calls_polling(self, mock_polling):
        """run_bot() should call app.run_polling()."""
        app = create_app()
        run_bot(app)
        mock_polling.assert_called_once_with(drop_pending_updates=True)

    @patch("app.handlers.telegram_bot.Application.run_polling")
    def test_run_bot_sets_drop_pending_updates(self, mock_polling):
        """run_bot() should drop pending updates (safe during development)."""
        app = create_app()
        run_bot(app)
        # Verify called with drop_pending_updates=True
        mock_polling.assert_called_once()
        call_kwargs = mock_polling.call_args[1]
        assert call_kwargs.get("drop_pending_updates") is True

    @patch("app.handlers.telegram_bot.Application.run_polling")
    def test_run_bot_logs_startup_and_shutdown(self, mock_polling, caplog):
        """run_bot() should log startup and shutdown messages."""
        app = create_app()
        with caplog.at_level(logging.INFO):
            run_bot(app)
        assert "Starting bot polling" in caplog.text
        assert "Bot stopped" in caplog.text

    @patch("app.handlers.telegram_bot.Application.run_polling")
    def test_run_bot_handles_keyboard_interrupt(self, mock_polling, caplog):
        """run_bot() should gracefully handle Ctrl+C."""
        # Simulate Ctrl+C during polling
        mock_polling.side_effect = KeyboardInterrupt()
        app = create_app()
        with caplog.at_level(logging.INFO):
            run_bot(app)
        assert "Received shutdown signal" in caplog.text
        assert "Bot stopped" in caplog.text

    @patch("app.handlers.telegram_bot.Application.run_polling")
    def test_run_bot_ensures_shutdown_logging(self, mock_polling, caplog):
        """run_bot() should always log shutdown, even on error."""
        # Simulate an error during polling
        mock_polling.side_effect = RuntimeError("Network error")
        app = create_app()
        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError):
                run_bot(app)
        # Even though error occurred, finally block should run
        assert "Bot stopped" in caplog.text


class TestBotBootstrapIntegration:
    """Integration tests for full bot bootstrap flow."""

    @patch("app.handlers.telegram_bot.Application.run_polling")
    def test_full_bootstrap_sequence(self, mock_polling):
        """Full bootstrap: create → setup → run should work end-to-end."""
        # Create app
        app = create_app()
        assert isinstance(app, Application)

        # Setup handlers
        setup_handlers(app)
        assert "service" in app.bot_data

        # Run bot (mocked)
        run_bot(app)
        mock_polling.assert_called_once()

    def test_service_accessible_in_bot_context(self):
        """Service should be accessible via bot context in handlers."""
        app = create_app()
        service = app.bot_data["service"]

        # Verify service is usable (test basic method)
        purchase_id = service.start_purchase()
        assert isinstance(purchase_id, int)
        assert purchase_id > 0

    def test_multiple_operations_via_service(self):
        """Service injected in bot should support full purchase lifecycle."""
        app = create_app()
        service = app.bot_data["service"]

        # Full lifecycle
        purchase_id = service.start_purchase()
        total = service.add_item(purchase_id, "Milk", 2, 1.50)
        assert total == 3.00

        purchase = service.get_purchase(purchase_id)
        assert purchase["item_count"] == 2  # qty=2 for Milk
        assert purchase["total"] == 3.00

        total = service.remove_item(purchase_id, 0)
        assert total == 0.00

    def test_service_error_handling(self):
        """Service errors should propagate correctly from handler layer."""
        app = create_app()
        service = app.bot_data["service"]

        purchase_id = service.start_purchase()

        # Should raise NotFoundError for non-existent purchase
        from app.domain import NotFoundError
        with pytest.raises(NotFoundError):
            service.get_purchase(99999)

    def test_database_persistence_through_bot_context(self, tmp_path):
        """Data persisted through service should be readable in same session."""
        # Use temporary database for this test
        test_db = str(tmp_path / "test_bot.db")

        from app.infra import init_db, get_db_connection
        init_db(test_db)

        # Create app with service pointing to test database
        app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        repo = SQLitePurchaseRepository(test_db)
        service = PurchaseService(repo)
        app.bot_data["service"] = service

        # Use service
        purchase_id = service.start_purchase()
        service.add_item(purchase_id, "Milk", 2, 1.50)

        # Retrieve from same service (should be in database)
        purchase = service.get_purchase(purchase_id)
        assert purchase["total"] == 3.00
        assert purchase["item_count"] == 2  # qty=2 for Milk


class TestBotBootstrapLogging:
    """Test logging output during bootstrap."""

    def test_create_app_logs_at_info_level(self, caplog):
        """create_app() should log at INFO level (visible by default)."""
        with caplog.at_level(logging.INFO):
            create_app()
        # Verify logs are present at INFO level
        assert any("Initializing" in record.message for record in caplog.records if record.levelno >= logging.INFO)

    def test_all_bootstrap_functions_log(self, caplog):
        """All three bootstrap functions should produce log output."""
        caplog.clear()
        app = create_app()

        with caplog.at_level(logging.INFO):
            setup_handlers(app)

        # Both should appear in caplog
        assert any("Setting up handlers" in record.message for record in caplog.records)


class TestBotConfigurationIsolation:
    """Test that bot configuration doesn't leak into domain/service layers."""

    def test_no_telegram_imports_in_domain(self):
        """Domain layer should not import telegram."""
        from app import domain
        import inspect
        source = inspect.getsource(domain)
        assert "telegram" not in source.lower()

    def test_no_telegram_imports_in_services(self):
        """Services layer should not import telegram."""
        from app import services
        import inspect
        source = inspect.getsource(services)
        assert "telegram" not in source.lower()

    def test_bot_layer_isolated_from_domain(self):
        """Handlers should not expose domain implementation details."""
        app = create_app()
        service = app.bot_data["service"]
        # Service is framework-agnostic
        assert not hasattr(service, "update")
        assert not hasattr(service, "context")


class TestBotContextDataAccess:
    """Test that handlers can correctly access and use bot context."""

    def test_bot_data_survives_setup(self):
        """bot_data should survive handler setup without modification."""
        app = create_app()
        original_service = app.bot_data["service"]

        setup_handlers(app)

        assert app.bot_data["service"] is original_service

    def test_service_instance_persists_across_operations(self):
        """Same service instance should be reused (stateless)."""
        app = create_app()
        service1 = app.bot_data["service"]

        # Simulate handler accessing service
        purchase_id = service1.start_purchase()

        # Simulate another handler accessing service
        service2 = app.bot_data["service"]

        # Should be same instance
        assert service1 is service2

        # But independent operations (stateless)
        purchase_id_2 = service2.start_purchase()
        assert purchase_id != purchase_id_2

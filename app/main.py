"""CartBot entry point."""

import logging
from app.infra import Config, setup_logging, init_db
from app.handlers.telegram_bot import create_app, setup_handlers, run_bot

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)

# Validate configuration
Config.validate()

# Initialize database
init_db()

# Application starts here
if __name__ == "__main__":
    logger.info("CartBot starting...")
    logger.info(f"Database: {Config.DATABASE_PATH}")
    logger.info(f"Log Level: {Config.LOG_LEVEL}")

    # Initialize and start Telegram bot
    app = create_app()
    setup_handlers(app)
    logger.info("Starting bot polling...")
    run_bot(app)


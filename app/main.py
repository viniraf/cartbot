"""CartBot entry point."""

import logging
from app.infra import Config, setup_logging, init_db

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
    logger.info("Ready to accept connections")


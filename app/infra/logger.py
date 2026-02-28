"""Centralized logging configuration."""

import logging
from app.infra.config import Config


def setup_logging(level=None):
    """
    Configure root logger with console output.
    
    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
               Defaults to Config.LOG_LEVEL.
    
    Returns:
        logging.Logger: Configured root logger.
    """
    if level is None:
        level = Config.LOG_LEVEL
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    return root_logger

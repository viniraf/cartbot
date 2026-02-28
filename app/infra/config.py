import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Centralized configuration loader from environment variables."""
    
    # Required variables - will raise ValueError if missing
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # Optional variables with defaults
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/cartbot.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required variables are set."""
        if not cls.TELEGRAM_TOKEN:
            raise ValueError(
                "TELEGRAM_TOKEN is required. "
                "Please set it in .env or as an environment variable."
            )

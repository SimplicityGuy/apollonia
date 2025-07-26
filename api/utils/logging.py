"""Logging configuration for API."""

import logging
import sys

from .emoji import EMOJI_MAP


class EmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis to log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with emoji prefix."""
        # Get emoji based on log level
        emoji = EMOJI_MAP.get(record.levelname, "📝")

        # Add emoji to message
        record.msg = f"{emoji} {record.msg}"

        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    # Create formatter
    formatter = EmojiFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific loggers
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

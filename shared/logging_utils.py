"""Centralized logging utilities for Apollonia services.

This module provides consistent emoji-prefixed logging across all services.
"""

import logging
from typing import Any, ClassVar


class EmojiLogger:
    """Logger wrapper that automatically adds emoji prefixes based on context."""

    # Emoji mappings by category
    EMOJI_MAP: ClassVar[dict[str, str]] = {
        # System Lifecycle
        "start": "🚀",
        "stop": "🛑",
        "shutdown": "🛑",
        "goodbye": "👋",
        "signal": "⚡",
        "interrupt": "⌨️",
        "fatal": "💥",
        # Connection & Network
        "connect": "🔌",
        "disconnect": "🔌",
        "network": "📡",
        "api": "🌐",
        "publish": "📤",
        "consume": "📥",
        "receive": "📥",
        # File Operations
        "directory": "📁",
        "subdirectory": "📂",
        "file": "📄",
        "watch": "👁️",
        "skip": "⏭️",
        # Processing & Analysis
        "process": "🔍",
        "audio": "🎵",
        "video": "🎬",
        "image": "🖼️",
        "ml": "🧠",
        "model": "🤖",
        # Status & Progress
        "success": "✅",
        "complete": "✅",
        "error": "❌",
        "fail": "❌",
        "warning": "⚠️",
        "critical": "🚨",
        "metrics": "📊",
        "loading": "🔄",
        "progress": "🔄",
        # Data & Storage
        "database": "💾",
        "package": "📦",
        "delete": "🗑️",
        "cleanup": "🧹",
        "batch": "💼",
        # Authentication & Security
        "auth": "🔐",
        "permission": "🔑",
        "security": "🛡️",
        "user": "👤",
        # Development & Debug
        "debug": "🐛",
        "config": "🔧",
        "log": "📝",
        "info": "💡",
    }

    def __init__(self, name: str):
        """Initialize emoji logger with underlying Python logger."""
        self.logger = logging.getLogger(name)

    def _add_emoji(self, message: str, emoji: str | None = None) -> str:
        """Add emoji prefix to message if not already present."""
        # If message already starts with an emoji, return as-is
        if message and len(message) > 0 and ord(message[0]) > 127:
            return message

        # If specific emoji provided, use it
        if emoji:
            return f"{emoji} {message}"

        # Otherwise, try to detect appropriate emoji from message content
        message_lower = message.lower()
        for keyword, emoji_char in self.EMOJI_MAP.items():
            if keyword in message_lower:
                return f"{emoji_char} {message}"

        # Default emoji based on log level will be added by specific methods
        return message

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message with emoji prefix."""
        message = self._add_emoji(message, self.EMOJI_MAP.get("debug", "🐛"))
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log info message with emoji prefix."""
        message = self._add_emoji(message)
        if not any(ord(c) > 127 for c in message[:2]):  # No emoji found
            message = f"💡 {message}"
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message with emoji prefix."""
        message = self._add_emoji(message, self.EMOJI_MAP.get("warning", "⚠️"))
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log error message with emoji prefix."""
        message = self._add_emoji(message, self.EMOJI_MAP.get("error", "❌"))
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log critical message with emoji prefix."""
        message = self._add_emoji(message, self.EMOJI_MAP.get("critical", "🚨"))
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log exception with emoji prefix."""
        message = self._add_emoji(message, self.EMOJI_MAP.get("fatal", "💥"))
        self.logger.exception(message, *args, **kwargs)

    # Proxy other logger methods
    def setLevel(self, level: int) -> None:
        """Set logger level."""
        self.logger.setLevel(level)

    @property
    def level(self) -> int:
        """Get logger level."""
        return self.logger.level

    @property
    def handlers(self) -> list:
        """Get logger handlers."""
        return self.logger.handlers

    def addHandler(self, handler: logging.Handler) -> None:
        """Add handler to logger."""
        self.logger.addHandler(handler)


def get_logger(name: str) -> EmojiLogger:
    """Get an emoji-enabled logger for the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        EmojiLogger instance
    """
    return EmojiLogger(name)


# Example usage for different contexts
def log_lifecycle_event(logger: EmojiLogger, event: str, details: str = "") -> None:
    """Log a system lifecycle event with appropriate emoji."""
    if event == "start":
        logger.info(f"🚀 Starting {details}")
    elif event == "stop":
        logger.info(f"🛑 Stopping {details}")
    elif event == "connect":
        logger.info(f"🔌 Connecting to {details}")
    elif event == "disconnect":
        logger.info(f"🔌 Disconnecting from {details}")


def log_processing_event(logger: EmojiLogger, media_type: str, file_path: str, status: str) -> None:
    """Log a media processing event with appropriate emoji."""
    emoji_map = {
        "audio": "🎵",
        "video": "🎬",
        "image": "🖼️",
    }
    status_map = {
        "start": "Processing",
        "complete": "✅ Completed processing",
        "error": "❌ Error processing",
    }

    emoji = emoji_map.get(media_type, "📄")
    status_text = status_map.get(status, status)

    if status == "error":
        logger.error(f"{emoji} {status_text} {media_type} file: {file_path}")
    else:
        logger.info(f"{emoji} {status_text} {media_type} file: {file_path}")

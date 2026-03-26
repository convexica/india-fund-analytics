import logging
import sys
from typing import Any, Dict, Optional


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a professionally configured logger with a standardized format.
    Ensures that logs are clear, timestamped, and categorized by module.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if the logger is already configured
    if not logger.handlers:
        logger.setLevel(level)

        # Institutional Format: [TIMESTAMP] [LEVEL] [MODULE] - MESSAGE
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Standard Output (Console)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_event(logger: logging.Logger, event_name: str, level: str = "info", **kwargs: Any) -> None:
    """
    Provides a pseudo-structured logging interface.
    Usage: log_event(logger, "CACHE_HIT", code="123456", status="SUCCESS")
    """
    # Formatting key-value pairs for clarity
    context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    message = f"[{event_name}] {context}" if context else f"[{event_name}]"

    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from .config import DATA_DIR


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add structured data if present
        if hasattr(record, "extra_data") and record.extra_data:
            log_entry.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging(level: int = logging.INFO, structured: bool = True) -> None:
    """Configure application-wide logging with rotation and structured output.

    Creates rotating file handlers with optional structured JSON logging:
    - app.log for INFO and above
    - debug.log for DEBUG (optional, controlled by level)
    - Structured logging for better monitoring and analysis
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    logger = logging.getLogger()
    # Avoid re-adding handlers if configure_logging is called multiple times
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    logger.setLevel(level)

    # Choose formatter based on structured flag
    if structured:
        formatter = StructuredJSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

    app_handler = RotatingFileHandler(
        os.path.join(DATA_DIR, "app.log"), maxBytes=2 * 1024 * 1024, backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    debug_handler = RotatingFileHandler(
        os.path.join(DATA_DIR, "debug.log"), maxBytes=5 * 1024 * 1024, backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(app_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)

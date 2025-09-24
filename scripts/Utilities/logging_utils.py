import logging
import os
from logging.handlers import RotatingFileHandler

from .config import DATA_DIR


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging with rotation.

    Creates two rotating file handlers:
    - app.log for INFO and above
    - debug.log for DEBUG (optional, controlled by level)
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    logger = logging.getLogger()
    # Avoid re-adding handlers if configure_logging is called multiple times
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    logger.setLevel(level)

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


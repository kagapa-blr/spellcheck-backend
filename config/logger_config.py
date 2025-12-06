import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Project root (one level up from current file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)


def setup_logger(
    module_name: str,
    log_level=logging.DEBUG,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB per log file
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger for a given module with both console and file handlers.
    - Rotates log files to prevent excessive size.
    - UTF-8 encoding.
    - Avoids duplicate logging.
    """

    logger = logging.getLogger(module_name)

    # Avoid adding multiple handlers if logger already has them
    if logger.hasHandlers():
        return logger

    logger.setLevel(log_level)
    logger.propagate = False

    # Log file name based on current date
    log_filename = datetime.now().strftime("spellcheck_%d_%m_%Y.log")
    log_file_path = os.path.join(LOGS_DIR, log_filename)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialized for module: {module_name}. Log file: {log_file_path}")

    return logger

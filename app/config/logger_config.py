from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()


def setup_logger(
    module_name: str,
    log_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 10,
) -> logging.Logger:
    """
    Configure application logger.

    Directory structure:

    logs/
    └── 2026-06-08/
        ├── spellcheck.log
        ├── spellcheck.log.1
        └── spellcheck.log.2

    Features:
    - Reads log path from .env
    - Creates missing directories automatically
    - Daily folder separation
    - Rotating log files
    - UTF-8 encoding
    - Prevents duplicate handlers
    """

    logger = logging.getLogger(module_name)

    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    logger.propagate = False

    # ------------------------------------------------------------------
    # Project Root
    # ------------------------------------------------------------------
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # ------------------------------------------------------------------
    # Base Logs Directory (.env)
    # ------------------------------------------------------------------
    logs_dir = os.getenv("LOGS_DIR", "logs")

    if not os.path.isabs(logs_dir):
        logs_dir = os.path.join(project_root, logs_dir)

    # ------------------------------------------------------------------
    # Create Date Folder
    # Example:
    # logs/2026-06-08/
    # ------------------------------------------------------------------
    date_folder = datetime.now().strftime("%Y-%m-%d")

    daily_log_dir = os.path.join(logs_dir, date_folder)
    os.makedirs(daily_log_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Log File
    # ------------------------------------------------------------------
    log_file_path = os.path.join(daily_log_dir, "spellcheck.log")

    # ------------------------------------------------------------------
    # Formatter
    # ------------------------------------------------------------------
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ------------------------------------------------------------------
    # Rotating File Handler
    # ------------------------------------------------------------------
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ------------------------------------------------------------------
    # Console Handler
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler()

    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ------------------------------------------------------------------
    # Add Handlers
    # ------------------------------------------------------------------
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

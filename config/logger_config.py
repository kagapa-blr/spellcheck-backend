import logging
import os
from datetime import datetime
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # Moves one level up

def setup_logger(module_name):
    """Set up a logger for the specified module name."""

    # Get the root directory of the project
    #PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

    # Create a logs directory if it doesn't exist
    LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Create a log file name based on the current date
    log_filename = datetime.now().strftime("spellcheck_%d_%m_%Y.log")
    log_file_path = os.path.join(LOGS_DIR, log_filename)

    # Create a logger
    logger = logging.getLogger(module_name)

    # Clear any existing handlers to prevent duplicate logging
    logger.handlers = []

    # Set the logger's propagation to False to prevent duplicate logging
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        try:
            # Create a file handler
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)

            # Create a console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Create a formatter and set it for both handlers
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

            logger.info(f"Logger initialized for module: {module_name}. Log file: {log_file_path}")
        except Exception as e:
            # Log the error if file handler creation fails
            logger.error(f"Failed to create file handler: {e}")
    else:
        logger.info(f"Logger already initialized for module: {module_name}")

    return logger

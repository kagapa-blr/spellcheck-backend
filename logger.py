import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Get the root directory of the project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Create a logs directory if it doesn't exist
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Create a log file name with the current date and time
log_filename = datetime.now().strftime("spellcheck_log_%d%m%Y_%H%M%S.log")
log_file_path = os.path.join(LOGS_DIR, log_filename)

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the logger to the lowest level

# Create a file handler that logs debug and higher levels to a file
file_handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setLevel(logging.DEBUG)

# Create a console handler that logs only info and higher levels to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Example usage:
if __name__ == "__main__":
    logger.info("Logger initialized successfully.")

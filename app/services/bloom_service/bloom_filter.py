from __future__ import annotations

import os

from dotenv import load_dotenv
from pybloom_live import BloomFilter
from sqlalchemy.orm import Session

from app.config.logger_config import setup_logger
from app.dbmodels.models import MainDictionary

# Load environment variables from .env
load_dotenv()

# Set up logger with the module name
logger = setup_logger(__name__)


class BloomWordFilter:
    """
    Bloom filter for fast word existence checks.

    Capacity is based on the current MainDictionary size with a 20% growth
    buffer. If the dictionary is empty, a default capacity from .env is used.
    """

    def __init__(self, db: Session):
        """
        Initialize the Bloom filter.

        Args:
            db: SQLAlchemy database session.
        """

        # Read values from .env (with defaults if not set)
        default_capacity = int(os.getenv("BLOOM_DEFAULT_CAPACITY", "100000"))
        error_rate = float(os.getenv("BLOOM_ERROR_RATE", "0.001"))

        # Actual number of words currently in the database
        self.original_word_count = db.query(MainDictionary).count()

        if self.original_word_count == 0:
            logger.info(
                f"No words found in the database. "
                f"Assigning default Bloom filter capacity of {default_capacity}."
            )
            self.loaded_count = 0
            capacity = default_capacity
        else:
            self.loaded_count = self.original_word_count
            # Add 20% buffer for future growth
            capacity = int(self.original_word_count * 1.2)

        self.error_rate = error_rate

        self.bloom_filter = BloomFilter(
            capacity=capacity,
            error_rate=error_rate,
        )

        logger.info(
            f"Bloom filter initialized successfully. "
            f"Actual word count: {self.original_word_count}, "
            f"Capacity: {capacity}, "
            f"Error rate: {error_rate}"
        )

    def load_words(self, db: Session) -> None:
        """
        Load words from MainDictionary into the Bloom filter.
        """
        words = db.query(MainDictionary.word).all()
        loaded_count = 0

        for (word,) in words:
            if word:
                self.bloom_filter.add(word)
                loaded_count += 1

        self.loaded_count = loaded_count

        logger.info(
            f"Bloom filter loaded with {loaded_count} words "
            f"(capacity: {self.get_capacity()})."
        )

    def __contains__(self, word: str) -> bool:
        return word in self.bloom_filter

    def get_size(self) -> int:
        return len(self.bloom_filter)

    def is_empty(self) -> bool:
        return self.get_size() == 0

    def get_capacity(self) -> int:
        return self.bloom_filter.capacity

    def get_error_rate(self) -> float:
        return self.error_rate

    def get_loaded_count(self) -> int:
        return self.loaded_count

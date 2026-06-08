from __future__ import annotations

from pybloom_live import BloomFilter
from sqlalchemy.orm import Session

from app.config.logger_config import setup_logger
from app.dbmodels.models import MainDictionary

# Set up logger with the module name
logger = setup_logger(__name__)


class BloomWordFilter:
    """
    Bloom filter for fast word existence checks.

    Capacity is based on the current MainDictionary size with a 20% growth
    buffer. If the dictionary is empty, a default capacity of 100,000 is used.

    Terminology:
    - original_word_count: actual number of words in MainDictionary
    - loaded_count: actual number of words loaded into the Bloom filter
    - capacity: Bloom filter capacity (may include growth buffer)
    """

    def __init__(self, db: Session, error_rate: float):
        """
        Initialize the Bloom filter.

        Args:
            db: SQLAlchemy database session.
            error_rate: Desired Bloom filter false positive rate.
        """

        # Actual number of words currently in the database
        self.original_word_count = db.query(MainDictionary).count()

        if self.original_word_count == 0:
            logger.info("No words found in the database. "
                "Assigning default Bloom filter capacity of 100000."
            )

            self.loaded_count = 0
            capacity = 100000
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
        """
        Check whether a word may exist in the Bloom filter.

        Returns:
            True if the word may exist.
            False if the word definitely does not exist.
        """
        return word in self.bloom_filter

    def get_size(self) -> int:
        """
        Return the current number of elements stored in the Bloom filter.
        """
        return len(self.bloom_filter)

    def is_empty(self) -> bool:
        """
        Check whether the Bloom filter is empty.
        """
        return self.get_size() == 0

    def get_capacity(self) -> int:
        """
        Return the Bloom filter capacity.
        """
        return self.bloom_filter.capacity

    def get_error_rate(self) -> float:
        """
        Return the configured Bloom filter error rate.
        """
        return self.error_rate

    def get_loaded_count(self) -> int:
        """
        Return the actual number of words loaded into the Bloom filter.

        This value does NOT include the 20% capacity buffer.
        """
        return self.loaded_count

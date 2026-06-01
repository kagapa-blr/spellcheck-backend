from __future__ import annotations

from pybloom_live import BloomFilter
from sqlalchemy.orm import Session

from config.logger_config import setup_logger
from dbmodels.models import MainDictionary

# Set up logger with the module name
logger = setup_logger(__name__)


class BloomWordFilter:
    def __init__(self, db: Session, error_rate: float):
        # Query the number of words in the MainDictionary
        self.word_count = db.query(MainDictionary).count()
        # If no words in the database, assign a default capacity of 100,000
        if self.word_count == 0:
            logger.info("No words found in the database. Assigning default capacity of 100,000.")
            self.word_count = 100000
        else:
            # Add buffer for future growth (20% extra capacity)
            self.word_count = int(self.word_count * 1.2)
            
        # Initialize the Bloom filter with the word count as capacity
        self.bloom_filter = BloomFilter(capacity=self.word_count, error_rate=error_rate)
        self.error_rate = error_rate

    def load_words(self, db: Session):
        """Load words from the MainDictionary into the Bloom filter."""
        words = db.query(MainDictionary.word).all()
        loaded_count = 0
        for word, in words:  # Unpack the tuple returned by query
            self.bloom_filter.add(word)
            loaded_count += 1
        logger.info(f"Bloom filter loaded with {loaded_count} words (capacity: {self.word_count}).")

    def __contains__(self, word: str) -> bool:
        """Check if a word is in the Bloom filter."""
        return word in self.bloom_filter

    def get_size(self) -> int:
        """Return the estimated number of elements in the Bloom filter."""
        return len(self.bloom_filter)  # Calls __len__()

    def is_empty(self) -> bool:
        """Check if the Bloom filter is empty."""
        return self.get_size() == 0

    def get_capacity(self) -> int:
        """Return the capacity of the Bloom filter."""
        return self.bloom_filter.capacity

    def get_error_rate(self) -> float:
        """Return the error rate of the Bloom filter."""
        return self.error_rate

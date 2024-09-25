# bloom_filter/filter.py

from pybloom_live import BloomFilter
from sqlalchemy.orm import Session
from models import MainDictionary

class BloomWordFilter:
    def __init__(self, capacity: int, error_rate: float):
        self.bloom_filter = BloomFilter(capacity=capacity, error_rate=error_rate)

    def load_words(self, db: Session):
        """Load words from the MainDictionary into the Bloom filter."""
        words = db.query(MainDictionary.word).all()
        for word, in words:  # Unpack the tuple returned by query
            self.bloom_filter.add(word)

    def __contains__(self, word: str) -> bool:
        """Check if a word is in the Bloom filter."""
        return word in self.bloom_filter

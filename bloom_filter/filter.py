from pybloom_live import BloomFilter
from sqlalchemy.orm import Session

from models import MainDictionary


class BloomWordFilter:
    def __init__(self, db: Session, error_rate: float):
        # Query the number of words in the MainDictionary
        self.word_count = db.query(MainDictionary).count()
        # If no words in the database, assign a default capacity of 100,000
        if self.word_count == 0:
            print("No words found in the database. Assigning default capacity of 100,000.")
            self.word_count = 100000
        # Initialize the Bloom filter with the word count as capacity
        self.bloom_filter = BloomFilter(capacity=self.word_count, error_rate=error_rate)

    def load_words(self, db: Session):
        """Load words from the MainDictionary into the Bloom filter."""
        words = db.query(MainDictionary.word).all()
        for word, in words:  # Unpack the tuple returned by query
            self.bloom_filter.add(word)
        print(f"Bloom filter loaded with {self.word_count} words.")
        return self.bloom_filter

    def __contains__(self, word: str) -> bool:
        """Check if a word is in the Bloom filter."""
        return word in self.bloom_filter

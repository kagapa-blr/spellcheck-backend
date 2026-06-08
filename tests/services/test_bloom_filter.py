from sqlalchemy.orm import Session

from app.config.database import get_db
from services.bloom_service.bloom_filter import BloomWordFilter

mock_db: Session = next(get_db())

def test_bloom_initialization(mock_db):
    bloom = BloomWordFilter(mock_db)

    assert bloom.get_capacity() == 120
    assert bloom.get_error_rate() == 0.001


def test_load_words(mock_db):
    bloom = BloomWordFilter(mock_db)

    loaded = bloom.load_words(mock_db)

    assert loaded == 3
    assert bloom.get_size() == 3


def test_contains_word(mock_db):
    bloom = BloomWordFilter(mock_db)

    bloom.load_words(mock_db)

    assert bloom.contains("hello") is True


def test_missing_word(mock_db):
    bloom = BloomWordFilter(mock_db)

    bloom.load_words(mock_db)

    assert bloom.contains("unknown") is False


def test_stats(mock_db):
    bloom = BloomWordFilter(mock_db)

    bloom.load_words(mock_db)

    stats = bloom.get_stats()

    assert "size" in stats
    assert "capacity" in stats
    assert "error_rate" in stats
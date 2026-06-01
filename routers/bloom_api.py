# routers/bloom_api.py
from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from bloom_filter.filter import BloomWordFilter
from config.database import get_db
from config.logger_config import setup_logger
from dbmodels.models import MainDictionary

# Set up logger with the module name
logger = setup_logger(__name__)
router = APIRouter()

last_update_timestamp = None  # Initialize to None


# Request model for checking a word
class WordCheckRequest(BaseModel):
    word: str


# New model for Bloom filter statistics
class BloomFilterStatsResponse(BaseModel):
    size: int
    capacity: int
    error_rate: float
    is_empty: bool
    last_updated: datetime = None


# Global variable to hold the initialized Bloom filter
loaded_bloom: BloomWordFilter = None


async def bloom_initialization():
    """Initialize the Bloom filter by loading words from the database."""
    global loaded_bloom, last_update_timestamp
    if loaded_bloom is None:  # Initialize only if not already initialized
        db: Session = next(get_db())
        try:
            loaded_bloom = BloomWordFilter(db, error_rate=0.001)
            loaded_bloom.load_words(db)  # Load words into the Bloom filter
            last_update_timestamp = datetime.now()  # Set the current UTC time
            logger.info(f"Bloom filter initialized successfully with {loaded_bloom.get_size()} words.")
        finally:
            db.close()


async def bloom_reinitialization():
    """Reinitialize the Bloom filter by loading words from the database."""
    global loaded_bloom, last_update_timestamp
    try:
        db: Session = next(get_db())
        try:
            # Reset the global variable
            loaded_bloom = None
            
            # Reinitialize with fresh word count
            loaded_bloom = BloomWordFilter(db, error_rate=0.001)
            loaded_bloom.load_words(db)
            
            last_update_timestamp = datetime.now()
            logger.info(f"Bloom filter reinitialized successfully with {loaded_bloom.get_size()} words.")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during bloom filter reinitialization: {str(e)}")
        raise




@router.post("/check_word/")
async def check_word_in_bloom(request: WordCheckRequest):
    """Check if a word exists in the Bloom filter.
    
    NOTE: This endpoint does NOT reload the Bloom filter - it uses the already-loaded 
    instance for performance. To reload the filter after dictionary updates, call /admin/reload 
    endpoint only.
    """
    try:
        if loaded_bloom is None:
            logger.warning("Bloom filter not initialized")
            return {
                "message": "Bloom filter is not initialized. Please wait for the application to start.",
                "status": "not_initialized"
            }

        word = request.word.strip()
        
        if not word:
            logger.warning("Empty word provided for checking")
            return {
                "message": "Word cannot be empty",
                "status": False
            }

        logger.info(f"Checking word in bloom: '{word}'")

        # Check if the word contains only English letters or digits
        if re.match(r'^[a-zA-Z0-9]+$', word):
            logger.info(f"Word '{word}' contains only English letters or digits")
            return {
                "message": f"The word '{word}' contains only English letters or digits.",
                "status": True
            }

        # Check the Bloom filter for non-English words (like Kannada)
        word_exists = word in loaded_bloom
        logger.info(f"Word '{word}' in bloom: {word_exists}")
        
        if word_exists:
            return {
                "message": f"The word '{word}' is present in the Main Dictionary.",
                "status": True
            }
        else:
            return {
                "message": f"The word '{word}' is definitely not in the dictionary.",
                "status": False
            }
    
    except Exception as e:
        logger.error(f"Error checking word '{request.word}' in bloom: {str(e)}", exc_info=True)
        return {
            "message": f"Error checking word: {str(e)}",
            "status": False
        }


@router.get("/bloom_stats/", response_model=BloomFilterStatsResponse)
async def get_bloom_stats():
    """Get statistics about the Bloom filter."""
    try:
        if loaded_bloom is None:
            logger.warning("Bloom filter not initialized when accessing stats")
            return BloomFilterStatsResponse(
                size=0,
                capacity=0,
                error_rate=0.0,
                is_empty=True,
                last_updated=None
            )

        # Get actual count from database for accuracy
        from config.database import get_db
        try:
            db: Session = next(get_db())
            try:
                actual_count = db.query(MainDictionary).count()
                logger.info(f"Database count: {actual_count}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not get count from database: {str(e)}, using bloom filter size")
            actual_count = loaded_bloom.get_size()

        # Log if there's a discrepancy
        bloom_size = loaded_bloom.get_size()
        if actual_count != bloom_size:
            logger.info(f"Count discrepancy: Database has {actual_count} words, Bloom filter shows {bloom_size}")

        logger.info(f"Returning bloom stats: size={actual_count}, capacity={loaded_bloom.get_capacity()}, error_rate={loaded_bloom.get_error_rate()}")
        
        return BloomFilterStatsResponse(
            size=actual_count,
            capacity=loaded_bloom.get_capacity(),
            error_rate=loaded_bloom.get_error_rate(),
            is_empty=actual_count == 0,
            last_updated=last_update_timestamp
        )
    
    except Exception as e:
        logger.error(f"Error getting bloom stats: {str(e)}", exc_info=True)
        return BloomFilterStatsResponse(
            size=0,
            capacity=0,
            error_rate=0.0,
            is_empty=True,
            last_updated=None
        )


def filter_missing_words(words: list[str]) -> list[str]:
    """
    Takes a list of words and returns the words that are not in the Bloom filter.

    Args:
        words (list[str]): The list of words to check.

    Returns:
        list[str]: A list of words that are not present in the Bloom filter.
    """
    if loaded_bloom is None:
        return words
    missing_words = [word for word in words if word not in loaded_bloom]
    return missing_words

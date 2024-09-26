# routers/bloom_api.py

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from bloom_filter.filter import BloomWordFilter
from database import get_db

router = APIRouter()


# Request model for checking a word
class WordCheckRequest(BaseModel):
    word: str


# New model for Bloom filter statistics
class BloomFilterStatsResponse(BaseModel):
    size: int
    capacity: int
    error_rate: float
    is_empty: bool


# Global variable to hold the initialized Bloom filter
loaded_bloom: BloomWordFilter = None


async def bloom_initialization():
    """Initialize the Bloom filter by loading words from the database."""
    db: Session = next(get_db())
    """Initialize the Bloom filter by loading words from the database."""
    global loaded_bloom
    if loaded_bloom is None:  # Initialize only if not already initialized
        loaded_bloom = BloomWordFilter(db, error_rate=0.001)
        loaded_bloom.load_words(db)  # Load words into the Bloom filter
        print("Bloom filter initialized successfully.")


async def bloom_reinitialization():
    """Reinitialize the Bloom filter by loading words from the database."""
    global loaded_bloom
    if loaded_bloom is not None:  # Only reinitialize if initialized
        loaded_bloom = None  # Reset the global variable
        await bloom_initialization()  # Reinitialize the Bloom filter
        print("Bloom filter reinitialized successfully.")


@router.post("/check_word/")
async def check_word_in_bloom(request: WordCheckRequest):
    """Check if a word exists in the Bloom filter."""
    if loaded_bloom == None:
        return {
            "message": "Bloom filter is not initialized. Please wait for the application to start.",
            "status": "not_initialized"
        }
    word = request.word
    if word in loaded_bloom:
        return {
            "message": f"The word '{word}' is present in the Main Dictionary.",
            "status": "true"
        }
    else:
        return {
            "message": f"The word '{word}' is definitely not in the dictionary.",
            "status": "false"
        }


@router.get("/bloom_stats/", response_model=BloomFilterStatsResponse)
async def get_bloom_stats():
    """Get statistics about the Bloom filter."""
    if loaded_bloom is None:
        return {
            "message": "Bloom filter is not initialized.",
            "status": "not_initialized"
        }

    return BloomFilterStatsResponse(
        size=loaded_bloom.get_size(),
        capacity=loaded_bloom.get_capacity(),
        error_rate=loaded_bloom.get_error_rate(),
        is_empty=loaded_bloom.is_empty()
    )

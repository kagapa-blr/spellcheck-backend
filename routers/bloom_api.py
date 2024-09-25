# routers/bloom_api.py

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from bloom_filter.filter import BloomWordFilter
from database import get_db

router = APIRouter()

# Initialize the Bloom filter with a specified capacity and error rate
bloom_filter = BloomWordFilter(capacity=10000, error_rate=0.1)


# Request model for checking a word
class WordCheckRequest(BaseModel):
    word: str


async def bloom_initialization():
    """Initialize the Bloom filter by loading words from the database."""
    db: Session = next(get_db())
    bloom_filter.load_words(db)
    print("Bloom filter loaded with words from MainDictionary.")


@router.post("/check_word/")
async def check_word_in_bloom(request: WordCheckRequest):
    """Check if a word exists in the Bloom filter."""
    word = request.word
    if word in bloom_filter:
        return {
            "message": f"The word '{word}' is present in the Main Dictionary.",
            "status": "true"
        }
    else:
        return {
            "message": f"The word '{word}' is definitely not in the dictionary.",
            "status": "false"
        }

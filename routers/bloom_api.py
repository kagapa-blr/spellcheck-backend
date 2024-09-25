# routers/bloom_api.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import FastAPI
from database import get_db
from bloom_filter.filter import BloomWordFilter

router = APIRouter()

# Initialize the Bloom filter with a specified capacity and error rate
bloom_filter = BloomWordFilter(capacity=10000, error_rate=0.1)



async def bloom_initialization():
    """Initialize the Bloom filter by loading words from the database."""
    db: Session = next(get_db())
    bloom_filter.load_words(db)
    print("Bloom filter loaded with words from MainDictionary.")

@router.get("/check_word/{word}")
async def check_word_in_bloom(word: str):
    """Check if a word exists in the Bloom filter."""
    if word in bloom_filter:
        return {"message": f"The word '{word}' is possibly in the dictionary."}
    else:
        return {"message": f"The word '{word}' is definitely not in the dictionary."}

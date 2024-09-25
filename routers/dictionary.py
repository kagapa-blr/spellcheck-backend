import hashlib
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import MainDictionary

router = APIRouter()


# Request model for adding, updating, and deleting a word
class WordRequest(BaseModel):
    word: str


# Response model for adding, updating, and deleting a word
class AddWordResponse(BaseModel):
    message: str


# API to check if a word exists in the main dictionary
@router.post("/check-word/", response_model=AddWordResponse)
def check_word(request: WordRequest, db: Session = Depends(get_db)):
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == request.word).first()
    if word_entry:
        return AddWordResponse(message="Word found in dictionary")
    return AddWordResponse(message="Word not found")


# API for users to add a word
@router.post("/add-word/", response_model=AddWordResponse)
def add_word(request: WordRequest, db: Session = Depends(get_db)):
    word = request.word
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == word).first()
    if word_entry:
        return AddWordResponse(message="Word already exists in the dictionary")

    new_word = MainDictionary(
        word=word,
        wordUniqueId=generate_word_id(word),
        frequency=1
    )
    db.add(new_word)
    db.commit()
    return AddWordResponse(message="Word added to dictionary")


# API to update a word
@router.put("/update-word/", response_model=AddWordResponse)
def update_word(request: WordRequest, db: Session = Depends(get_db)):
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == request.word).first()
    if not word_entry:
        raise HTTPException(status_code=404, detail="Word not found in the dictionary")

    # Assuming you want to update frequency or other attributes; adjust accordingly
    word_entry.frequency += 1  # Increment the frequency for demonstration
    db.commit()
    return AddWordResponse(message="Word updated successfully")


# API to delete a word
@router.delete("/delete-word/", response_model=AddWordResponse)
def delete_word(request: WordRequest, db: Session = Depends(get_db)):
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == request.word).first()
    if not word_entry:
        raise HTTPException(status_code=404, detail="Word not found in the dictionary")

    db.delete(word_entry)
    db.commit()
    return AddWordResponse(message="Word deleted successfully")


# API to update the dictionary from a text file
@router.get("/update-dictionary/", response_model=AddWordResponse)
def update_dictionary(db: Session = Depends(get_db)):
    file_path = "testwords.txt"

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="collections.txt file not found")

    added_words = []
    with open(file_path, "r") as file:
        words = file.readlines()

    for word in words:
        word = word.strip()
        if not word:
            continue

        word_entry = db.query(MainDictionary).filter(MainDictionary.word == word).first()
        if not word_entry:
            new_word = MainDictionary(
                word=word,
                wordUniqueId=generate_word_id(word),
                frequency=1
            )
            db.add(new_word)
            added_words.append(word)

    db.commit()
    return AddWordResponse(message=f"Added {len(added_words)} new words to the dictionary.")


def generate_word_id(word: str) -> str:
    """Generate a unique ID for the word using hash."""
    return hashlib.sha256(word.encode()).hexdigest()[:10]

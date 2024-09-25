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


from sqlalchemy.exc import IntegrityError  # Import IntegrityError for specific handling


@router.get("/update-dictionary/", response_model=AddWordResponse)
def update_dictionary(db: Session = Depends(get_db)):
    """Update the main dictionary by adding words from a text file."""
    file_path = "testwords.txt"  # Path to the text file

    # Check if the file exists
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="testwords.txt file not found")

    added_words = []
    errors = []  # To keep track of words that caused errors
    with open(file_path, "r") as file:
        words = file.readlines()  # Read all lines (words) from the file

    for word in words:
        word = word.strip()  # Remove whitespace and newlines
        if not word:  # Skip empty lines
            continue

        # Prepare the new word entry
        new_word = MainDictionary(
            word=word,
            added_by_username=None,  # Set this as needed, or remove if not required
            wordUniqueId=generate_word_id(word),  # Generate a unique ID for the new word
            frequency=1  # Set default frequency to 1
        )

        try:
            db.add(new_word)  # Add the new word to the session
            db.commit()  # Commit the changes
            added_words.append(word)  # Keep track of successfully added words
        except IntegrityError as ie:
            # Handle IntegrityError (e.g., duplicate entry)
            errors.append(f"Duplicate entry for word '{word}': {str(ie)}")
            db.rollback()  # Rollback the current transaction to reset the session
        except Exception as e:
            # Handle other potential exceptions
            errors.append(f"Error adding word '{word}': {str(e)}")
            db.rollback()  # Rollback on other exceptions as well

    # Prepare a response message
    response_message = f"Added {len(added_words)} new words to the dictionary."
    if errors:
        response_message += f" Skipped {len(errors)} words due to errors."

    return AddWordResponse(message=response_message)


def generate_word_id(word: str) -> str:
    """Generate a unique ID for the word using hash."""
    return hashlib.sha256(word.encode()).hexdigest()[:10]

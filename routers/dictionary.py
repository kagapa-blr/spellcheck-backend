import os
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError  # Import IntegrityError for specific handling
from sqlalchemy.orm import Session

from database import get_db
from models import MainDictionary

router = APIRouter()


# class WordRequest(BaseModel):
#     words: List[str]
#     added_by_username: Optional[str] = None  # Make added_by_username optional


# Response model for adding, updating, and deleting a word
class AddWordResponse(BaseModel):
    message: str


class WordEntry(BaseModel):
    word: str
    frequency: int


class WordRequest(BaseModel):
    words: List[WordEntry]
    added_by_username: Optional[str] = None  # Optional username


# API to check if a word exists in the main dictionary
@router.post("/check-word/", response_model=AddWordResponse)
def check_word(request: WordRequest, db: Session = Depends(get_db)):
    word_entries = db.query(MainDictionary).filter(MainDictionary.word.in_(request.words)).all()
    existing_words = [entry.word for entry in word_entries]
    if existing_words:
        return AddWordResponse(message=f"Words found in dictionary: {', '.join(existing_words)}")
    return AddWordResponse(message="No words found")


# API for users to add words
@router.post("/add-words/", response_model=AddWordResponse)
def add_words_to_dictionary(request: WordRequest, db: Session = Depends(get_db)):
    """
    Adds words to the main dictionary from a WordRequest object.

    Parameters:
    - request (WordRequest): A WordRequest object containing a list of WordEntry objects and an optional added_by_username.
    - db (Session): A SQLAlchemy Session object for database operations.

    Returns:
    - AddWordResponse: A response object containing a message indicating the number of words added to the dictionary.
    """
    added_count = 0
    for entry in request.words:
        # Check if the word already exists
        existing_word = db.query(MainDictionary).filter(MainDictionary.word == entry.word).first()

        if existing_word:
            continue  # Skip if the word already exists

        new_word = MainDictionary(
            word=entry.word,
            added_by_username=request.added_by_username if request.added_by_username else None,
            frequency=entry.frequency if entry.frequency else 1
        )
        db.add(new_word)
        added_count += 1

    db.commit()  # Commit all new words at once

    return AddWordResponse(message=f"Added {added_count} words to the dictionary.")


# API to update a word
@router.put("/update-word/", response_model=AddWordResponse)
def update_word(request: WordRequest, db: Session = Depends(get_db)):
    if len(request.words) != 1:
        raise HTTPException(status_code=400, detail="Update requires exactly one word.")

    word = request.words[0]
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == word).first()
    if not word_entry:
        raise HTTPException(status_code=404, detail="Word not found in the dictionary")

    word_entry.frequency += 1  # Increment the frequency for demonstration
    db.commit()
    return AddWordResponse(message="Word updated successfully")


# API to delete a word
@router.delete("/delete-word/", response_model=AddWordResponse)
def delete_word(request: WordRequest, db: Session = Depends(get_db)):
    if len(request.words) != 1:
        raise HTTPException(status_code=400, detail="Deletion requires exactly one word.")

    word = request.words[0]
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == word).first()
    if not word_entry:
        raise HTTPException(status_code=404, detail="Word not found in the dictionary")

    db.delete(word_entry)
    db.commit()
    return AddWordResponse(message="Word deleted successfully")


# Function to get the last word serial number from the database
def get_last_serial_number(db: Session) -> int:
    """Get the total number of rows in the MainDictionary and return total rows + 1."""
    total_rows = db.query(func.count(MainDictionary.id)).scalar()
    return total_rows + 1  # Return total rows + 1


# Function to process words in batches of 1000
def process_words_in_batches(words, db: Session, batch_size=3000):
    added_words = []
    errors = []
    batch = []

    for word in words:
        word = word.strip()
        if not word:
            continue

        batch.append(word)  # Store word

        if len(batch) == batch_size:
            added, failed = add_words_to_db(batch, db)
            added_words.extend(added)
            errors.extend(failed)
            batch = []  # Reset batch after processing

    # Process any remaining words in the final batch
    if batch:
        added, failed = add_words_to_db(batch, db)
        added_words.extend(added)
        errors.extend(failed)

    return added_words, errors


# Function to add words to the database
def add_words_to_db(words, db: Session):
    added_words = []
    errors = []

    for word in words:
        new_word = MainDictionary(
            word=word,
            frequency=1  # No unique ID needed
        )

        try:
            db.add(new_word)
            db.commit()
            added_words.append(word)
        except IntegrityError as ie:
            # Handle duplicate entries
            errors.append(f"Duplicate entry for word '{word}': {str(ie)}")
            db.rollback()
        except Exception as e:
            # Handle any other exception
            errors.append(f"Error adding word '{word}': {str(e)}")
            db.rollback()

    return added_words, errors


# API to update the dictionary
@router.get("/update-dictionary/", response_model=AddWordResponse)
def update_dictionary(db: Session = Depends(get_db)):
    """Update the main dictionary by adding words from a text file."""
    file_path = "collection.txt"  # Path to the text file

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="collection.txt file not found")

    with open(file_path, "r") as file:
        words = file.readlines()  # Read all words from the file

    added_words, errors = process_words_in_batches(words, db, batch_size=1000)

    response_message = f"Added {len(added_words)} new words to the dictionary."
    if errors:
        response_message += f" Skipped {len(errors)} words due to errors."

    return AddWordResponse(message=response_message)

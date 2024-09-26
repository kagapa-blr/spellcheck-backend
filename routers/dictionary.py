import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
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
        wordUniqueId=get_last_serial_number(db),
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


# Function to get the last word serial number from the database
def get_last_serial_number(db: Session) -> int:
    """Get the highest wordUniqueId (serial number) from the database."""
    last_serial = db.query(func.max(MainDictionary.wordUniqueId)).scalar()
    return last_serial or 0  # If no entries, start from 0


# Function to process words in batches of 1000
def process_words_in_batches(words, db: Session, starting_serial, batch_size=1000):
    added_words = []
    errors = []
    batch = []
    current_serial = starting_serial

    for word in words:
        word = word.strip()
        if not word:
            continue

        batch.append((word, current_serial))  # Store word with serial number
        current_serial += 1  # Increment serial for the next word

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
def add_words_to_db(word_data, db: Session):
    added_words = []
    errors = []

    for word, serial in word_data:
        new_word = MainDictionary(
            word=word,
            added_by_username=None,  # Set as needed
            wordUniqueId=serial,  # Use the serial number
            frequency=1
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

    # Get the highest serial number from the database
    last_serial = get_last_serial_number(db)
    next_serial = last_serial + 1  # Start from the next serial number

    with open(file_path, "r") as file:
        words = file.readlines()  # Read all words from the file

    added_words, errors = process_words_in_batches(words, db, next_serial, batch_size=1000)

    response_message = f"Added {len(added_words)} new words to the dictionary."
    if errors:
        response_message += f" Skipped {len(errors)} words due to errors."

    return AddWordResponse(message=response_message)

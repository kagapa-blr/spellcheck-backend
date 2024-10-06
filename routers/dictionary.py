from collections import Counter
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi import File, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError  # Import IntegrityError for specific handling
from sqlalchemy.orm import Session

from security.auth import get_current_user
from config.database import get_db
from dbmodels.models import MainDictionary, User
from utilities.read_file_content import filter_words_from_file, clean_words

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
def process_words_in_batches(words: List[str], db: Session, username, batch_size=1000):
    added_words = []
    errors = []

    words_counter = Counter(words)  # Count frequencies
    unique_words = list(words_counter.keys())  # Get unique words

    # Process words in batches
    for i in range(0, len(unique_words), batch_size):
        batch = unique_words[i:i + batch_size]  # Create a slice for the current batch
        added, failed = add_words_to_db(batch, db, words_counter, username)  # Pass frequency info
        added_words.extend(added)  # Collect successfully added words
        errors.extend(failed)  # Collect errors from the current batch

    return added_words, errors


# Function to add words to the database considering frequency
def add_words_to_db(words: List[str], db: Session, words_counter: Counter, username):
    added_words = []
    errors = []

    for word in words:
        frequency = words_counter[word]  # Get the frequency from Counter
        new_word = MainDictionary(
            word=word,
            frequency=frequency,
            added_by_username=username,  # Use the provided username
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


@router.post("/update/batch/", response_model=AddWordResponse)
async def update_dictionary_batch(file: UploadFile = File(...), db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_user)
                                  ):
    """
    Update the main dictionary by adding words from a text file.

    Parameters:
    - file (UploadFile): An uploaded text file containing words to be added to the dictionary.
    - db (Session): A SQLAlchemy Session object for database operations.

    Returns:
    - AddWordResponse: A response object containing a message indicating the number of new words added to the dictionary and any skipped words due to errors.
    """
    # Function will return list of missing words which needs to be added to the dictionary
    missing_words = await filter_words_from_file(file=file)
    words = clean_words(missing_words)

    # Count the frequency of each word using Counter
    word_frequency = Counter(words)
    added_words, errors = process_words_in_batches(words=words, db=db,
                                                   batch_size=1000,
                                                   username=current_user.username
                                                   )  # Use the full words list

    response_message = f"Added {len(added_words)} new words to the dictionary."
    if errors:
        response_message += f" Skipped {len(errors)} words due to errors."

    return AddWordResponse(message=response_message)

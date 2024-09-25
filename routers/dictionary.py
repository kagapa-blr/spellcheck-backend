from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import MainDictionary, UserAddedWord, Suggestion  # Import the database models
from database import get_db  # Import the database session dependency
from pydantic import BaseModel  # Import BaseModel for request/response models
from typing import List, Optional

router = APIRouter()  # Create an instance of the API router


# Request model for adding a word
class WordRequest(BaseModel):
    word: str


# Response model for checking a word
class CheckWordResponse(BaseModel):
    status: bool
    message: str


# API to check if a word exists in the main dictionary
@router.post("/check-word/", response_model=CheckWordResponse)
def check_word(request: WordRequest, db: Session = Depends(get_db)):
    """
    Check if the given word exists in the main dictionary.

    Args:
        request (WordRequest): The request body containing the word to check.
        db (Session): The database session.

    Returns:
        CheckWordResponse: A response indicating whether the word was found.
    """
    # Query the MainDictionary for the specified word
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == request.word).first()

    # Return response based on the query result
    if word_entry:
        return CheckWordResponse(status=True, message="Word found in dictionary")
    return CheckWordResponse(status=False, message="Word not found")


# Response model for suggestions
class SuggestionResponse(BaseModel):
    word: str
    frequency: int


# API to get suggestions (no authentication required)
@router.get("/suggestions/", response_model=List[SuggestionResponse])
def get_suggestions(db: Session = Depends(get_db)):
    """
    Get a list of suggestions from the database.

    Args:
        db (Session): The database session.

    Returns:
        List[SuggestionResponse]: A list of suggestion objects.
    """
    # Query all suggestions from the Suggestion table
    suggestions = db.query(Suggestion).all()
    return [{"word": suggestion.word, "frequency": suggestion.frequency} for suggestion in suggestions]


# API for users to add a word (authentication required)
@router.post("/add-word/")
def add_word(request: WordRequest, db: Session = Depends(get_db)):
    """
    Add a new word to the main dictionary or increment the frequency of an existing user-added word.

    Args:
        request (WordRequest): The request body containing the word to be added.
        db (Session): The database session.

    Returns:
        dict: A message indicating the outcome of the operation.
    """
    word = request.word

    # Query the MainDictionary to check if the word already exists
    word_entry = db.query(MainDictionary).filter(MainDictionary.word == word).first()

    if word_entry:
        # If the word exists, check if it's been added by the user
        user_word = db.query(UserAddedWord).filter(UserAddedWord.word == word).first()

        if user_word:
            # Increment the frequency count if the word was already added by the user
            user_word.frequency += 1
            message = "Word frequency updated"
        else:
            # If the word hasn't been added by the user, create a new UserAddedWord entry
            user_word = UserAddedWord(word=word, added_by=None, frequency=1)
            db.add(user_word)  # Add the new user word entry to the session
            message = "New user word added"

        db.commit()  # Commit the changes to the database
    else:
        # If the word doesn't exist, create a new entry in the MainDictionary
        new_word = MainDictionary(word=word,
                                  wordUniqueId="your_generated_hash")  # Generate a unique ID for the new word
        db.add(new_word)  # Add the new word to the session
        db.commit()  # Commit the changes to the database
        message = "Word added to dictionary"

    return {"message": message}

import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # Import for handling integrity errors
from models import User, MainDictionary, UserAddedWord, Suggestion  # Import the database models
from database import get_db  # Import the database session dependency
from pydantic import BaseModel  # Import Pydantic for data validation

router = APIRouter()  # Create an instance of the API router


# Pydantic models for request bodies
class UserCreate(BaseModel):
    username: str
    email: str
    phone: str
    password: str


class WordCreate(BaseModel):
    word: str
    added_by: int = None  # Optional field for user ID


class UserAddedWordCreate(BaseModel):
    word: str
    added_by: str  # Change to string for username


class SuggestionCreate(BaseModel):
    word: str
    frequency: int = 0  # Default frequency is 0


# API to add a new user
@router.post("/users/")
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Add a new user to the database.

    Args:
        user (UserCreate): The user data.

    Returns:
        dict: A message indicating the result of the operation.
    """
    try:
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        new_user = User(**user.dict())  # Create a new user instance
        db.add(new_user)  # Add the new user to the session
        db.commit()  # Commit the transaction
        return {"message": "User added successfully"}

    except IntegrityError:
        db.rollback()  # Rollback if there's an integrity error (e.g., duplicate entries)
        raise HTTPException(status_code=400, detail="Error adding user. Please try again.")
    except Exception as e:
        db.rollback()  # Rollback for any other exceptions
        raise HTTPException(status_code=500, detail=str(e))  # Return a 500 Internal Server Error


# API to add a new word to the main dictionary
@router.post("/main-dictionary/")
def add_word_to_dictionary(word: WordCreate, db: Session = Depends(get_db)):
    """
    Add a new word to the main dictionary.

    Args:
        word (WordCreate): The word data.

    Returns:
        dict: A message indicating the result of the operation.
    """
    try:
        existing_word = db.query(MainDictionary).filter(MainDictionary.word == word.word).first()
        if existing_word:
            raise HTTPException(status_code=400, detail="Word already exists in the dictionary")

        new_word = MainDictionary(**word.dict(), wordUniqueId="your_generated_hash")  # Create a new word instance
        db.add(new_word)  # Add the new word to the session
        db.commit()  # Commit the transaction
        return {"message": "Word added to the dictionary"}

    except IntegrityError:
        db.rollback()  # Rollback if there's an integrity error
        raise HTTPException(status_code=400, detail="Error adding word. Please try again.")
    except Exception as e:
        db.rollback()  # Rollback for any other exceptions
        raise HTTPException(status_code=500, detail=str(e))


# API to add a new user-added word

@router.post("/user-added-words/")
def add_user_added_word(user_word: UserAddedWordCreate, db: Session = Depends(get_db)):
    """
    Add a new user-added word to the database or increment its frequency if it already exists.

    Args:
        user_word (UserAddedWordCreate): The user-added word data.

    Returns:
        dict: A message indicating the result of the operation.
    """
    try:
        # Check if the word already exists in the database
        existing_word = db.query(UserAddedWord).filter(UserAddedWord.word == user_word.word).first()

        if existing_word:
            # If it exists, increment the frequency
            existing_word.frequency += 1  # Increment frequency by 1
            db.commit()  # Commit the transaction
            return {"message": f"User-added word frequency incremented successfully."}
        else:
            # If it does not exist, create a new user-added word instance
            new_user_word = UserAddedWord(**user_word.dict(), frequency=1)  # Initialize frequency to 1
            db.add(new_user_word)  # Add the new user-added word to the session
            db.commit()  # Commit the transaction
            return {"message": "User-added word added successfully with frequency 1."}

    except IntegrityError:
        db.rollback()  # Rollback if there's an integrity error
        raise HTTPException(status_code=400, detail="Error adding user-added word. Please try again.")
    except Exception as e:
        db.rollback()  # Rollback for any other exceptions
        raise HTTPException(status_code=500, detail=str(e))

# API to add a new suggestion
@router.post("/suggestions/")
def add_suggestion(suggestion: SuggestionCreate, db: Session = Depends(get_db)):
    """
    Add a new suggestion to the database.

    Args:
        suggestion (SuggestionCreate): The suggestion data.

    Returns:
        dict: A message indicating the result of the operation.
    """
    try:
        new_suggestion = Suggestion(**suggestion.dict())  # Create a new suggestion instance
        db.add(new_suggestion)  # Add the new suggestion to the session
        db.commit()  # Commit the transaction
        return {"message": "Suggestion added successfully"}

    except IntegrityError:
        db.rollback()  # Rollback if there's an integrity error
        raise HTTPException(status_code=400, detail="Error adding suggestion. Please try again.")
    except Exception as e:
        db.rollback()  # Rollback for any other exceptions
        raise HTTPException(status_code=500, detail=str(e))






@router.get("/user-added-words/refresh/")
def refresh_words(username: str, db: Session = Depends(get_db)):
    """
    Refresh words from the collection.txt file and add them to the UserAddedWord table.

    Args:
        username (str): The username of the user adding the words.
        db (Session): SQLAlchemy session.

    Returns:
        dict: A message indicating the result of the operation.
    """
    if username is None:
        raise HTTPException(status_code=400, detail="Username must be provided")

    # Check if the user exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Path to the collection.txt file in the working directory
    file_path = os.path.join(os.getcwd(), "collection.txt")

    # Check if the file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="collection.txt file not found")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            words = file.readlines()  # Read all lines from the file

        # Prepare to insert words into the database
        for word in words:
            word = word.strip()  # Remove any leading/trailing whitespace
            if word:  # Ensure the word is not empty
                new_user_word = UserAddedWord(word=word, added_by_username=username)  # Use username
                db.add(new_user_word)  # Add the new user-added word to the session

        db.commit()  # Commit the transaction
        return {"message": "User-added words refreshed successfully"}

    except IntegrityError as e:
        db.rollback()  # Rollback if there's an integrity error
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e.orig)}")
    except Exception as e:
        db.rollback()  # Rollback for any other exceptions
        raise HTTPException(status_code=500, detail=str(e))


# API to check if a word exists in the UserAddedWord table
@router.get("/user-added-words/check/")
def check_user_word(word: str, db: Session = Depends(get_db)):
    """
    Check if a word exists in the UserAddedWord table.

    Args:
        word (str): The word to check.
        db (Session): SQLAlchemy session.

    Returns:
        dict: A message indicating whether the word exists.
    """
    try:
        # Query the UserAddedWord table for the specified word
        existing_word = db.execute(select(UserAddedWord).filter(UserAddedWord.word == word)).scalars().first()

        if existing_word:
            return {"message": "Word exists in the UserAddedWord table"}
        else:
            return {"message": "Word does not exist in the UserAddedWord table"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # Return a 500 Internal Serve
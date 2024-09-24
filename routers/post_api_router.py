from fastapi import APIRouter, Depends, HTTPException
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
    added_by: int = None  # Optional field for user ID


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
    Add a new user-added word to the database.

    Args:
        user_word (UserAddedWordCreate): The user-added word data.

    Returns:
        dict: A message indicating the result of the operation.
    """
    try:
        new_user_word = UserAddedWord(**user_word.dict())  # Create a new user-added word instance
        db.add(new_user_word)  # Add the new user-added word to the session
        db.commit()  # Commit the transaction
        return {"message": "User-added word added successfully"}

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

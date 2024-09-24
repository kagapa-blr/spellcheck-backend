from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import User, MainDictionary, UserAddedWord, Suggestion  # Import the database models
from database import get_db  # Import the database session dependency

router = APIRouter()  # Create an instance of the API router

# API to get all users
@router.get("/users/")
def get_users(db: Session = Depends(get_db)):
    """
    Retrieve all users from the database.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of user objects.
    """
    users = db.query(User).all()  # Query all users
    return users

# API to get all words in the main dictionary
@router.get("/main-dictionary/")
def get_main_dictionary(db: Session = Depends(get_db)):
    """
    Retrieve all words from the main dictionary.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of words in the main dictionary.
    """
    words = db.query(MainDictionary).all()  # Query all words in the main dictionary
    return words

# API to get all user-added words
@router.get("/user-added-words/")
def get_user_added_words(db: Session = Depends(get_db)):
    """
    Retrieve all user-added words from the database.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of user-added words.
    """
    user_added_words = db.query(UserAddedWord).all()  # Query all user-added words
    return user_added_words

# API to get all suggestions
@router.get("/suggestions/")
def get_suggestions(db: Session = Depends(get_db)):
    """
    Retrieve all suggestions from the database.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of suggestion objects.
    """
    suggestions = db.query(Suggestion).all()  # Query all suggestions
    return suggestions

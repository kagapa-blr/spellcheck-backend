from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db  # Import your database session
from models import UserAddedWord

router = APIRouter()


class UserAddedWordResponse(BaseModel):
    id: int
    word: str
    added_by_username: Optional[str]
    frequency: int


class AddUserWordRequest(BaseModel):
    word: str
    added_by_username: Optional[str] = None
    frequency: Optional[int] = 1


class RemoveUserWordRequest(BaseModel):
    word: str


@router.get("/user-added-words/", response_model=List[UserAddedWordResponse])
def get_all_user_added_words(db: Session = Depends(get_db)):
    """Get all words from the user_added_words table."""
    words = db.query(UserAddedWord).all()
    if not words:  # Check if the list is empty
        raise HTTPException(status_code=404, detail="No words found in the database.")
    return words  # Return the list directly if not empty


@router.post("/user-added-words/", response_model=UserAddedWordResponse)
def add_user_added_word(request: AddUserWordRequest, db: Session = Depends(get_db)):
    """Add a new word to the user_added_words table."""
    existing_word = db.query(UserAddedWord).filter(UserAddedWord.word == request.word).first()
    if existing_word:
        raise HTTPException(status_code=400, detail="Word already exists.")

    new_word = UserAddedWord(
        word=request.word,
        added_by_username=request.added_by_username,
        frequency=request.frequency if request.frequency else 1
    )

    try:
        db.add(new_word)
        db.commit()
        db.refresh(new_word)  # Refresh to get the updated object

        # Construct the response using UserAddedWordResponse model
        return UserAddedWordResponse(
            id=new_word.id,
            word=new_word.word,
            added_by_username=new_word.added_by_username,
            frequency=new_word.frequency
        )
    except IntegrityError:
        db.rollback()  # Rollback the transaction if there's an error
        raise HTTPException(status_code=400,
                            detail="Failed to add word. The added_by_username must exist in the users table.")


@router.delete("/user-added-words/", response_model=dict)
def remove_user_added_word(request: RemoveUserWordRequest, db: Session = Depends(get_db)):
    """Remove a word from the user_added_words table."""
    word_entry = db.query(UserAddedWord).filter(UserAddedWord.word == request.word).first()
    if not word_entry:
        raise HTTPException(status_code=404, detail=f"Word '{request.word}' not found.")

    db.delete(word_entry)
    db.commit()
    return {"message": f"Word '{request.word}' removed successfully."}  # Return a success message directly

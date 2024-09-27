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
    frequency: int


class AddUserWordRequest(BaseModel):
    word: str
    frequency: Optional[int] = 1


class RemoveUserWordRequest(BaseModel):
    words: List[str]  # Accept a list


@router.get('/user-added-words/stats', response_model=int)
def get_user_added_word_stats(db: Session = Depends(get_db)):
    """Get the total number of words in the user_added_words table."""
    total_count = db.query(UserAddedWord).count()
    return total_count


@router.get("/user-added-words/", response_model=List[UserAddedWordResponse])
def get_all_user_added_words(db: Session = Depends(get_db)):
    """Get all words from the user_added_words table."""
    words = db.query(UserAddedWord).all()
    if not words:  # Check if the list is empty
        raise HTTPException(status_code=404, detail="No words found in the database.")
    return words  # Return the list directly if not empty


@router.post("/user-added-words/", response_model=UserAddedWordResponse)
def add_user_added_word(request: AddUserWordRequest, db: Session = Depends(get_db)):
    """Add a new word to the user_added_words table or update its frequency if it exists."""
    existing_word = db.query(UserAddedWord).filter(UserAddedWord.word == request.word).first()

    if existing_word:
        # Update the frequency by 1
        existing_word.frequency += 1
        db.commit()  # Commit the update

        # Refresh the updated object to get the latest values
        db.refresh(existing_word)

        # Construct the response using UserAddedWordResponse model
        return UserAddedWordResponse(
            id=existing_word.id,
            word=existing_word.word,
            frequency=existing_word.frequency
        )

    # If the word doesn't exist, create a new entry
    new_word = UserAddedWord(
        word=request.word,
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
            frequency=new_word.frequency
        )
    except IntegrityError:
        db.rollback()  # Rollback the transaction if there's an error
        raise HTTPException(status_code=400,
                            detail="Failed to add word. The added_by_username must exist in the users table.")


@router.delete("/user-added-words/remove/", response_model=dict)
def remove_user_added_words(request: RemoveUserWordRequest, db: Session = Depends(get_db)):
    """Remove a list of words from the user_added_words table."""
    removed_words = []
    not_found_words = []

    for word in request.words:
        word_entry = db.query(UserAddedWord).filter(UserAddedWord.word == word).first()
        if not word_entry:
            not_found_words.append(word)  # Collect not found words for response
        else:
            db.delete(word_entry)
            removed_words.append(word)

    db.commit()  # Commit once after processing all deletions

    # Prepare response message
    response_message = {
        "message": f"Successfully removed {len(removed_words)} words.",
        "removed": removed_words,
        "unable_to_remove": not_found_words
    }

    return response_message  # Return a detailed response

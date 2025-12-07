from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config.database import get_db
from dbmodels.models import UserAddedWord
from security.auth import get_current_user
from utilities.read_file_content import filter_missing_words_from_list, clean_single_word

router = APIRouter()


# ---------------------- Pydantic Models ---------------------- #

class UserAddedWordResponse(BaseModel):
    id: int
    word: str
    frequency: int


class AddUserWordRequest(BaseModel):
    word: str
    frequency: Optional[int] = 1


class CheckWrongWordsFromList(BaseModel):
    wordlist: List[str]


class RemoveUserWordRequest(BaseModel):
    words: List[str]


# ---------------------- Routes ---------------------- #

@router.get(
    "/user-added-words/stats",
    response_model=int,
    dependencies=[Depends(get_current_user)]
)
def get_user_added_word_stats(db: Session = Depends(get_db)):
    """Return total number of words in user_added_words."""
    return db.query(UserAddedWord).count()


@router.get(
    "/user-added-words/",
    response_model=List[UserAddedWordResponse],
    dependencies=[Depends(get_current_user)]
)
def get_all_user_added_words(db: Session = Depends(get_db)):
    """Return all user-added words. Returns [] if none exist."""
    return db.query(UserAddedWord).all() or []


@router.post(
    "/user-added-words/",
    response_model=UserAddedWordResponse
)
def add_user_added_word(request: AddUserWordRequest, db: Session = Depends(get_db)):
    """Add or update a user-added word."""
    given_word = clean_single_word(request.word)

    existing_word = db.query(UserAddedWord).filter(
        UserAddedWord.word == given_word
    ).first()

    if existing_word:
        existing_word.frequency += 1
        db.commit()
        db.refresh(existing_word)
        return existing_word

    new_word = UserAddedWord(
        word=given_word,
        frequency=request.frequency or 1
    )

    try:
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        return new_word
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Failed to add word. The added_by_username must exist in the users table."
        )


@router.delete(
    "/user-added-words/remove/",
    response_model=dict,
    dependencies=[Depends(get_current_user)]
)
def remove_user_added_words(request: RemoveUserWordRequest, db: Session = Depends(get_db)):
    """Remove multiple words from user_added_words table."""
    removed_words = []
    not_found_words = []

    for word in request.words:
        entry = db.query(UserAddedWord).filter(UserAddedWord.word == word).first()
        if entry:
            db.delete(entry)
            removed_words.append(word)
        else:
            not_found_words.append(word)

    db.commit()

    return {
        "message": f"Successfully removed {len(removed_words)} words.",
        "removed": removed_words,
        "unable_to_remove": not_found_words
    }


@router.post("/filter-wrongwords")
async def filter_wrong_words(request: CheckWrongWordsFromList):
    """Identify wrong words from provided list."""
    try:
        result = await filter_missing_words_from_list(words=request.wordlist)
        return result or []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing data: {str(e)}"
        )

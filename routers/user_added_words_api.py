from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db
from dbmodels.models import UserAddedWord
from security.auth import get_current_user
from utilities.read_file_content import filter_missing_words_from_list

router = APIRouter()


# ---------------------- Pydantic Models ---------------------- #

class UserAddedWordResponse(BaseModel):
    id: int
    word: str
    frequency: int


class AddUserWordsBulkRequest(BaseModel):
    words: List[str]


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


from sqlalchemy import func


@router.post(
    "/user-added-words/add",
    response_model=dict,
    dependencies=[Depends(get_current_user)]
)
def add_or_increment_user_added_words(
    request: AddUserWordsBulkRequest,
    db: Session = Depends(get_db)
):
    """
    Accepts only list of words from frontend.
    If word exists -> increment frequency by 1
    If not -> insert with frequency = 1
    """

    added = []
    updated = []

    # Deduplicate + sanitize
    unique_words = {w.strip() for w in request.words if w and w.strip()}

    for word in unique_words:
        entry = (
            db.query(UserAddedWord)
            .filter(func.lower(UserAddedWord.word) == word.lower())
            .first()
        )

        if entry:
            entry.frequency += 1
            updated.append(entry.word)
        else:
            new_entry = UserAddedWord(word=word, frequency=1)
            db.add(new_entry)
            added.append(word)

    db.commit()

    return {
        "message": "User added words processed successfully",
        "added_count": len(added),
        "updated_count": len(updated),
        "added_words": added,
        "updated_words": updated,
    }

# @router.get(
#     "/user-added-words/",
#     response_model=List[UserAddedWordResponse],
#     dependencies=[Depends(get_current_user)]
# )
# def get_all_user_added_words(db: Session = Depends(get_db)):
#     """Return all user-added words. Returns [] if none exist."""
#     return db.query(UserAddedWord).all() or []


from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session


@router.get("/user-added-words/")
def get_user_added_words(
        limit: int = 10,
        offset: int = 0,
        search: str | None = None,
        db: Session = Depends(get_db),
):
    query = db.query(UserAddedWord)

    if search:
        query = query.filter(UserAddedWord.word.ilike(f"%{search}%"))

    total = query.count()

    data = query.order_by(UserAddedWord.id.desc()).offset(offset).limit(limit).all()

    return {
        "data": data,
        "total": total
    }


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

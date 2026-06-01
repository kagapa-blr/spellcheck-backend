from __future__ import annotations

from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from config.database import get_db
from dbmodels.models import UserAddedWord
from security.auth import get_current_user
from utilities.read_file_content import filter_missing_words_from_list

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------- Pydantic Models ---------------------- #

class UserAddedWordResponse(BaseModel):
    id: int
    word: str
    frequency: int


class AddUserWordsBulkRequest(BaseModel):
    words: list[str]


class AddUserWordRequest(BaseModel):
    word: str
    frequency: Optional[int] = 1


class CheckWrongWordsFromList(BaseModel):
    wordlist: list[str]


class RemoveUserWordRequest(BaseModel):
    words: list[str]


# ---------------------- Routes ---------------------- #

@router.get(
    "/user-added-words/stats",
    response_model=int,
    dependencies=[Depends(get_current_user)]
)
def get_user_added_word_stats(db: Session = Depends(get_db)):
    """Return total number of words in user_added_words."""
    try:
        count = db.query(UserAddedWord).count()
        logger.info(f"User added words stats: {count}")
        return count
    except Exception as e:
        logger.error(f"Error getting user added word stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving stats")


from sqlalchemy import func


@router.post(
    "/user-added-words/add",
    response_model=dict
)
def add_or_increment_user_added_words(
    request: AddUserWordsBulkRequest,
    db: Session = Depends(get_db)
):
    """
    Public endpoint - Accepts list of words from users.
    If word exists -> increment frequency by 1
    If not -> insert with frequency = 1
    """

    added = []
    updated = []

    # Deduplicate + sanitize
    unique_words = {w.strip() for w in request.words if w and w.strip()}

    try:
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
                try:
                    new_entry = UserAddedWord(word=word, frequency=1)
                    db.add(new_entry)
                    added.append(word)
                except IntegrityError:
                    # Handle race condition where word was added between check and insert
                    db.rollback()
                    entry = (
                        db.query(UserAddedWord)
                        .filter(func.lower(UserAddedWord.word) == func.lower(word))
                        .first()
                    )
                    if entry:
                        entry.frequency += 1
                        updated.append(entry.word)

        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error adding user words: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing words: Database integrity error")
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding user words: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing words: {str(e)}")

    message = f"User added words processed successfully: {len(added)} words added, {len(updated)} words updated"
    
    return {
        "message": message,
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


from fastapi import Depends
from sqlalchemy.orm import Session


@router.get("/user-added-words/")
def get_user_added_words(
        limit: int = 10,
        offset: int = 0,
        search: Optional[str] = None,
        db: Session = Depends(get_db),
):
    """Get list of user added words with pagination and search."""
    try:
        query = db.query(UserAddedWord)

        if search:
            search_term = f"%{search}%"
            query = query.filter(UserAddedWord.word.ilike(search_term))
            logger.info(f"Searching user added words for: {search}")

        total = query.count()
        logger.info(f"Total user added words found: {total}")

        data = query.order_by(UserAddedWord.id.desc()).offset(offset).limit(limit).all()

        return {
            "data": data,
            "total": total
        }
    except Exception as e:
        logger.error(f"Error getting user added words: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving user added words")


@router.delete(
    "/user-added-words/remove/",
    response_model=dict,
    dependencies=[Depends(get_current_user)]
)
def remove_user_added_words(request: RemoveUserWordRequest, db: Session = Depends(get_db)):
    """Remove multiple words from user_added_words table."""
    try:
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
        logger.info(f"Removed {len(removed_words)} user added words: {removed_words}")

        return {
            "message": f"Successfully removed {len(removed_words)} words.",
            "removed": removed_words,
            "unable_to_remove": not_found_words
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing user added words: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error removing words")


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

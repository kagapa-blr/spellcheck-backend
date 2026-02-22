from collections import Counter
from typing import Optional, List
from sqlalchemy.dialects.mysql import insert
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from config.database import get_db
from dbmodels.models import MainDictionary, User
from security.auth import get_current_user
from utilities.read_file_content import filter_words_from_file, clean_words

router = APIRouter()


# ---------------------- Pydantic Models ---------------------- #

class WordEntry(BaseModel):
    word: str
    frequency: Optional[int] = 1


class WordRequest(BaseModel):
    words: List[WordEntry]
    added_by_username: Optional[str] = None


class AddWordResponse(BaseModel):
    message: str
    added_count: int = 0
    updated_count: int = 0
    added_words: List[str] = []
    updated_words: List[str] = []


# ---------------------- APIs ---------------------- #

@router.post("/check-word/", response_model=AddWordResponse)
def check_word(request: WordRequest, db: Session = Depends(get_db)):
    words = [w.word.lower() for w in request.words]
    existing = db.query(MainDictionary).filter(
        func.lower(MainDictionary.word).in_(words)
    ).all()

    found_words = [w.word for w in existing]

    return AddWordResponse(
        message="Words found" if found_words else "No words found",
        added_words=found_words
    )



@router.post("/add-words/", response_model=AddWordResponse)
def add_or_increment_words(
    request: WordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not request.words:
        raise HTTPException(status_code=400, detail="No words provided")

    cleaned_entries = [
        (entry.word.strip(), entry.frequency or 1)
        for entry in request.words
        if entry.word and entry.word.strip()
    ]

    added_words = []
    updated_words = []

    for word, freq in cleaned_entries:
        stmt = insert(MainDictionary).values(
            word=word,
            frequency=freq,
            added_by_username=request.added_by_username or current_user.username
        ).on_duplicate_key_update(
            frequency=MainDictionary.frequency + freq
        )

        result = db.execute(stmt)
        db.flush()  # ensure result is applied immediately

        # Check if row was inserted or updated
        if result.lastrowid:
            added_words.append(word)
        else:
            updated_words.append(word)

    db.commit()

    return AddWordResponse(
        message="Words processed successfully",
        added_count=len(added_words),
        updated_count=len(updated_words),
        added_words=added_words,
        updated_words=updated_words
    )

@router.put("/update-word/", response_model=AddWordResponse, dependencies=[Depends(get_current_user)])
def update_word(request: WordRequest, db: Session = Depends(get_db)):
    if len(request.words) != 1:
        raise HTTPException(status_code=400, detail="Update requires exactly one word")

    entry = request.words[0]

    db_word = db.query(MainDictionary).filter(
        func.lower(MainDictionary.word) == entry.word.lower()
    ).first()

    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")

    db_word.frequency += entry.frequency or 1
    db.commit()

    return AddWordResponse(message="Word updated successfully")


@router.delete("/delete-word/", response_model=AddWordResponse, dependencies=[Depends(get_current_user)])
def delete_word(request: WordRequest, db: Session = Depends(get_db)):
    if len(request.words) != 1:
        raise HTTPException(status_code=400, detail="Delete requires exactly one word")

    word = request.words[0].word

    db_word = db.query(MainDictionary).filter(
        func.lower(MainDictionary.word) == word.lower()
    ).first()

    if not db_word:
        raise HTTPException(status_code=404, detail="Word not found")

    db.delete(db_word)
    db.commit()

    return AddWordResponse(message="Word deleted successfully")


@router.post("/update/batch/", response_model=AddWordResponse)
async def update_dictionary_batch(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    missing_words = await filter_words_from_file(file=file)
    words = clean_words(missing_words)

    counter = Counter(words)
    unique_words = list(counter.keys())

    added_words = []
    updated_words = []

    existing_entries = db.query(MainDictionary).filter(
        func.lower(MainDictionary.word).in_([w.lower() for w in unique_words])
    ).all()

    existing_map = {e.word.lower(): e for e in existing_entries}

    for word, freq in counter.items():
        key = word.lower()
        if key in existing_map:
            existing_map[key].frequency += freq
            updated_words.append(word)
        else:
            db.add(MainDictionary(
                word=word,
                frequency=freq,
                added_by_username=current_user.username
            ))
            added_words.append(word)

    db.commit()

    return AddWordResponse(
        message="Batch dictionary update completed",
        added_count=len(added_words),
        updated_count=len(updated_words),
        added_words=added_words[:50],  # limit large response
        updated_words=updated_words[:50]
    )

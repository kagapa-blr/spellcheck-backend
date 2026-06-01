from collections import Counter
from typing import Optional, List
from sqlalchemy.dialects.mysql import insert
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
import logging

from config.database import get_db
from dbmodels.models import MainDictionary, User, UserAddedWord
from security.auth import get_current_user, admin_auth_required
from utilities.read_file_content import filter_words_from_file, clean_words

logger = logging.getLogger(__name__)
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
    try:
        if not request.words:
            logger.warning("Empty word list provided for check-word endpoint")
            return AddWordResponse(
                message="No words provided",
                added_words=[]
            )
        
        words = [w.word.lower() for w in request.words]
        logger.info(f"Checking {len(words)} words in dictionary")
        
        existing = db.query(MainDictionary).filter(
            func.lower(MainDictionary.word).in_(words)
        ).all()

        found_words = [w.word for w in existing]
        logger.info(f"Found {len(found_words)} existing words")

        return AddWordResponse(
            message="Words found" if found_words else "No words found",
            added_words=found_words
        )
    except Exception as e:
        logger.error(f"Error checking words: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error checking words")



@router.post("/add-words/", response_model=AddWordResponse)
def add_or_increment_words(
    request: WordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.exc import IntegrityError
    
    if not request.words:
        raise HTTPException(status_code=400, detail="No words provided")

    cleaned_entries = [
        (entry.word.strip(), entry.frequency or 1)
        for entry in request.words
        if entry.word and entry.word.strip()
    ]

    added_words = []
    updated_words = []

    try:
        for word, freq in cleaned_entries:
            # Check if word already exists (case-insensitive for better Kannada support)
            existing = db.query(MainDictionary).filter(
                func.lower(MainDictionary.word) == func.lower(word)
            ).first()

            if existing:
                # Update frequency
                existing.frequency += freq
                updated_words.append(word)
            else:
                try:
                    # Insert new word
                    new_entry = MainDictionary(
                        word=word,
                        frequency=freq,
                        added_by_username=request.added_by_username or current_user.username
                    )
                    db.add(new_entry)
                    added_words.append(word)
                except IntegrityError:
                    # If duplicate key error despite check, update it
                    db.rollback()
                    existing = db.query(MainDictionary).filter(
                        func.lower(MainDictionary.word) == func.lower(word)
                    ).first()
                    if existing:
                        existing.frequency += freq
                        updated_words.append(word)

        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error adding words: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing words: Database integrity error")
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding words: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing words: {str(e)}")

    # Create detailed message showing what was done
    message = f"Words processed successfully: {len(added_words)} words added, {len(updated_words)} words updated"
    
    return AddWordResponse(
        message=message,
        added_count=len(added_words),
        updated_count=len(updated_words),
        added_words=added_words,
        updated_words=updated_words
    )

@router.put("/update-word/", response_model=AddWordResponse, dependencies=[Depends(get_current_user)])
def update_word(request: WordRequest, db: Session = Depends(get_db)):
    try:
        if len(request.words) != 1:
            raise HTTPException(status_code=400, detail="Update requires exactly one word")

        entry = request.words[0]
        logger.info(f"Updating word: {entry.word}")

        db_word = db.query(MainDictionary).filter(
            func.lower(MainDictionary.word) == entry.word.lower()
        ).first()

        if not db_word:
            logger.warning(f"Word not found for update: {entry.word}")
            raise HTTPException(status_code=404, detail="Word not found")

        db_word.frequency += entry.frequency or 1
        db.commit()
        
        logger.info(f"Word updated successfully: {entry.word}")

        return AddWordResponse(message="Word updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating word: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error updating word")


@router.delete("/delete-word/", response_model=AddWordResponse, dependencies=[Depends(get_current_user)])
def delete_word(request: WordRequest, db: Session = Depends(get_db)):
    try:
        if len(request.words) != 1:
            raise HTTPException(status_code=400, detail="Delete requires exactly one word")

        word = request.words[0].word
        logger.info(f"Deleting word: {word}")

        db_word = db.query(MainDictionary).filter(
            func.lower(MainDictionary.word) == word.lower()
        ).first()

        if not db_word:
            logger.warning(f"Word not found for deletion: {word}")
            raise HTTPException(status_code=404, detail="Word not found")

        db.delete(db_word)
        db.commit()
        
        logger.info(f"Word deleted successfully: {word}")

        return AddWordResponse(message="Word deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting word: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error deleting word")


@router.post("/update/batch/", response_model=AddWordResponse)
async def update_dictionary_batch(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.dialects.mysql import insert as mysql_insert
    
    missing_words = await filter_words_from_file(file=file)
    words = clean_words(missing_words)

    counter = Counter(words)
    unique_words = list(counter.keys())

    added_words = []
    updated_words = []

    try:
        # Fetch existing words with their exact stored form
        existing_entries = db.query(MainDictionary).all()
        existing_map = {e.word.lower(): e for e in existing_entries}

        # Separate words into add and update lists
        words_to_update = []
        words_to_add = []

        for word in unique_words:
            key = word.lower()
            freq = counter[word]
            
            if key in existing_map:
                words_to_update.append({
                    'word_key': key,
                    'word': word,
                    'freq': freq,
                    'existing_word': existing_map[key].word
                })
            else:
                words_to_add.append({
                    'word': word,
                    'frequency': freq,
                    'added_by_username': current_user.username
                })

        # Update existing words
        for item in words_to_update:
            existing = existing_map[item['word_key']]
            existing.frequency += item['freq']
            updated_words.append(item['word'])

        # Insert new words using ON DUPLICATE KEY UPDATE for safety
        if words_to_add:
            for batch_data in words_to_add:
                stmt = mysql_insert(MainDictionary).values(
                    word=batch_data['word'],
                    frequency=batch_data['frequency'],
                    added_by_username=batch_data['added_by_username']
                ).on_duplicate_key_update(
                    frequency=MainDictionary.frequency + batch_data['frequency']
                )
                
                try:
                    db.execute(stmt)
                    added_words.append(batch_data['word'])
                except IntegrityError:
                    # If still fails, treat as update
                    db.rollback()
                    existing = db.query(MainDictionary).filter(
                        func.lower(MainDictionary.word) == func.lower(batch_data['word'])
                    ).first()
                    if existing:
                        existing.frequency += batch_data['frequency']
                        updated_words.append(batch_data['word'])
                        if batch_data['word'] in added_words:
                            added_words.remove(batch_data['word'])

        db.commit()
        logger.info(f"Batch update completed: {len(added_words)} added, {len(updated_words)} updated")

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error during batch commit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing batch: Database integrity error. Processed {len(added_words)} additions, {len(updated_words)} updates."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

    message = f"Batch dictionary update completed: {len(added_words)} words added, {len(updated_words)} words updated"
    
    return AddWordResponse(
        message=message,
        added_count=len(added_words),
        updated_count=len(updated_words),
        added_words=added_words[:50],  # limit large response
        updated_words=updated_words[:50]
    )


@router.post("/merge-user-words/", response_model=AddWordResponse, dependencies=[Depends(admin_auth_required)])
def merge_user_added_words_to_main_dict(db: Session = Depends(get_db)):
    """
    Admin endpoint: Merge all user-added words to main dictionary.
    This moves words from user_added_words table to main_dictionary.
    """
    try:
        # Fetch all user-added words
        user_words = db.query(UserAddedWord).all()
        
        if not user_words:
            return AddWordResponse(
                message="No user-added words to merge",
                added_count=0,
                updated_count=0
            )

        merged_words = []
        updated_words = []

        for user_word in user_words:
            # Check if word already exists in main dictionary (case-insensitive)
            existing = db.query(MainDictionary).filter(
                func.lower(MainDictionary.word) == func.lower(user_word.word)
            ).first()

            if existing:
                # Update frequency by adding user word frequency
                existing.frequency += user_word.frequency
                updated_words.append(user_word.word)
            else:
                # Add new word to main dictionary
                new_entry = MainDictionary(
                    word=user_word.word,
                    frequency=user_word.frequency,
                    added_by_username="system_merged"
                )
                db.add(new_entry)
                merged_words.append(user_word.word)

        # Commit changes to main_dictionary
        db.commit()

        # Delete all user-added words after successful merge
        db.query(UserAddedWord).delete()
        db.commit()

        message = f"User-added words merged successfully: {len(merged_words)} words added to main dictionary, {len(updated_words)} words updated"
        
        return AddWordResponse(
            message=message,
            added_count=len(merged_words),
            updated_count=len(updated_words),
            added_words=merged_words[:100],
            updated_words=updated_words[:100]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error merging user words: {str(e)}")

from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import exists, delete
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.config.logger_config import setup_logger
from app.dbmodels.models import MainDictionary, UserAddedWord, User
from app.utils.kannada_word_clean import clean_kannada_word

logger = setup_logger(__name__)

# ======================================================
# MAIN DICTIONARY SERVICE
# ======================================================
KANNADA_PATTERN = re.compile(r"^[\u0C80-\u0CFF]+$")


class MainDictionaryService:

    @staticmethod
    def add_words(
            db: Session,
            words: list[dict[str, Any]],
            added_by_username: Optional[str] = None,
    ) -> dict:

        added_words = []
        updated_words = []

        # `added_by_username` is mandatory for main dictionary operations.
        if not added_by_username:
            logger.error(
                "added_by_username is required for adding main dictionary words"
            )
            raise ValueError("added_by_username is required")
        logger.info(f"Total Words given for Adding to Main dictionary : {len(words)}")
        username_to_use: str
        try:
            user = (
                db.query(User)
                .filter(func.lower(User.username) == added_by_username.lower())
                .first()
            )
            if not user:
                logger.error(
                    f"Provided added_by_username '{added_by_username}' not found"
                )
                raise ValueError(f"added_by_username '{added_by_username}' not found")

            username_to_use = user.username
        except ValueError:
            # re-raise validation errors
            raise
        except Exception:
            logger.exception("Error verifying added_by_username")
            raise

        try:
            # Aggregate input words (clean and sum frequencies for duplicates)
            aggregated: dict[str, int] = {}
            for item in words:
                raw = item.get("word", "")
                try:
                    word = clean_kannada_word(raw)
                except Exception as e:
                    logger.warning(f"Skipping invalid main dictionary word '{raw}': {e}")
                    continue

                frequency = int(item.get("frequency", 1) or 1)
                key = word.strip()
                if not key:
                    continue
                aggregated[key] = aggregated.get(key, 0) + frequency

            if not aggregated:
                return {
                    "added_count": 0,
                    "updated_count": 0,
                    "added_words": [],
                    "updated_words": [],
                }

            # Prepare lowercase list for existing lookup
            input_lowers = [w.lower() for w in aggregated.keys()]

            existing_rows = (
                db.query(MainDictionary)
                .filter(func.lower(MainDictionary.word).in_(input_lowers))
                .all()
            )

            existing_lower_set = {r.word.lower() for r in existing_rows}

            # Build bulk insert rows
            table = MainDictionary.__table__
            insert_rows = [
                {"word": w, "frequency": f, "added_by_username": username_to_use}
                for w, f in aggregated.items()
            ]

            # MySQL upsert: add frequencies on duplicate key
            insert_stmt = mysql_insert(table).values(insert_rows)
            upsert_stmt = insert_stmt.on_duplicate_key_update(
                frequency=(table.c.frequency + insert_stmt.inserted.frequency)
            )

            try:
                db.execute(upsert_stmt)
                db.commit()
            except Exception:
                db.rollback()
                # Fallback to row-by-row logic if dialect or unexpected error
                logger.exception("Bulk upsert failed, falling back to row-by-row merge")

                for w, f in aggregated.items():
                    lw = w.lower()
                    if lw in existing_lower_set:
                        db.query(MainDictionary).filter(
                            func.lower(MainDictionary.word) == lw
                        ).update({MainDictionary.frequency: MainDictionary.frequency + f}, synchronize_session=False)
                    else:
                        db.add(MainDictionary(word=w, frequency=f, added_by_username=username_to_use))

                db.commit()

            # Fetch final rows to report added/updated and frequencies
            final_rows = (
                db.query(MainDictionary)
                .filter(func.lower(MainDictionary.word).in_(input_lowers))
                .all()
            )

            added_words = []
            updated_words = []

            for row in final_rows:
                if row.word.lower() in existing_lower_set:
                    updated_words.append({"word": row.word, "frequency": row.frequency})
                else:
                    added_words.append({"word": row.word, "frequency": row.frequency})

            return {
                "added_count": len(added_words),
                "updated_count": len(updated_words),
                "added_words": added_words,
                "updated_words": updated_words,
            }

        except Exception:
            db.rollback()
            logger.exception("Error adding words to main dictionary")
            raise

    @staticmethod
    def word_exists(db: Session, word: str) -> Optional[bool]:
        try:
            cleaned = clean_kannada_word(word)
        except Exception as e:
            return False
        stmt = select(
            exists().where(func.lower(MainDictionary.word) == cleaned.lower())
        )
        return db.scalar(stmt)

    @staticmethod
    def get_count(db: Session) -> int:
        return db.query(func.count(MainDictionary.id)).scalar() or 0

    @staticmethod
    def delete_words(db: Session, words: list[str]) -> dict:
        try:
            lowered = [w.lower() for w in words]

            entries = (
                db.query(MainDictionary)
                .filter(func.lower(MainDictionary.word).in_(lowered))
                .all()
            )

            if not entries:
                return {"deleted_count": 0, "deleted_words": []}

            deleted_words = [e.word for e in entries]

            for entry in entries:
                db.delete(entry)

            db.commit()

            return {"deleted_count": len(deleted_words), "deleted_words": deleted_words}

        except Exception:
            db.rollback()
            logger.exception("Error deleting words from main dictionary")
            raise

    @staticmethod
    def check_word(db: Session, word: str) -> Optional[dict]:
        entry = (
            db.query(MainDictionary)
            .filter(func.lower(MainDictionary.word) == word.lower())
            .first()
        )
        if not entry:
            return None

        return {"word": entry.word, "frequency": entry.frequency}

    @staticmethod
    def check_words(db: Session, words: list[str]) -> list[dict]:

        lowered = [w.lower() for w in words]

        entries = (
            db.query(MainDictionary)
            .filter(func.lower(MainDictionary.word).in_(lowered))
            .all()
        )

        return [{"word": e.word, "frequency": e.frequency} for e in entries]

    @staticmethod
    def get_words(
            db: Session,
            limit: int = 50,
            offset: int = 0,
            search: Optional[str] = None,
    ) -> dict:

        query = db.query(MainDictionary)

        if search:
            query = query.filter(
                func.lower(MainDictionary.word).like(f"%{search.lower()}%")
            )

        total_count = query.count()

        entries = (
            query.order_by(MainDictionary.word.asc()).offset(offset).limit(limit).all()
        )

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "words": [
                {
                    "word": e.word,
                    "frequency": e.frequency,
                    "added_by_username": e.added_by_username,
                }
                for e in entries
            ],
        }

    @staticmethod
    def find_missing_words(db: Session, words: list[str]) -> dict:

        try:
            # normalize input once
            input_words = set(words)

            # fetch existing words only from input set
            existing_rows = (
                db.query(MainDictionary.word)
                .filter(MainDictionary.word.in_(input_words))
                .all()
            )

            existing_set = {row.word for row in existing_rows}

            missing_words = list(input_words - existing_set)

            return {
                "total_input": len(words),
                "existing_count": len(existing_set),
                "missing_count": len(missing_words),
                "missing_words": missing_words,
            }

        except Exception:
            logger.exception("Error finding missing Kannada words")
            raise

    @staticmethod
    def approve_user_words(
            db: Session,
            words: list[str],
            approved_by_username: str,
    ) -> dict:
        """
        Approve user-added words by moving them into the main dictionary.

        - Existing main dictionary words have their frequency increased.
        - New words are inserted into the main dictionary.
        - Approved words are removed from UserAddedWord.
        """

        if not approved_by_username:
            raise ValueError("approved_by_username is required")

        try:
            user = (
                db.query(User)
                .filter(func.lower(User.username) == approved_by_username.lower())
                .first()
            )

            if not user:
                raise ValueError(
                    f"approved_by_username '{approved_by_username}' not found"
                )

            username_to_use = user.username

            lowered_words = list(
                {word.strip().lower() for word in words if word and word.strip()}
            )

            if not lowered_words:
                return {
                    "approved_count": 0,
                    "approved_words": [],
                }

            user_words = (
                db.query(UserAddedWord)
                .filter(func.lower(UserAddedWord.word).in_(lowered_words))
                .all()
            )

            if not user_words:
                return {
                    "approved_count": 0,
                    "approved_words": [],
                }

            existing_main_words = (
                db.query(MainDictionary)
                .filter(
                    func.lower(MainDictionary.word).in_(
                        [uw.word.lower() for uw in user_words]
                    )
                )
                .all()
            )

            main_word_map = {row.word.lower(): row for row in existing_main_words}

            approved_words = []
            added_count = 0
            updated_count = 0

            for user_word in user_words:

                existing_main = main_word_map.get(user_word.word.lower())

                if existing_main:
                    existing_main.frequency += user_word.frequency
                    updated_count += 1

                else:
                    new_word = MainDictionary(
                        word=user_word.word,
                        frequency=user_word.frequency,
                        added_by_username=username_to_use,
                    )

                    db.add(new_word)
                    added_count += 1

                approved_words.append(
                    {
                        "word": user_word.word,
                        "frequency": user_word.frequency,
                    }
                )

                db.delete(user_word)

            db.commit()

            logger.info(
                f"User words approval completed. "
                f"Approved={len(approved_words)}, "
                f"Added={added_count}, "
                f"Updated={updated_count}, "
                f"Deleted={len(approved_words)}, "
                f"ApprovedBy={username_to_use}"
            )

            return {
                "approved_count": len(approved_words),
                "approved_words": approved_words,
            }

        except Exception:
            db.rollback()
            logger.exception("Error approving user words into main dictionary")
            raise

    @staticmethod
    def is_valid_kannada_word(word: str) -> bool:
        if not word:
            return False

        cleaned = clean_kannada_word(word)

        if not cleaned:
            return False

        return True

    @staticmethod
    def clean_dictionary(
            db: Session,
            batch_size: int = 5000,
    ):

        deleted_count = 0
        updated_count = 0
        checked_count = 0

        deleted_words = []

        last_id = 0

        while True:

            items = (
                db.query(MainDictionary)
                .filter(MainDictionary.id > last_id)
                .order_by(MainDictionary.id)
                .limit(batch_size)
                .all()
            )

            if not items:
                break

            invalid_ids = []

            for item in items:

                checked_count += 1

                last_id = item.id

                original_word = item.word

                cleaned_word = clean_kannada_word(
                    original_word
                )

                # Invalid word -> delete
                if not cleaned_word:

                    invalid_ids.append(item.id)

                    if len(deleted_words) < 100:
                        deleted_words.append(original_word)


                # Normalized / cleaned word changed
                elif cleaned_word != original_word:

                    item.word = cleaned_word
                    updated_count += 1

            # Delete current batch invalid words
            if invalid_ids:
                db.execute(
                    delete(MainDictionary)
                    .where(
                        MainDictionary.id.in_(invalid_ids)
                    )
                )

                deleted_count += len(invalid_ids)

            # Commit every batch
            db.commit()

        return {
            "total_checked": checked_count,
            "deleted_count": deleted_count,
            "updated_count": updated_count,
            "sample_deleted_words": deleted_words,
            "batch_size": batch_size,
        }


# ======================================================
# USER ADDED WORD SERVICE
# ======================================================


class UserAddedWordService:

    @staticmethod
    def add_words(db: Session, words: list[dict[str, Any]]) -> dict:
        added_words = []
        updated_words = []

        try:
            # Aggregate input words to sum frequencies for duplicates
            aggregated: dict[str, int] = {}
            for item in words:
                raw = item.get("word", "")
                try:
                    word = clean_kannada_word(raw)
                except Exception as e:
                    logger.warning(f"Skipping invalid user-added word '{raw}': {e}")
                    continue

                frequency = int(item.get("frequency", 1) or 1)
                key = word.strip()
                if not key:
                    continue
                aggregated[key] = aggregated.get(key, 0) + frequency

            if not aggregated:
                return {
                    "added_count": 0,
                    "updated_count": 0,
                    "added_words": [],
                    "updated_words": [],
                }

            input_lowers = [w.lower() for w in aggregated.keys()]

            existing_rows = (
                db.query(UserAddedWord)
                .filter(func.lower(UserAddedWord.word).in_(input_lowers))
                .all()
            )

            existing_map = {r.word.lower(): r for r in existing_rows}

            # Prepare bulk update mappings and insert mappings
            update_mappings = []
            insert_mappings = []

            for w, f in aggregated.items():
                lw = w.lower()
                if lw in existing_map:
                    existing = existing_map[lw]
                    update_mappings.append({"id": existing.id, "frequency": existing.frequency + f})
                else:
                    insert_mappings.append({"word": w, "frequency": f})

            if update_mappings:
                db.bulk_update_mappings(UserAddedWord, update_mappings)

            if insert_mappings:
                db.bulk_insert_mappings(UserAddedWord, insert_mappings)

            db.commit()

            # Build response lists
            for mapping in insert_mappings:
                added_words.append({"word": mapping["word"], "frequency": mapping["frequency"]})

            for m in update_mappings:
                # mapped id -> fetch word to return consistent casing
                row = db.get(UserAddedWord, m["id"])
                if row:
                    updated_words.append({"word": row.word, "frequency": row.frequency})

            return {
                "added_count": len(added_words),
                "updated_count": len(updated_words),
                "added_words": added_words,
                "updated_words": updated_words,
            }

        except Exception:
            db.rollback()
            logger.exception("Error adding user words")
            raise

    @staticmethod
    def get_count(db: Session) -> int:
        return db.query(func.count(UserAddedWord.id)).scalar() or 0

    @staticmethod
    def delete_words(db: Session, words: list[str]) -> dict:

        try:
            lowered = [w.lower() for w in words]

            entries = (
                db.query(UserAddedWord)
                .filter(func.lower(UserAddedWord.word).in_(lowered))
                .all()
            )

            if not entries:
                return {"deleted_count": 0, "deleted_words": []}

            deleted_words = [e.word for e in entries]

            for entry in entries:
                db.delete(entry)

            db.commit()

            return {"deleted_count": len(deleted_words), "deleted_words": deleted_words}

        except Exception:
            db.rollback()
            logger.exception("Error deleting user words")
            raise

    @staticmethod
    def check_word(db: Session, word: str) -> Optional[dict]:

        entry = (
            db.query(UserAddedWord)
            .filter(func.lower(UserAddedWord.word) == word.lower())
            .first()
        )

        if not entry:
            return None

        return {"word": entry.word, "frequency": entry.frequency}

    @staticmethod
    def check_words(db: Session, words: list[str]) -> list[dict]:

        lowered = [w.lower() for w in words]

        entries = (
            db.query(UserAddedWord)
            .filter(func.lower(UserAddedWord.word).in_(lowered))
            .all()
        )

        return [{"word": e.word, "frequency": e.frequency} for e in entries]

    @staticmethod
    def get_words(
            db: Session,
            limit: int = 50,
            offset: int = 0,
            search: Optional[str] = None,
    ) -> dict:

        query = db.query(UserAddedWord)

        if search:
            query = query.filter(
                func.lower(UserAddedWord.word).like(f"%{search.lower()}%")
            )

        total_count = query.count()

        entries = (
            query.order_by(UserAddedWord.word.asc()).offset(offset).limit(limit).all()
        )

        return {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "words": [
                {
                    "word": e.word,
                    "frequency": e.frequency,
                }
                for e in entries
            ],
        }

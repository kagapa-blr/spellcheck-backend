from __future__ import annotations

from typing import Any

from sqlalchemy import exists
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.logger_config import setup_logger
from app.dbmodels.models import MainDictionary, UserAddedWord, User
from app.utils.kannada_word_clean import clean_kannada_word

logger = setup_logger(__name__)


# ======================================================
# MAIN DICTIONARY SERVICE
# ======================================================


class MainDictionaryService:

    @staticmethod
    def add_words(
        db: Session,
        words: list[dict[str, Any]],
        added_by_username: str | None = None,
    ) -> dict:

        added_words = []
        updated_words = []

        # `added_by_username` is mandatory for main dictionary operations.
        if not added_by_username:
            logger.error(
                "added_by_username is required for adding main dictionary words"
            )
            raise ValueError("added_by_username is required")

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
            # Normalize and collect all cleaned input words first
            cleaned_items: list[tuple[str, int]] = []
            for item in words:
                raw = item.get("word", "")
                try:
                    word = clean_kannada_word(raw)
                except Exception as e:
                    logger.warning(
                        f"Skipping invalid main dictionary word '{raw}': {e}"
                    )
                    continue

                frequency = int(item.get("frequency", 1) or 1)
                cleaned_items.append((word, frequency))

            if not cleaned_items:
                return {
                    "added_count": 0,
                    "updated_count": 0,
                    "added_words": [],
                    "updated_words": [],
                }

            # Fetch existing rows for all input words in one query
            input_words_lower = [w.lower() for w, _ in cleaned_items]
            existing_rows = (
                db.query(MainDictionary)
                .filter(func.lower(MainDictionary.word).in_(input_words_lower))
                .all()
            )

            existing_map = {row.word.lower(): row for row in existing_rows}

            # Track newly added words within this transaction to avoid duplicate inserts
            new_map: dict[str, MainDictionary] = {}

            for word, frequency in cleaned_items:
                lw = word.lower()

                if lw in existing_map:
                    row = existing_map[lw]
                    row.frequency += frequency
                    updated_words.append({"word": row.word, "frequency": row.frequency})
                elif lw in new_map:
                    row = new_map[lw]
                    row.frequency += frequency
                    updated_words.append({"word": row.word, "frequency": row.frequency})
                else:
                    row = MainDictionary(
                        word=word,
                        frequency=frequency,
                        added_by_username=username_to_use,
                    )
                    db.add(row)
                    new_map[lw] = row
                    added_words.append({"word": word, "frequency": frequency})

            try:
                db.commit()
            except IntegrityError:
                # Fallback for race conditions / duplicate key errors: update existing rows
                db.rollback()

                for lw, row in new_map.items():
                    try:
                        # First try to update existing row (atomic)
                        updated_count = (
                            db.query(MainDictionary)
                            .filter(func.lower(MainDictionary.word) == lw)
                            .update(
                                {
                                    MainDictionary.frequency: MainDictionary.frequency
                                    + row.frequency
                                },
                                synchronize_session=False,
                            )
                        )

                        if updated_count:
                            existing = (
                                db.query(MainDictionary)
                                .filter(func.lower(MainDictionary.word) == lw)
                                .first()
                            )
                            if existing:
                                updated_words.append(
                                    {
                                        "word": existing.word,
                                        "frequency": existing.frequency,
                                    }
                                )
                            # continue to next entry
                            continue

                        # No existing row updated — try to insert and commit immediately.
                        try:
                            db.add(
                                MainDictionary(
                                    word=row.word,
                                    frequency=row.frequency,
                                    added_by_username=row.added_by_username,
                                )
                            )
                            db.commit()
                            added_words.append(
                                {"word": row.word, "frequency": row.frequency}
                            )
                        except IntegrityError:
                            # Another transaction inserted concurrently — rollback and update instead
                            db.rollback()
                            db.query(MainDictionary).filter(
                                func.lower(MainDictionary.word) == lw
                            ).update(
                                {
                                    MainDictionary.frequency: MainDictionary.frequency
                                    + row.frequency
                                },
                                synchronize_session=False,
                            )
                            existing = (
                                db.query(MainDictionary)
                                .filter(func.lower(MainDictionary.word) == lw)
                                .first()
                            )
                            if existing:
                                updated_words.append(
                                    {
                                        "word": existing.word,
                                        "frequency": existing.frequency,
                                    }
                                )

                    except Exception:
                        logger.exception(
                            "Error merging new_map entry after IntegrityError"
                        )

                # commit any remaining updates
                try:
                    db.commit()
                except Exception:
                    db.rollback()

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
    def word_exists(db: Session, word: str) -> bool | None:
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
    def check_word(db: Session, word: str) -> dict | None:
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
        search: str | None = None,
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


# ======================================================
# USER ADDED WORD SERVICE
# ======================================================


class UserAddedWordService:

    @staticmethod
    def add_words(db: Session, words: list[dict[str, Any]]) -> dict:

        added_words = []
        updated_words = []

        try:
            for item in words:
                raw = item.get("word", "")
                try:
                    word = clean_kannada_word(raw)
                except Exception as e:
                    logger.warning(f"Skipping invalid user-added word '{raw}': {e}")
                    continue

                frequency = item.get("frequency", 1)

                existing = (
                    db.query(UserAddedWord)
                    .filter(func.lower(UserAddedWord.word) == word.lower())
                    .first()
                )

                if existing:
                    existing.frequency += frequency
                    updated_words.append(
                        {"word": existing.word, "frequency": existing.frequency}
                    )
                else:
                    db.add(UserAddedWord(word=word, frequency=frequency))
                    added_words.append({"word": word, "frequency": frequency})

            db.commit()

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
    def check_word(db: Session, word: str) -> dict | None:

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
        search: str | None = None,
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

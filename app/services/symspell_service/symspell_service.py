from __future__ import annotations

from threading import RLock
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from symspellpy import SymSpell, Verbosity

from app.config.database import get_db
from app.config.logger_config import setup_logger
from app.dbmodels.models import MainDictionary

logger = setup_logger(__name__)


class SymSpellService:
    """
    Singleton-style service for managing SymSpell.

    Responsibilities:
    - Initialize dictionary
    - Reload dictionary
    - Suggest corrections
    - Provide statistics
    """

    def __init__(
        self,
        max_dictionary_edit_distance: int = 2,
        prefix_length: int = 7,
    ):
        self._lock = RLock()

        self.max_dictionary_edit_distance = max_dictionary_edit_distance
        self.prefix_length = prefix_length

        self._symspell = SymSpell(
            max_dictionary_edit_distance=max_dictionary_edit_distance,
            prefix_length=prefix_length,
        )

        self._initialized = False
        self._loaded_word_count = 0
        self._max_word_length = 0

    @property
    def instance(self) -> SymSpell:
        return self._symspell

    def initialize(self) -> dict[str, Any]:
        """
        Load dictionary into SymSpell.
        """
        with self._lock:

            logger.info("Initializing SymSpell...")

            db: Session = next(get_db())

            try:
                result = db.execute(
                    select(MainDictionary.word, MainDictionary.frequency)
                ).all()

                loaded_count = 0

                for word, frequency in result:
                    # Defensive casting: ensure we pass a string term and integer frequency
                    try:
                        term = str(word).strip()
                    except Exception:
                        continue

                    if not term:
                        continue

                    try:
                        freq = int(frequency)
                    except Exception:
                        freq = 1

                    self._symspell.create_dictionary_entry(term, freq)
                    loaded_count += 1

                    # track max word length locally
                    try:
                        self._max_word_length = max(self._max_word_length, len(term))
                    except Exception:
                        pass

                self._loaded_word_count = loaded_count
                self._initialized = True

                logger.info(
                    f"SymSpell initialized successfully. "
                    f"Loaded words={loaded_count}, "
                    f"word_count={self._symspell.word_count}"
                )

                return self.get_statistics()

            finally:
                db.close()

    def reinitialize(self) -> dict[str, Any]:
        """
        Create a fresh SymSpell instance and reload.
        """

        with self._lock:

            logger.info("Reinitializing SymSpell...")

            self._symspell = SymSpell(
                max_dictionary_edit_distance=self.max_dictionary_edit_distance,
                prefix_length=self.prefix_length,
            )

            self._initialized = False
            self._loaded_word_count = 0
            self._max_word_length = 0

            return self.initialize()

    def get_suggestions(
        self,
        word: str,
        limit: int = 5,
    ) -> list[str]:
        """
        Get spelling suggestions.
        """

        word = word.strip()

        if not word:
            return []

        if not self._initialized:
            logger.warning("SymSpell not initialized.")
            return []

        suggestions = self._symspell.lookup(
            word,
            Verbosity.ALL,
            include_unknown=False,
        )

        if not suggestions:
            return []

        suggestions = sorted(
            suggestions,
            key=lambda x: x.count,
            reverse=True,
        )

        return [suggestion.term for suggestion in suggestions[:limit]]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get runtime statistics.
        """

        db_count = 0

        try:
            db: Session = next(get_db())

            try:
                db_count = db.query(MainDictionary).count()
            finally:
                db.close()

        except Exception as e:
            logger.warning(f"Unable to fetch database count: {e}")

        return {
            "initialized": self._initialized,
            "loaded_words": self._loaded_word_count,
            "symspell_word_count": self._symspell.word_count,
            "database_word_count": db_count,
            "max_word_length": self._max_word_length,
            "max_dictionary_edit_distance": self.max_dictionary_edit_distance,
            "prefix_length": self.prefix_length,
            "has_delete_dictionary": hasattr(self._symspell, "_deletes"),
            "dictionary_match": self._symspell.word_count == db_count,
        }


# Module-level singleton service and startup helper
symspell_service = SymSpellService()


def symspell_initialization() -> dict[str, Any]:
    """
    Blocking initialization helper used during application startup.

    Designed to be run in a background thread via `asyncio.to_thread`.
    """
    logger.info("Starting SymSpell initialization (background task)")

    try:
        stats = symspell_service.initialize()
        logger.info("SymSpell background initialization finished")
        return stats
    except Exception as e:
        logger.error(f"SymSpell initialization failed: {e}", exc_info=True)
        raise

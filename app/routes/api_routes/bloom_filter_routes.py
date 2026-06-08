# routers/bloom_filter_routes.py

from __future__ import annotations

import re
from datetime import datetime
from threading import Lock
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.logger_config import setup_logger
from app.services.bloom_service.bloom_filter import BloomWordFilter

logger = setup_logger(__name__)

bloom_router = APIRouter()

# ============================================================
# Global State
# ============================================================

loaded_bloom: Optional[BloomWordFilter] = None
last_update_timestamp: Optional[datetime] = None

# Prevent concurrent reloads
bloom_reload_lock = Lock()


# ============================================================
# Request Models
# ============================================================

class WordCheckRequest(BaseModel):
    words: list[str] = Field(
        ...,
        min_length=1,
        description="List of words to check against the Bloom filter",
    )


# ============================================================
# Response Models
# ============================================================

class WordResult(BaseModel):
    word: str
    exists: bool
    reason: str


class WordCheckResponse(BaseModel):
    total_words: int
    matched_words: int
    missing_words: int
    results: list[WordResult]


class BloomFilterStatsResponse(BaseModel):
    initialized: bool
    loaded_word_count: int
    bloom_size: int
    capacity: int
    utilization_percent: float
    error_rate: float
    is_empty: bool
    last_updated: Optional[datetime] = None


class BloomReloadResponse(BaseModel):
    success: bool
    message: str
    previous_loaded_count: int
    current_loaded_count: int
    capacity: int
    reloaded_at: datetime


# ============================================================
# Initialization Functions
# ============================================================

async def bloom_initialization() -> None:
    """
    Initialize Bloom filter at application startup.
    """

    global loaded_bloom
    global last_update_timestamp

    if loaded_bloom is not None:
        logger.info("Bloom filter already initialized. Skipping initialization.")
        return

    db: Session = next(get_db())

    try:
        logger.info("Starting Bloom filter initialization.")

        loaded_bloom = BloomWordFilter(
            db=db,
            error_rate=0.001,
        )

        loaded_bloom.load_words(db)

        last_update_timestamp = datetime.now()

        logger.info(
            f"Bloom filter initialized successfully. "
            f"LoadedCount={loaded_bloom.get_loaded_count()}, "
            f"BloomSize={loaded_bloom.get_size()}, "
            f"Capacity={loaded_bloom.get_capacity()}, "
            f"ErrorRate={loaded_bloom.get_error_rate()}"
        )

    except Exception as e:
        logger.error(
            f"Bloom filter initialization failed: {str(e)}",
            exc_info=True,
        )
        raise

    finally:
        db.close()


async def bloom_reinitialization() -> None:
    """
    Rebuild Bloom filter from current database contents.
    """

    global loaded_bloom
    global last_update_timestamp

    db: Session = next(get_db())

    try:
        logger.info("Starting Bloom filter reinitialization.")

        new_bloom = BloomWordFilter(
            db=db,
            error_rate=0.001,
        )

        new_bloom.load_words(db)

        loaded_bloom = new_bloom
        last_update_timestamp = datetime.now()

        logger.info(
            f"Bloom filter reinitialized successfully. "
            f"LoadedCount={loaded_bloom.get_loaded_count()}, "
            f"BloomSize={loaded_bloom.get_size()}, "
            f"Capacity={loaded_bloom.get_capacity()}, "
            f"ErrorRate={loaded_bloom.get_error_rate()}"
        )

    except Exception as e:
        logger.error(
            f"Bloom filter reinitialization failed: {str(e)}",
            exc_info=True,
        )
        raise

    finally:
        db.close()


# ============================================================
# APIs
# ============================================================

@bloom_router.post("/check/",response_model=WordCheckResponse)
async def check_word_in_bloom(request: WordCheckRequest) -> WordCheckResponse:
    """
    Check one or more words against the Bloom filter.
    """

    try:
        if loaded_bloom is None:
            logger.warning(
                "Word check requested before Bloom filter initialization."
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bloom filter is not initialized.",
            )

        logger.info(
            f"Checking {len(request.words)} words against Bloom filter."
        )

        results: list[WordResult] = []

        for raw_word in request.words:
            word = raw_word.strip()

            if not word:
                results.append(
                    WordResult(
                        word=raw_word,
                        exists=False,
                        reason="Empty word",
                    )
                )
                continue

            # English words and numbers bypass dictionary lookup
            if re.fullmatch(r"[a-zA-Z0-9]+", word):
                results.append(
                    WordResult(
                        word=word,
                        exists=True,
                        reason="Contains only English letters or digits",
                    )
                )
                continue

            exists = word in loaded_bloom

            results.append(
                WordResult(
                    word=word,
                    exists=exists,
                    reason=(
                        "Present in Main Dictionary"
                        if exists
                        else "Definitely not in dictionary"
                    ),
                )
            )

        matched_words = sum(
            1 for result in results if result.exists
        )

        missing_words = len(results) - matched_words

        logger.info(
            f"Word check completed. "
            f"Total={len(results)}, "
            f"Matched={matched_words}, "
            f"Missing={missing_words}"
        )

        return WordCheckResponse(
            total_words=len(results),
            matched_words=matched_words,
            missing_words=missing_words,
            results=results,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error checking words in Bloom filter: {str(e)}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check words in Bloom filter.",
        )


@bloom_router.get("/status/",response_model=BloomFilterStatsResponse)
async def get_bloom_stats() -> BloomFilterStatsResponse:
    """
    Return Bloom filter statistics.
    """

    try:
        if loaded_bloom is None:
            logger.warning(
                "Bloom stats requested before initialization."
            )

            return BloomFilterStatsResponse(
                initialized=False,
                loaded_word_count=0,
                bloom_size=0,
                capacity=0,
                utilization_percent=0.0,
                error_rate=0.0,
                is_empty=True,
                last_updated=None,
            )

        loaded_count = loaded_bloom.get_loaded_count()
        bloom_size = loaded_bloom.get_size()
        capacity = loaded_bloom.get_capacity()

        utilization_percent = (
            round((bloom_size / capacity) * 100, 2)
            if capacity > 0
            else 0.0
        )

        logger.info(
            f"Bloom stats requested. "
            f"LoadedCount={loaded_count}, "
            f"BloomSize={bloom_size}, "
            f"Capacity={capacity}, "
            f"Utilization={utilization_percent}%"
        )

        return BloomFilterStatsResponse(
            initialized=True,
            loaded_word_count=loaded_count,
            bloom_size=bloom_size,
            capacity=capacity,
            utilization_percent=utilization_percent,
            error_rate=loaded_bloom.get_error_rate(),
            is_empty=loaded_bloom.is_empty(),
            last_updated=last_update_timestamp,
        )

    except Exception as e:
        logger.error(
            f"Error getting Bloom filter stats: {str(e)}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Bloom filter statistics.",
        )


@bloom_router.post("/reload/",response_model=BloomReloadResponse)
async def reload_bloom_filter() -> BloomReloadResponse:
    """
    Rebuild the Bloom filter from the database.

    Call this endpoint whenever words are added,
    updated, or removed from MainDictionary.
    """

    global loaded_bloom

    if not bloom_reload_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bloom filter reload already in progress.",
        )

    try:
        previous_count = (
            loaded_bloom.get_loaded_count()
            if loaded_bloom is not None
            else 0
        )

        logger.info(
            f"Starting Bloom filter reload. "
            f"CurrentLoadedCount={previous_count}"
        )

        await bloom_reinitialization()

        current_count = loaded_bloom.get_loaded_count()

        logger.info(
            f"Bloom filter reload completed successfully. "
            f"PreviousCount={previous_count}, "
            f"CurrentCount={current_count}, "
            f"Capacity={loaded_bloom.get_capacity()}"
        )

        return BloomReloadResponse(
            success=True,
            message="Bloom filter reloaded successfully.",
            previous_loaded_count=previous_count,
            current_loaded_count=current_count,
            capacity=loaded_bloom.get_capacity(),
            reloaded_at=last_update_timestamp,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Bloom filter reload failed: {str(e)}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bloom filter reload failed.",
        )

    finally:
        bloom_reload_lock.release()


# ============================================================
# Utility Functions
# ============================================================

def filter_missing_words(
        words: list[str],
) -> list[str]:
    """
    Return words that are definitely not present in the Bloom filter.
    """

    if loaded_bloom is None:
        logger.warning(
            "filter_missing_words called before Bloom initialization."
        )
        return words

    missing_words = [
        word
        for word in words
        if word not in loaded_bloom
    ]

    logger.info(
        f"Filtered {len(words)} words. "
        f"Missing={len(missing_words)}"
    )

    return missing_words

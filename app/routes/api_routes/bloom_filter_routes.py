from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from threading import Lock
from typing import Optional

from docx import Document
from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from fastapi import UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.logger_config import setup_logger
from app.dbmodels.models import User
from app.services.bloom_service.bloom_filter import BloomWordFilter
from app.services.security_service.auth import admin_auth_required
from app.utils.kannada_word_clean import clean_kannada_word

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


class BloomNotFoundWordsList(BaseModel):
    wrong_words: list[str]


class BloomWrongWordsFileResponse(BaseModel):
    file_content: str
    wrong_words: list[str]


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


def filter_missing_words(
    words: list[str],
) -> list[str]:
    """
    Return words that are definitely not present in the Bloom filter.
    """

    if loaded_bloom is None:
        logger.warning("filter_missing_words called before Bloom initialization.")
        return words

    missing_words = []

    for word in words:
        cleaned_word = clean_kannada_word(word)

        # Skip invalid/empty words
        if not cleaned_word:
            continue

        if cleaned_word not in loaded_bloom:
            missing_words.append(cleaned_word)

    logger.info(f"Filtered {len(words)} words. Missing={len(missing_words)}")

    return missing_words


# ============================================================
# APIs
# ============================================================


@bloom_router.post("/check/", response_model=WordCheckResponse)
async def check_word_in_bloom(request: WordCheckRequest) -> WordCheckResponse:
    """
    Check one or more words against the Bloom filter.
    """

    try:
        if loaded_bloom is None:
            logger.warning("Word check requested before Bloom filter initialization.")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bloom filter is not initialized.",
            )

        logger.info(f"Checking {len(request.words)} words against Bloom filter.")

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

        matched_words = sum(1 for result in results if result.exists)
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


@bloom_router.get("/check/{word}", response_model=WordResult)
async def check_single_word(word: str) -> WordResult:
    """
    Check a single word against the Bloom filter.
    """

    try:
        if loaded_bloom is None:
            logger.warning(
                "Single word check requested before Bloom filter initialization."
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bloom filter is not initialized.",
            )

        word = word.strip()

        if not word:
            return WordResult(
                word=word,
                exists=False,
                reason="Empty word",
            )

        if re.fullmatch(r"[a-zA-Z0-9]+", word):
            return WordResult(
                word=word,
                exists=True,
                reason="Contains only English letters or digits",
            )

        exists = word in loaded_bloom

        return WordResult(
            word=word,
            exists=exists,
            reason=(
                "Present in Main Dictionary"
                if exists
                else "Definitely not in dictionary"
            ),
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Error checking word '{word}' in Bloom filter: {str(e)}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check word in Bloom filter.",
        )


@bloom_router.get("/filter/wrongwords", response_model=BloomNotFoundWordsList)
async def get_wrong_words(word_list: list):
    missing_words_list = filter_missing_words(words=word_list)
    return BloomNotFoundWordsList(wrong_words=missing_words_list)


@bloom_router.get(
    "/statistics/",
    response_model=BloomFilterStatsResponse,
)
async def get_bloom_stats(
    current_user: User = Depends(admin_auth_required),
) -> BloomFilterStatsResponse:
    """
    Return Bloom filter statistics.
    """

    try:
        logger.info(f"Bloom stats requested by admin: {current_user.username}")

        if loaded_bloom is None:
            logger.warning("Bloom stats requested before initialization.")

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
            round((bloom_size / capacity) * 100, 2) if capacity > 0 else 0.0
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


@bloom_router.post("/reload/", response_model=BloomReloadResponse)
async def reload_bloom_filter(
    current_user: User = Depends(admin_auth_required),
) -> BloomReloadResponse:
    """
    Rebuild the Bloom filter from the database.

    Call this endpoint whenever words are added,
    updated, or removed from MainDictionary.
    """

    global loaded_bloom

    logger.info(f"Bloom reload requested by admin: {current_user.username}")

    if not bloom_reload_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bloom filter reload already in progress.",
        )

    try:
        previous_count = (
            loaded_bloom.get_loaded_count() if loaded_bloom is not None else 0
        )

        logger.info(
            f"Starting Bloom filter reload. CurrentLoadedCount={previous_count}"
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


@bloom_router.post("/filter/wrongwords/file", response_model=BloomNotFoundWordsList)
async def get_wrong_words_from_file(file: UploadFile = File(...)):
    """
    Upload a .txt or .docx file and return:
    - file_content
    - wrong_words
    """

    filename = file.filename.lower()

    if not (filename.endswith(".txt") or filename.endswith(".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .docx files are supported.",
        )

    try:
        content = ""

        if filename.endswith(".txt"):
            content = (await file.read()).decode("utf-8")

        elif filename.endswith(".docx"):
            file_bytes = await file.read()

            document = Document(BytesIO(file_bytes))

            content = "\n".join(paragraph.text for paragraph in document.paragraphs)

        words = content.split()

        wrong_words = filter_missing_words(words=words)

        return BloomNotFoundWordsList(
            wrong_words=wrong_words,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(exc)}",
        )

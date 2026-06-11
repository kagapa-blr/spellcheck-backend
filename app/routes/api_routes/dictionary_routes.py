from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi import (
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.logger_config import setup_logger
from app.dbmodels.models import User
from schemas.common_response import APIResponse
from schemas.dictionary_schema import (
    AddUserWordsRequest,
    WordListRequest,
    ApproveUserWordsRequest,
)
from services.dictionary_service.dictionary_service import (
    MainDictionaryService,
    UserAddedWordService,
)
from services.security_service.auth import admin_auth_required
from utils.read_file_content import FileWordProcessor

logger = setup_logger(module_name=__name__)
dictionary_router = APIRouter()


# ======================================================
# MAIN DICTIONARY ROUTES
# ======================================================


@dictionary_router.delete("/main", response_model=APIResponse)
def delete_main_words(
    payload: WordListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_auth_required),
):
    logger.info(f"{payload.words} Attempted Delete by {current_user.username}")
    result = MainDictionaryService.delete_words(db=db, words=payload.words)

    if result["deleted_count"] == 0:
        raise HTTPException(status_code=404, detail="No words found")

    return APIResponse(
        message="Words deleted",
        data=result,
    )


@dictionary_router.get("/main/check", response_model=APIResponse)
def check_main_word(word: str, db: Session = Depends(get_db)):
    if not word:
        return True
    word = word.strip()
    if not word or (word.isascii() and word.isalpha()) or word.isdigit():
        return True
    result = MainDictionaryService.word_exists(db=db, word=word)
    return APIResponse(
        message="checked in Main dictionary for existance",
        data=result,
    )


@dictionary_router.get("/main", response_model=APIResponse)
def list_main_words(
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    db: Session = Depends(get_db),
):

    result = MainDictionaryService.get_words(
        db=db,
        limit=limit,
        offset=offset,
        search=search,
    )

    return APIResponse(
        message="Main dictionary list fetched",
        data=result,
    )


SUPPORTED_EXTENSIONS = {".txt", ".docx"}


@dictionary_router.post("/main/upload")
async def upload_main_dictionary_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_auth_required),
):
    temp_path = None

    try:
        filename = (file.filename or "").strip()

        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required",
            )

        extension = Path(filename).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Only .txt and .docx files are supported",
            )

        added_by_username = current_user.username

        if not added_by_username:
            raise HTTPException(
                status_code=400,
                detail="added_by_username is required",
            )

        logger.info(f"Main dictionary upload started by {added_by_username}")

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty",
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name

        if extension == ".txt":
            words = FileWordProcessor.process_txt(temp_path)
        else:
            words = FileWordProcessor.process_docx(temp_path)

        if not words:
            raise HTTPException(
                status_code=400,
                detail="No valid Kannada words found in file",
            )

        try:
            result = MainDictionaryService.add_words(
                db=db,
                words=words,
                added_by_username=added_by_username,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        result["total_words_extracted"] = len(words)

        logger.info(
            "Main dictionary upload completed by %s. Extracted=%s",
            added_by_username,
            len(words),
        )

        return APIResponse(
            message="File uploaded and dictionary updated successfully",
            data=result,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Main dictionary file upload failed")

        raise HTTPException(
            status_code=500,
            detail="File processing failed",
        ) from exc

    finally:
        await file.close()

        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logger.warning(
                    "Failed to remove temp file: %s",
                    temp_path,
                )


@dictionary_router.get("/main/count", response_model=APIResponse)
def get_dictionary_counts(db: Session = Depends(get_db)):
    return APIResponse(
        message="Main and User dictionary words count fetched",
        data={
            "main_dictionary_count": MainDictionaryService.get_count(db),
            "user_added_dictionary_count": UserAddedWordService.get_count(db),
        },
    )


@dictionary_router.post(
    "/user/approve",
    response_model=APIResponse,
)
def approve_user_words(
    payload: ApproveUserWordsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_auth_required),
):
    result = MainDictionaryService.approve_user_words(
        db=db, words=payload.words, approved_by_username=current_user.username
    )

    return APIResponse(
        message="Approval operation completed",
        data=result,
    )


# ======================================================
# USER WORD ROUTES
# ======================================================


@dictionary_router.post("/user/add", response_model=APIResponse)
def add_user_words(
    payload: AddUserWordsRequest,
    db: Session = Depends(get_db),
):

    result = UserAddedWordService.add_words(
        db=db,
        words=[w.model_dump() for w in payload.words],
    )

    return APIResponse(
        message="User words updated",
        data=result,
    )


@dictionary_router.delete("/user", response_model=APIResponse)
def delete_user_words(
    payload: WordListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_auth_required),
):
    logger.info(f"Attempting to Delete {payload.words} by {current_user.username}")
    result = UserAddedWordService.delete_words(
        db=db,
        words=payload.words,
    )

    if result["deleted_count"] == 0:
        raise HTTPException(status_code=404, detail="No words found")

    return APIResponse(
        message="User words deleted",
        data=result,
    )


@dictionary_router.get("/user", response_model=APIResponse)
def list_user_words(
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    db: Session = Depends(get_db),
):

    result = UserAddedWordService.get_words(
        db=db,
        limit=limit,
        offset=offset,
        search=search,
    )

    return APIResponse(
        message="User dictionary list fetched",
        data=result,
    )

from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.logger_config import setup_logger
from schemas.common_response import APIResponse
from schemas.dictionary_schema import (
    AddMainDictionaryWordsRequest,
    AddUserWordsRequest,
    WordListRequest,
    ApproveUserWordsRequest,
)
from services.dictionary_service.dictionary_service import (
    MainDictionaryService,
    UserAddedWordService,
)
from utils.read_file_content import FileWordProcessor

logger = setup_logger(module_name=__name__)
dictionary_router = APIRouter()


# ======================================================
# MAIN DICTIONARY ROUTES
# ======================================================


@dictionary_router.post("/main/add", response_model=APIResponse)
def add_main_words(
    payload: AddMainDictionaryWordsRequest,
    db: Session = Depends(get_db),
):
    try:
        result = MainDictionaryService.add_words(
            db=db,
            words=[w.model_dump() for w in payload.words],
            added_by_username=payload.added_by_username,
        )

        return APIResponse(
            message="Main dictionary updated",
            data=result,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@dictionary_router.delete("/main", response_model=APIResponse)
def delete_main_words(
    payload: WordListRequest,
    db: Session = Depends(get_db),
):

    result = MainDictionaryService.delete_words(db=db, words=payload.words)

    if result["deleted_count"] == 0:
        raise HTTPException(status_code=404, detail="No words found")

    return APIResponse(
        message="Words deleted",
        data=result,
    )


@dictionary_router.get("/main/{word}", response_model=APIResponse)
def get_main_word(word: str, db: Session = Depends(get_db)):

    result = MainDictionaryService.check_word(db=db, word=word)

    if not result:
        raise HTTPException(status_code=404, detail="Word not found")

    return APIResponse(
        message="Word found",
        data=result,
    )


@dictionary_router.post("/main/check", response_model=APIResponse)
def check_main_words(
    payload: WordListRequest,
    db: Session = Depends(get_db),
):

    result = MainDictionaryService.check_words(
        db=db,
        words=payload.words,
    )

    return APIResponse(
        message="Words checked",
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


@dictionary_router.post("/main/upload")
def upload_main_dictionary_file(
    file: UploadFile = File(...),
    added_by_username: str | None = Form(None),
    db: Session = Depends(get_db),
):
    temp_path = None

    try:
        # -------------------------------------
        # Validate file type early
        # -------------------------------------
        filename = file.filename or ""

        if not (filename.endswith(".txt") or filename.endswith(".docx")):
            raise HTTPException(
                status_code=400, detail="Only .txt and .docx files are supported"
            )

        # added_by_username must be provided; stop early to avoid unnecessary work
        if not added_by_username:
            raise HTTPException(status_code=400, detail="added_by_username is required")

        # -------------------------------------
        # Save temp file safely
        # -------------------------------------
        suffix = os.path.splitext(filename)[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp.flush()
            temp_path = tmp.name

        # -------------------------------------
        # Process file
        # -------------------------------------
        if filename.endswith(".txt"):
            words = FileWordProcessor.process_txt(temp_path)

        else:
            words = FileWordProcessor.process_docx(temp_path)

        if not words:
            raise HTTPException(
                status_code=400, detail="No valid Kannada words found in file"
            )

        # -------------------------------------
        # Insert into DB
        # -------------------------------------

        try:
            result = MainDictionaryService.add_words(
                db=db,
                words=words,
                added_by_username=added_by_username,
            )
            result["TotalWordsExtracted"] = len(words)

            return APIResponse(
                message="File uploaded and dictionary updated successfully",
                data=result,
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise

    except Exception:
        logger.exception("File upload failed")
        raise HTTPException(status_code=500, detail="File processing failed")

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@dictionary_router.post("/main/missing", response_model=APIResponse)
def find_missing_words(
    payload: WordListRequest,
    db: Session = Depends(get_db),
):

    result = MainDictionaryService.find_missing_words(
        db=db,
        words=payload.words,
    )

    return APIResponse(
        message="Missing words identified",
        data=result,
    )


@dictionary_router.post(
    "/user/approve",
    response_model=APIResponse,
)
def approve_user_words(
    payload: ApproveUserWordsRequest,
    db: Session = Depends(get_db),
):

    result = MainDictionaryService.approve_user_words(
        db=db,
        words=payload.words,
        approved_by_username=payload.approved_by_username,
    )

    if result["approved_count"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No matching user words found",
        )

    return APIResponse(
        message="Words approved successfully",
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
):

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


@dictionary_router.get("/user/{word}", response_model=APIResponse)
def get_user_word(word: str, db: Session = Depends(get_db)):

    result = UserAddedWordService.check_word(db=db, word=word)

    if not result:
        raise HTTPException(status_code=404, detail="Word not found")

    return APIResponse(
        message="User word found",
        data=result,
    )


@dictionary_router.post("/user/check", response_model=APIResponse)
def check_user_words(
    payload: WordListRequest,
    db: Session = Depends(get_db),
):

    result = UserAddedWordService.check_words(
        db=db,
        words=payload.words,
    )

    return APIResponse(
        message="User words checked",
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


@dictionary_router.post("/user/upload", response_model=APIResponse)
def upload_user_dictionary_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    try:
        suffix = os.path.splitext(file.filename)[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            temp_path = tmp.name

        if file.filename.endswith(".txt"):
            words = FileWordProcessor.process_txt(temp_path)

        elif file.filename.endswith(".docx"):
            words = FileWordProcessor.process_docx(temp_path)

        else:
            raise HTTPException(
                status_code=400, detail="Only .txt and .docx files are supported"
            )

        result = UserAddedWordService.add_words(
            db=db,
            words=words,
        )

        return APIResponse(
            message="User file uploaded and words updated",
            data=result,
        )

    except Exception:
        logger.exception("User file upload failed")
        raise HTTPException(status_code=500, detail="File processing failed")

    finally:
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

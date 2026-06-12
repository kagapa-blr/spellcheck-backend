from __future__ import annotations

import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends

from app.config.logger_config import setup_logger
from app.dbmodels.models import User
from app.services.security_service.auth import admin_auth_required
from app.utils.read_file_content import FileWordProcessor

load_dotenv()

admin_activities_router = APIRouter()
logger = setup_logger(__name__)


@admin_activities_router.post("/separate/words/file")
async def separate_typical_words(
    file: UploadFile = File(...),
    current_user: User = Depends(admin_auth_required),
):
    """
    Upload .txt or .docx file and return:
    - total_words_extracted
    - word_frequency
    """
    logger.info(
        f"Typical word and Frequency separation performing by {current_user.username}"
    )
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    filename = file.filename.lower()

    if not filename.endswith((".txt", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .docx files are supported.",
        )

    temp_file = None

    try:
        file_bytes = await file.read()

        suffix = Path(filename).suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp:
            temp.write(file_bytes)
            temp_file = temp.name

        if suffix == ".txt":
            word_frequency = FileWordProcessor.process_txt(temp_file)
        else:
            word_frequency = FileWordProcessor.process_docx(temp_file)

        total_words_extracted = sum(item["frequency"] for item in word_frequency)

        logger.info(
            f"File processed successfully | "
            f"file={filename} | "
            f"total_words={total_words_extracted}"
        )

        return {
            "total_words_extracted": total_words_extracted,
            "word_frequency": word_frequency,
        }

    except Exception as exc:
        logger.exception(f"File processing failed | file={filename}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(exc)}",
        )

    finally:
        if temp_file:
            Path(temp_file).unlink(missing_ok=True)

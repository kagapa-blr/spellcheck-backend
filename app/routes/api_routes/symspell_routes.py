from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from app.config.logger_config import setup_logger
from app.dbmodels.models import User
from app.schemas.symspell_schema import (
    SuggestionRequest,
    SuggestionsResponse,
    SymSpellStatisticsResponse,
)
from app.services.security_service.auth import admin_auth_required
from services.symspell_service.symspell_service import symspell_service

logger = setup_logger(__name__)

symspell_router = APIRouter()


@symspell_router.post(
    "/suggestions",
    response_model=SuggestionsResponse,
    summary="Get spelling suggestions",
)
def get_suggestions(
    request: SuggestionRequest,
):

    try:

        suggestions = symspell_service.get_suggestions(
            word=request.word,
            limit=5,
        )

        return SuggestionsResponse(suggestions=suggestions)

    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve suggestions",
        )


@symspell_router.get(
    "/statistics",
    response_model=SymSpellStatisticsResponse,
    summary="Get SymSpell statistics",
)
def get_statistics(
    current_user: User = Depends(admin_auth_required),
):
    """
    Returns runtime statistics for SymSpell.

    Includes:
    - Loaded word count
    - Max word length
    - Edit distance configuration
    - Prefix length
    - Initialization status
    """
    try:
        logger.info(f"SymSpell statistics requested by admin: {current_user.username}")

        stats = symspell_service.get_statistics()

        return SymSpellStatisticsResponse(**stats)

    except Exception as e:
        logger.error(
            f"Error retrieving SymSpell statistics: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve statistics",
        )


@symspell_router.post("/reload")
def reload_symspell(
    current_user: User = Depends(admin_auth_required),
):
    """
    Rebuilds SymSpell from the MainDictionary table.

    Admin only endpoint.

    Creates a fresh SymSpell instance and reloads
    all words from the database.
    """
    try:
        logger.info(f"Admin requested SymSpell reload: {current_user.username}")

        stats = symspell_service.reinitialize()

        logger.info("SymSpell reload completed successfully")

        return {
            "status": "success",
            "message": "SymSpell reloaded successfully",
            "statistics": stats,
        }

    except Exception as e:
        logger.error(
            f"Error reloading SymSpell: {str(e)}",
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to reload SymSpell",
        )


@symspell_router.get(
    "/health",
    summary="SymSpell health check",
)
def health_check(
    current_user: User = Depends(admin_auth_required),
):
    """
    Lightweight endpoint to verify that
    SymSpell is initialized and operational.
    """
    try:
        logger.info(
            f"SymSpell health check requested by admin: {current_user.username}"
        )

        stats = symspell_service.get_statistics()

        loaded_words = (
            stats.get("current_symspell_words_count")
            if "current_symspell_words_count" in stats
            else stats.get("symspell_word_count", 0)
        )

        is_healthy = stats["initialized"] and loaded_words > 0

        return {
            "healthy": is_healthy,
            "initialized": stats["initialized"],
            "loaded_words": loaded_words,
            "last_updated": stats.get("last_updated"),
        }

    except Exception as e:
        logger.error(
            f"SymSpell health check failed: {str(e)}",
            exc_info=True,
        )

        return {
            "healthy": False,
            "error": str(e),
        }

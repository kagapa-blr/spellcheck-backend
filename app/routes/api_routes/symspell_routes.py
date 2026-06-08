# routers/symspell_routes.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config.logger_config import setup_logger
from app.schemas.symspell_schema import (
    SuggestionRequest,
    SuggestionsResponse,
    SymSpellStatisticsResponse,
)
from services.symspell_service.symspell_service import symspell_service

logger = setup_logger(__name__)

symspell_router = APIRouter()


@symspell_router.post(
    "/suggestions",
    response_model=SuggestionsResponse,
    summary="Get spelling suggestions",
)
def get_suggestions(request: SuggestionRequest):
    """
    Get spelling suggestions for a given word.

    Example:
        POST /symspell/suggestions

        {
            "word": "kannda"
        }
    """
    try:
        suggestions = symspell_service.get_suggestions(
            word=request.word,
            limit=5,
        )

        return SuggestionsResponse(suggestions=suggestions)

    except Exception as e:
        logger.error(
            f"Error getting suggestions: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve suggestions",
        )


@symspell_router.get(
    "/statistics",
    response_model=SymSpellStatisticsResponse,
    summary="Get SymSpell statistics",
)
def get_statistics():
    """
    Returns runtime statistics for SymSpell.

    Includes:
    - Loaded word count
    - Database word count
    - Max word length
    - Edit distance configuration
    - Prefix length
    - Initialization status
    """
    try:
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
def reload_symspell():
    """
    Rebuilds SymSpell from the MainDictionary table.

    Admin only endpoint.

    Creates a fresh SymSpell instance and reloads
    all words from the database.
    """
    try:
        logger.info("Admin requested SymSpell reload")

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
def health_check():
    """
    Lightweight endpoint to verify that
    SymSpell is initialized and operational.
    """
    try:
        stats = symspell_service.get_statistics()

        is_healthy = (
            stats["initialized"]
            and stats["symspell_word_count"] > 0
            and stats["has_delete_dictionary"]
        )

        return {
            "healthy": is_healthy,
            "initialized": stats["initialized"],
            "loaded_words": stats["symspell_word_count"],
            "dictionary_match": stats["dictionary_match"],
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

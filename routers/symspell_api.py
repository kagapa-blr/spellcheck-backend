# routers/bloom_api.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from symspellpy import Verbosity

from symspell.sym_spell import get_sym_spell, symspell_initialization, symspell_reinitialization, get_symspell_word_count
from config.logger_config import setup_logger
from security.auth import admin_auth_required

# Create a new APIRouter for SymSpell
router = APIRouter()

# Setup logger
logger = setup_logger(__name__)


# Request model for getting suggestions
class SuggestionRequest(BaseModel):
    word: str


# Response model for suggestions
class SuggestionsResponse(BaseModel):
    suggestions: list


# Response model for SymSpell model details
class SymSpellDetailsResponse(BaseModel):
    loaded_words: int
    error_rate: float  # Assuming you have a method to calculate this
    other_details: str  # Add any other relevant details you want to include


# API for getting suggestions from SymSpell
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/suggestions/", response_model=SuggestionsResponse)
def get_suggestions(request: SuggestionRequest):
    """Get spelling suggestions for the provided word.
    
    NOTE: This endpoint does NOT reload the SymSpell dictionary - it uses the already-loaded 
    instance for performance. To reload the dictionary after updates, call /admin/reload 
    endpoint only.
    """
    try:
        word = request.word.strip()
        
        if not word:
            logger.warning("Empty word provided for suggestions")
            return SuggestionsResponse(suggestions=[])
        
        # Get the current SymSpell instance (always gets latest after reload)
        current_sym_spell = get_sym_spell()
        
        # Get the actual word count from SymSpell
        symspell_word_count = current_sym_spell.word_count
        logger.info(f"SymSpell current word count: {symspell_word_count}")
        
        # Check if SymSpell has words loaded
        if symspell_word_count == 0:
            logger.error(f"SymSpell has 0 words loaded - not initialized properly")
            return SuggestionsResponse(suggestions=[])
        
        # Check if SymSpell internal structures exist
        if not hasattr(current_sym_spell, '_deletes'):
            logger.error("SymSpell _deletes structure not found - incomplete initialization")
            return SuggestionsResponse(suggestions=[])
        
        logger.info(f"Looking up suggestions for word: '{word}' (SymSpell has {symspell_word_count} words)")
        
        # Look up suggestions using SymSpell
        suggestions = current_sym_spell.lookup(word, Verbosity.ALL, include_unknown=False)
        
        logger.info(f"Lookup returned {len(suggestions)} suggestions for '{word}'")
        
        # Log the raw suggestions for debugging
        if suggestions:
            logger.debug(f"Raw suggestions: {[(s.term, s.count) for s in suggestions]}")

        if not suggestions:
            logger.info(f"No suggestions found for word: '{word}', returning empty suggestions")
            return SuggestionsResponse(suggestions=[])

        # Extract terms and their frequencies into a list
        suggestion_terms_with_frequencies = [(suggestion.term, suggestion.count) for suggestion in suggestions]

        # Sort suggestions based on frequency (count) in descending order
        sorted_suggestions = sorted(suggestion_terms_with_frequencies, key=lambda x: x[1], reverse=True)

        # Extract terms into a list (only the words)
        top_suggestions = [term for term, _ in sorted_suggestions[:5]]  # Get up to 5 suggestions
        
        logger.info(f"Returning {len(top_suggestions)} top suggestions: {top_suggestions}")

        return SuggestionsResponse(suggestions=top_suggestions)
    
    except Exception as e:
        logger.error(f"Error getting suggestions for word '{request.word}': {str(e)}", exc_info=True)
        return SuggestionsResponse(suggestions=[])


# API for getting details about the SymSpell model
@router.get("/symspell/details/", response_model=SymSpellDetailsResponse)
def get_symspell_details():
    """Get details about the SymSpell model."""
    try:
        current_sym_spell = get_sym_spell()
        loaded_words = get_symspell_word_count()
        error_rate = calculate_error_rate()
        other_details = f"SymSpell with edit distance 2 and prefix length 7 loaded. Initialized: {hasattr(current_sym_spell, '_deletes')}"
        
        logger.info(f"SymSpell details: {loaded_words} words loaded, error_rate: {error_rate}")

        return SymSpellDetailsResponse(
            loaded_words=loaded_words,
            error_rate=error_rate,
            other_details=other_details
        )
    except Exception as e:
        logger.error(f"Error getting SymSpell details: {str(e)}", exc_info=True)
        return SymSpellDetailsResponse(
            loaded_words=0,
            error_rate=0.0,
            other_details="Error retrieving SymSpell details"
        )


def calculate_error_rate() -> float:
    """Calculate the error rate for the SymSpell model."""
    # Implement your logic here to compute the error rate
    return 0.001  # Default placeholder value


@router.post("/reload/", dependencies=[Depends(admin_auth_required)])
async def reload_symspell():
    """Reload the SymSpell dictionary on demand. ADMIN ONLY.
    
    Note: Use /admin/reload endpoint instead to reload both Bloom and SymSpell together.
    This endpoint should only be called by administrators to avoid performance issues.
    """
    try:
        logger.info("Admin triggered SymSpell reinitialization...")
        symspell_reinitialization()  # Call reinitialization function
        word_count = get_symspell_word_count()
        logger.info(f"SymSpell dictionary reloaded successfully with {word_count} words.")
        
        if word_count == 0:
            logger.warning("SymSpell reloaded but word count is 0")
        
        return {
            "message": "SymSpell dictionary reloaded successfully",
            "loaded_words": word_count,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error reloading SymSpell: {str(e)}", exc_info=True)
        return {
            "message": f"Error reloading SymSpell: {str(e)}",
            "status": "error",
            "loaded_words": 0
        }

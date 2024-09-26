# routers/bloom_api.py

from fastapi import APIRouter
from pydantic import BaseModel
from symspellpy import Verbosity

from symspell.sym_spell import sym_spell, symspell_initialization

# Create a new APIRouter for SymSpell
router = APIRouter()


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
    """Get spelling suggestions for the provided word."""
    logger.info(f"Received request for suggestions for word: {request.word}")

    # Look up suggestions using SymSpell
    suggestions = sym_spell.lookup(request.word, Verbosity.ALL, include_unknown=False)

    # Log the suggestions found
    if suggestions:
        logger.info(f"Suggestions found: {[suggestion.term for suggestion in suggestions]}")
    else:
        logger.warning("No suggestions found.")

    return SuggestionsResponse(suggestions=[suggestion.term for suggestion in suggestions])


# API for getting details about the SymSpell model
@router.get("/symspell/details/", response_model=SymSpellDetailsResponse)
def get_symspell_details():
    """Get details about the SymSpell model."""
    loaded_words = sym_spell.word_count  # Assuming this gives you the count of loaded words
    error_rate = calculate_error_rate()  # Replace with actual logic to calculate error rate
    other_details = "Add any additional information here."  # Customize this as needed

    return SymSpellDetailsResponse(
        loaded_words=loaded_words,
        error_rate=error_rate,
        other_details=other_details
    )


def calculate_error_rate() -> float:
    """Calculate the error rate for the SymSpell model."""
    # Implement your logic here to compute the error rate
    return 0.0  # Placeholder value; replace with actual calculation


@router.post("/reload/")
async def reload_symspell():
    """Reload the SymSpell dictionary on demand."""
    symspell_initialization()  # Call your existing initialization function
    return {"message": "SymSpell dictionary reloaded successfully."}

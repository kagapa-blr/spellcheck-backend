from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SuggestionRequest(BaseModel):
    word: str


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class SymSpellStatisticsResponse(BaseModel):
    initialized: bool
    current_symspell_words_count: int
    max_word_length: int
    max_dictionary_edit_distance: int
    prefix_length: int
    last_updated: Optional[datetime] = None

from pydantic import BaseModel


class SuggestionRequest(BaseModel):
    word: str


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


class SymSpellStatisticsResponse(BaseModel):
    initialized: bool
    loaded_words: int
    symspell_word_count: int
    database_word_count: int
    max_word_length: int
    max_dictionary_edit_distance: int
    prefix_length: int
    has_delete_dictionary: bool
    dictionary_match: bool

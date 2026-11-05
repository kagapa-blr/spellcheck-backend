from typing import Optional

from pydantic import BaseModel, Field


class WordInput(BaseModel):
    word: str
    frequency: int = Field(default=1, ge=1)


class AddMainDictionaryWordsRequest(BaseModel):
    words: list[WordInput]
    added_by_username: Optional[str] = None


class AddUserWordsRequest(BaseModel):
    words: list[WordInput]


class WordListRequest(BaseModel):
    words: list[str]


class UpdateMainDictionaryWordRequest(BaseModel):
    word: str = Field(min_length=1, max_length=255)
    frequency: int = Field(ge=1)


class MainDictionaryWordResponse(BaseModel):
    id: int
    word: str
    frequency: int
    added_by_username: Optional[str] = None


class MainDictionaryListResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    words: list[MainDictionaryWordResponse]


class WordResponse(BaseModel):
    word: str
    frequency: int


class AddWordsResponse(BaseModel):
    added_count: int
    updated_count: int
    added_words: list[WordResponse]
    updated_words: list[WordResponse]


class ApproveUserWordsRequest(BaseModel):
    words: list[str]
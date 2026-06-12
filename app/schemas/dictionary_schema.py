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
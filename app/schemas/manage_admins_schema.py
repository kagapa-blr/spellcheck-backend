from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr


# -------------------------
# Pydantic Models
# -------------------------
class UserSignupRequest(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class UsernameListResponse(BaseModel):
    usernames: list[str]


class UserSignupResponse(BaseModel):
    message: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserExistenceResponse(BaseModel):
    username: str
    exists: bool


class UserInfoResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: str

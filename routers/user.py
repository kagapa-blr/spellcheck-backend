from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr  # For validation
from auth import create_access_token, get_password_hash, verify_password
from models import User
from database import get_db
from datetime import timedelta

router = APIRouter()


# Pydantic models for request and response validation
class UserSignupRequest(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserSignupResponse(BaseModel):
    message: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/signup", response_model=UserSignupResponse)
def signup(request: UserSignupRequest, db: Session = Depends(get_db)):
    # Check if the user already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(request.password)
    new_user = User(username=request.username, email=request.email, phone=request.phone, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserSignupResponse(message="User created successfully")


@router.post("/login", response_model=UserLoginResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return UserLoginResponse(access_token=access_token, token_type="bearer")

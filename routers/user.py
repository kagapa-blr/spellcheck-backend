from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr  # For validation
from sqlalchemy.orm import Session

from auth import create_access_token, get_password_hash, verify_password
from database import get_db
from models import User

router = APIRouter()


# Pydantic models for request and response validation
class UserSignupRequest(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str


# New model for updating user details
class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None  # Optional field
    phone: Optional[str] = None  # Optional field
    password: Optional[str] = None  # Optional field


# Response model for getting usernames
class UsernameListResponse(BaseModel):
    usernames: List[str]


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserSignupResponse(BaseModel):
    message: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str


# Response model for checking user existence
class UserExistenceResponse(BaseModel):
    username: str
    exists: bool


class UserInfoResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: str


@router.post("/signup", response_model=UserSignupResponse)
def signup(request: UserSignupRequest, db: Session = Depends(get_db)):
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


@router.get("/usernames", response_model=UsernameListResponse)
def get_all_usernames(db: Session = Depends(get_db)):
    users = db.query(User.username).all()  # Fetch all usernames from the User table
    usernames = [user[0] for user in users]  # Extract usernames from the results
    return UsernameListResponse(usernames=usernames)


@router.get("/check-user/{username}", response_model=UserExistenceResponse)
def check_user_exists(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    return UserExistenceResponse(username=username, exists=user is not None)


@router.get("/info", response_model=List[UserInfoResponse])
def get_all_user_info(db: Session = Depends(get_db)):
    users = db.query(User).all()  # Fetch all users from the User table
    return users  # FastAPI automatically serializes it into JSON using the Pydantic model


@router.delete("/delete-user/{username}", response_model=UserSignupResponse)
def delete_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()

    return UserSignupResponse(message="User deleted successfully")


@router.put("/update-user/{username}", response_model=UserSignupResponse)
def update_user(username: str, request: UserUpdateRequest, db: Session = Depends(get_db)):
    """Update a user's details in the database by username."""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields if provided
    if request.email:
        user.email = request.email
    if request.phone:
        user.phone = request.phone
    if request.password:
        user.password = get_password_hash(request.password)  # Hash the new password

    db.commit()
    db.refresh(user)

    return UserSignupResponse(message="User updated successfully")

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import create_access_token, get_password_hash, verify_password
from models import User
from database import get_db
from datetime import timedelta

router = APIRouter()

@router.post("/signup")
def signup(username: str, email: str, phone: str, password: str, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, phone=phone, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

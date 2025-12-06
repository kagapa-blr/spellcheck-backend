#auth.py
"""
Author: Ravikumar Pawar
Email: ravi.ravipawar17@gmail.com
Description:Ekannada Spellcheck Application authorization usage
Date:25-11-2025
"""

import os
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from config.database import SessionLocal
import pytz
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config.database import get_db
from dbmodels.models import User

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
default_admin_username = os.getenv("ADMIN_USERNAME")
default_admin_password = os.getenv("ADMIN_PASSWORD")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/kaagunitha/user/api/v1/generate/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=pytz.timezone('Asia/Kolkata')) + expires_delta  # Use timezone-aware UTC
    else:
        expire = datetime.now(tz=pytz.timezone('Asia/Kolkata')) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Use timezone-aware UTC
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def admin_auth_required(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch user from the database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    # If the token is valid, return the user
    return user




async def create_default_admin():
    db = SessionLocal()  # Initialize the session properly
    try:
        # Check if the admin user already exists
        admin_user = db.query(User).filter_by(username=default_admin_username).first()

        if not admin_user:
            # If admin doesn't exist, create it
            admin_password_hashed = get_password_hash(default_admin_password)  # Use the correct hashing function
            new_admin = User(
                username=default_admin_username,
                email="admin@example.com",  # You can customize the email
                phone="1234567",  # You can customize the phone
                password=admin_password_hashed
            )
            db.add(new_admin)
            db.commit()
            print("Default admin user created.")
        else:
            # If admin user exists, update the password
            admin_password_hashed = get_password_hash(default_admin_password)
            admin_user.password = admin_password_hashed
            db.commit()
            print("Admin user password updated.")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error creating or updating admin user: {str(e)}")
    finally:
        db.close()


def generate_token(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify if the password is correct
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If credentials are valid, create and return access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}

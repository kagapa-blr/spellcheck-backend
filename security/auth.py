"""
Author: Ravikumar Pawar
Email: ravi.ravipawar17@gmail.com
Description: Ekannada Spellcheck Application authorization usage
Date: 25-11-2025
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.database import SessionLocal, get_db
from config.logger_config import setup_logger
from dbmodels.models import User

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
JWT_SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM','HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))
default_admin_username = os.getenv("ADMIN_USERNAME")
default_admin_password = os.getenv("ADMIN_PASSWORD")
ISSUER = os.getenv("TOKEN_ISSUER", "ekannada-app")
AUDIENCE = os.getenv("TOKEN_AUDIENCE", "ekannada-users")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/kaagunitha/user/api/v1/generate/token")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

logger = setup_logger(__name__)
# ----------------------------
# Password Utilities
# ----------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ----------------------------
# JWT Token Utilities
# ----------------------------
# ----------------------------
# JWT Token Utilities
# ----------------------------
def create_access_token(
        subject: str,
        expires_delta: Optional[timedelta] = None,
        extra_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a secure JWT access token with standard claims.
    Uses the expires_delta if provided; otherwise defaults to ACCESS_TOKEN_EXPIRE_MINUTES.
    """

    try:
        now = datetime.now(timezone.utc)

        # Determine expiration
        expire = (
            now + expires_delta
            if expires_delta
            else now + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        )

        payload = {
            "sub": str(subject),           # Subject (user identity)
            "iss": ISSUER,                 # Issuer
            "aud": AUDIENCE,               # Audience
            "iat": int(now.timestamp()),   # Issued at
            "nbf": int(now.timestamp()),   # Not valid before
            "exp": int(expire.timestamp()),# Expiry
            "jti": str(uuid.uuid4()),      # Unique token ID
        }

        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        logger.info(
            f"Access token created for user={subject}, "
            f"expires_at={expire.isoformat()}, "
            f"claims={list(extra_claims.keys()) if extra_claims else []}"
        )

        return token

    except Exception as e:
        logger.error(f"Failed to create access token for user={subject}: {str(e)}")
        raise

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            audience=AUDIENCE,
            issuer=ISSUER
        )
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_exception
    return user


def admin_auth_required(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Returns the user if they are authenticated as admin.
    """
    user = get_current_user(token, db)
    if user.username != default_admin_username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


# ----------------------------
# Default Admin Creation
# ----------------------------
async def create_default_admin():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == default_admin_username).first()
        if not admin_user:
            admin_password_hashed = get_password_hash(default_admin_password)
            new_admin = User(
                username=default_admin_username,
                email=os.getenv('EMAIL', 'ekannada@gmail.com'),
                phone=os.getenv('PHONE', 123456789),
                password=admin_password_hashed
            )
            db.add(new_admin)
            db.commit()
            print("Default admin user created.")
        else:
            # Update password if already exists
            admin_user.password = get_password_hash(default_admin_password)
            db.commit()
            print("Admin user password updated.")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Error creating/updating admin user: {str(e)}")
    finally:
        db.close()

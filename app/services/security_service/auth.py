"""
Author: Ravikumar Pawar
Email: ravi.ravipawar17@gmail.com
Description: Ekannada Spellcheck Application authorization usage
Date: 25-11-2025
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.database import get_db, get_session
from app.config.logger_config import setup_logger
from app.dbmodels.models import User

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
JWT_SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))
default_admin_username = os.getenv("ADMIN_USERNAME")
default_admin_password = os.getenv("ADMIN_PASSWORD")
ISSUER = os.getenv("TOKEN_ISSUER", "ekannada-app")
AUDIENCE = os.getenv("TOKEN_AUDIENCE", "ekannada-users")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/api/v1/generate/token")
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

logger = setup_logger(__name__)

# Ensure a secret key is configured at startup for secure token signing
if not JWT_SECRET_KEY:
    logger.error("JWT SECRET_KEY is not set. Tokens cannot be created or verified.")
    raise RuntimeError("JWT SECRET_KEY is required for token creation and verification")


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
    extra_claims: Optional[dict[str, Any]] = None,
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
            "sub": str(subject),  # Subject (user identity)
            "iss": ISSUER,  # Issuer
            "aud": AUDIENCE,  # Audience
            "iat": int(now.timestamp()),  # Issued at
            "nbf": int(now.timestamp()),  # Not valid before
            "exp": int(expire.timestamp()),  # Expiry
            "jti": str(uuid.uuid4()),  # Unique token ID
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


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
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
            issuer=ISSUER,
        )
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_exception
    return user


def admin_auth_required(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Returns the user if they are authenticated as admin.
    """
    user = get_current_user(token, db)
    if user.username != default_admin_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user


# ----------------------------
# Default Admin Creation
# ----------------------------
async def create_default_admin():
    """
    Ensure a default admin user exists at application startup.

    Behavior:
    - `ADMIN_USERNAME` and `ADMIN_PASSWORD` must be set in environment.
    - If user does not exist, create with provided email/phone (or sensible defaults).
    - If user exists, update the password to the provided value.
    """

    if not default_admin_username or not default_admin_password:
        logger.error(
            "ADMIN_USERNAME and ADMIN_PASSWORD must be set to create default admin"
        )
        return

    db = get_session()
    try:
        admin_user = (
            db.query(User).filter(User.username == default_admin_username).first()
        )

        # normalize defaults
        email = os.getenv("EMAIL", "admin@example.com")
        phone = os.getenv("PHONE", "")

        if not admin_user:
            admin_password_hashed = get_password_hash(default_admin_password)
            new_admin = User(
                username=default_admin_username,
                email=email,
                phone=str(phone),
                password=admin_password_hashed,
            )
            db.add(new_admin)
            db.commit()
            logger.info("Default admin user created: %s", default_admin_username)
        else:
            # Update password if already exists
            admin_user.password = get_password_hash(default_admin_password)
            # ensure email/phone are updated if provided
            admin_user.email = email or admin_user.email
            admin_user.phone = str(phone) or admin_user.phone
            db.commit()
            logger.info("Admin user password updated for: %s", default_admin_username)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Error creating/updating admin user")
        raise
    finally:
        try:
            db.close()
        except Exception:
            logger.debug(
                "Exception while closing DB session in create_default_admin",
                exc_info=True,
            )

from __future__ import annotations

import os
from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.logger_config import setup_logger
from app.dbmodels.models import User
from app.services.security_service.auth import (
    create_access_token,
    get_current_user,
    admin_auth_required,
    default_admin_username,
    get_password_hash,
    verify_password,
)
from schemas.common_response import APIResponse
from schemas.manage_admins_schema import (
    UserSignupRequest,
    UserLoginResponse,
    UserLoginRequest,
    UserInfoResponse,
    UserUpdateRequest,
    TokenResponse,
)

load_dotenv()
manage_admin_router = APIRouter()
logger = setup_logger(__name__)

IST = pytz.timezone("Asia/Kolkata")
LOCKOUT_THRESHOLD = int(os.getenv("LOCKOUT_THRESHOLD", 5))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", 20))


# -------------------------
# Helper
# -------------------------
def _issue_token_for_user(user: User) -> str:
    """Central method to issue a JWT token with standard claims and extra info."""
    logger.info(f"Issuing token for user: {user.username}")

    extra_claims = {}

    roles = []
    if hasattr(user, "roles"):
        if isinstance(user.roles, str):
            roles = [r.strip() for r in user.roles.split(",") if r.strip()]
        elif isinstance(user.roles, list):
            roles = user.roles

    if roles:
        extra_claims["roles"] = roles
    if getattr(user, "email", None):
        extra_claims["email"] = user.email

    token = create_access_token(subject=user.username, extra_claims=extra_claims)

    logger.info(f"Token issued for {user.username}")
    return token


# -------------------------
# Routes
# -------------------------


@manage_admin_router.post("/signup", response_model=APIResponse, status_code=201)
def signup(
    request: UserSignupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_auth_required),
):
    logger.info(f"Signup attempt by admin user: {current_user.username}")

    if db.query(User).filter(User.username == request.username).first():
        logger.warning(f"Signup failed: username '{request.username}' already exists")
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(
        username=request.username,
        email=request.email,
        phone=request.phone,
        password=get_password_hash(request.password),
    )

    try:
        db.add(new_user)
        db.commit()
        logger.info(f"New user created: {request.username}")
    except Exception:
        db.rollback()
        logger.exception("Failed to create new user")
        raise HTTPException(status_code=500, detail="Failed to create user")

    return APIResponse(success=True, message="User created successfully", data=None)


@manage_admin_router.post("/login", response_model=APIResponse)
def login_json(request: UserLoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for username/email: {request.username}")

    user = (
        db.query(User)
        .filter((User.username == request.username) | (User.email == request.username))
        .first()
    )

    if not user:
        logger.warning(f"Login failed: user '{request.username}' not found")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # -----------------------------
    # CURRENT TIME IN IST
    # -----------------------------
    now = datetime.now(IST)

    # Normalize DB locked_until
    locked_until = None
    if user.locked_until:
        if user.locked_until.tzinfo is None:
            # naive → IST-aware
            locked_until = IST.localize(user.locked_until)
        else:
            locked_until = user.locked_until.astimezone(IST)

    # -----------------------------
    # CHECK LOCKOUT
    # -----------------------------
    if locked_until and now < locked_until:
        remaining_minutes = int((locked_until - now).total_seconds() // 60)
        logger.warning(
            f"User '{user.username}' is locked out for {remaining_minutes} more minutes"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Account locked. Try again after {remaining_minutes} minutes.",
        )

    # -----------------------------
    # PASSWORD CHECK
    # -----------------------------
    if not verify_password(request.password, user.password):
        user.failed_attempts += 1
        attempts_left = LOCKOUT_THRESHOLD - user.failed_attempts
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to update failed_attempts")
            raise HTTPException(status_code=500, detail="Internal error")

        logger.warning(
            f"Incorrect password for '{user.username}'. "
            f"Failed attempts: {user.failed_attempts}/{LOCKOUT_THRESHOLD}"
        )

        if user.failed_attempts >= LOCKOUT_THRESHOLD:
            user.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            try:
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Failed to set locked_until")
                raise HTTPException(status_code=500, detail="Internal error")

            logger.error(f"User '{user.username}' locked out until {user.locked_until}")
            raise HTTPException(
                status_code=403,
                detail=f"Too many failed attempts. "
                f"Account locked for {LOCKOUT_DURATION_MINUTES} minutes.",
            )

        # Wrong password but not locked yet
        raise HTTPException(
            status_code=401,
            detail=f"Invalid password. {attempts_left} attempt(s) remaining.",
        )

    # -----------------------------
    # SUCCESSFUL LOGIN
    # -----------------------------
    user.failed_attempts = 0
    user.locked_until = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to reset failed_attempts on successful login")
        raise HTTPException(status_code=500, detail="Internal error")

    token = _issue_token_for_user(user)

    logger.info(f"Login successful for user: {user.username}")

    return APIResponse(
        success=True,
        message="Login successful",
        data=UserLoginResponse(access_token=token, token_type="bearer"),
    )


@manage_admin_router.post(
    "/generate/token",
    response_model=TokenResponse,
)
def generate_token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    logger.info(f"Swagger token request for: {form.username}")

    user = (
        db.query(User)
        .filter((User.username == form.username) | (User.email == form.username))
        .first()
    )

    if not user or not verify_password(form.password, user.password):
        logger.warning(f"Swagger token failed for: {form.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    token = _issue_token_for_user(user)

    logger.info(f"Token issued via Swagger for: {user.username}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


@manage_admin_router.get("/admins", response_model=APIResponse)
def get_all_user_info(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    logger.info(f"admins info fetch by: {current_user.username}")

    if current_user.username == default_admin_username:
        users = db.query(User).all()
        logger.info("Admin fetched all user info")
    else:
        users = [current_user]
        logger.info(f"User fetched own info: {current_user.username}")

    users_response = [
        UserInfoResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            phone=u.phone,
        )
        for u in users
    ]

    return APIResponse(success=True, message=None, data=users_response)


@manage_admin_router.delete("/delete/{username}", response_model=APIResponse)
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_auth_required),
):
    logger.info(f"Delete user request for '{username}' by {current_user.username}")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Delete failed: user '{username}' not found")
        raise HTTPException(status_code=404, detail="User not found")

    try:
        db.delete(user)
        db.commit()
        logger.info(f"User deleted: {username}")
        return APIResponse(success=True, message="User deleted successfully", data=None)
    except Exception:
        db.rollback()
        logger.exception("Failed to delete user: %s", username)
        raise HTTPException(status_code=500, detail="Failed to delete user")


@manage_admin_router.put("/update/{username}", response_model=APIResponse)
def update_user(
    username: str,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_auth_required),
):
    logger.info(f"Update request for '{username}' by {current_user.username}")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.error(f"Update failed: user '{username}' not found")
        raise HTTPException(status_code=404, detail="User not found")

    if request.email:
        logger.info(f"Updating email for: {username}")
        user.email = request.email
    if request.phone:
        logger.info(f"Updating phone for: {username}")
        user.phone = request.phone
    if request.password:
        logger.info(f"Updating password for: {username}")
        user.password = get_password_hash(request.password)

    try:
        db.commit()
        logger.info(f"User updated: {username}")
        return APIResponse(success=True, message="User updated successfully", data=None)
    except Exception:
        db.rollback()
        logger.exception("Failed to update user: %s", username)
        raise HTTPException(status_code=500, detail="Failed to update user")


@manage_admin_router.get(
    "/admin/validate",
    response_model=APIResponse,
)
async def validate_admin(
    current_user: User = Depends(admin_auth_required),
):
    return APIResponse(
        success=True,
        message="Admin authentication successful",
        data={"username": current_user.username},
    )

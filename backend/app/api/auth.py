from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, RefreshRequest, UserResponse
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
    revoke_token,
)
from app.core.audit import log_login_success, log_login_failure, log_logout
from app.core.rate_limit import login_rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    client_ip = _get_client_ip(request)

    is_limited, retry_after = login_rate_limiter.check_rate_limit(credentials.email, client_ip)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)} if retry_after else None,
        )

    user = db.query(User).filter(User.email == credentials.email).first()

    if not user:
        login_rate_limiter.record_failure(credentials.email, client_ip)
        log_login_failure(
            db=db,
            email=credentials.email,
            request_method="POST",
            request_path="/api/auth/login",
            details="User not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        login_rate_limiter.record_failure(credentials.email, client_ip)
        log_login_failure(
            db=db,
            email=credentials.email,
            request_method="POST",
            request_path="/api/auth/login",
            details="Inactive user"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    if not verify_password(credentials.password, user.password_hash):
        login_rate_limiter.record_failure(credentials.email, client_ip)
        log_login_failure(
            db=db,
            email=credentials.email,
            request_method="POST",
            request_path="/api/auth/login",
            details="Invalid password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    login_rate_limiter.clear_failures(credentials.email, client_ip)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token, expires_in = create_access_token(user.id, user.email, user.role.value)
    refresh_token, refresh_expires_at = create_refresh_token(user.id)

    log_login_success(
        db=db,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        request_method="POST",
        request_path="/api/auth/login"
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    payload = decode_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    jti = payload.get("jti")
    if jti:
        from app.core.security import is_token_revoked
        if is_token_revoked(jti, db):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    if jti:
        expires = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
        revoke_token(jti, expires, db)

    new_access_token, expires_in = create_access_token(user.id, user.email, user.role.value)
    new_refresh_token, refresh_expires_at = create_refresh_token(user.id)

    return LoginResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse.model_validate(current_user)


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    log_logout(
        db=db,
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role.value
    )
    return {"message": "Logged out successfully"}
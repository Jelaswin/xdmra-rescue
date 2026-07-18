import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, RevokedToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

KNOWN_WEAK_SECRETS = {
    "dev-secret-change-in-production",
    "change-me",
    "secret",
    "changeme",
    "password",
    "your-secret-key",
}

ENV = os.getenv("ENV", os.getenv("ENVIRONMENT", "")).lower()
_IS_DEV = ENV in ("development", "dev", "test")


def _is_production() -> bool:
    return not _IS_DEV


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        if _is_production():
            raise ValueError(
                "JWT_SECRET environment variable is not set. "
                "A secure secret of at least 32 characters is required in production."
            )
        return "dev-secret-change-in-production"

    if len(secret) < 32:
        if _is_production():
            raise ValueError(
                f"JWT_SECRET is too short ({len(secret)} chars). "
                "A minimum of 32 characters is required in production."
            )
        return secret

    secret_lower = secret.lower()
    if secret_lower in KNOWN_WEAK_SECRETS:
        if _is_production():
            raise ValueError(
                "JWT_SECRET is a known weak/placeholder value. "
                "A unique secret of at least 32 characters is required in production."
            )
        return secret

    return secret


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, email: str, role: str) -> tuple[str, int]:
    secret = get_jwt_secret()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": f"{user_id}_{datetime.now(timezone.utc).timestamp()}"
    }
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_refresh_token(user_id: int) -> tuple[str, datetime]:
    secret = get_jwt_secret()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": f"refresh_{user_id}_{datetime.now(timezone.utc).timestamp()}"
    }
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token, expire


def decode_token(token: str) -> Optional[dict]:
    secret = get_jwt_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_revoked(jti: str, db: Session) -> bool:
    return db.query(RevokedToken).filter(RevokedToken.token_jti == jti).first() is not None


def revoke_token(jti: str, expires_at: datetime, db: Session) -> None:
    revoked = RevokedToken(token_jti=jti, expires_at=expires_at)
    db.add(revoked)
    db.commit()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, email: str, role: str) -> tuple[str, int]:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": f"{user_id}_{datetime.now(timezone.utc).timestamp()}"
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_refresh_token(user_id: int) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": f"refresh_{user_id}_{datetime.now(timezone.utc).timestamp()}"
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, expire


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_revoked(jti: str, db: Session) -> bool:
    return db.query(RevokedToken).filter(RevokedToken.token_jti == jti).first() is not None


def revoke_token(jti: str, expires_at: datetime, db: Session) -> None:
    revoked = RevokedToken(token_jti=jti, expires_at=expires_at)
    db.add(revoked)
    db.commit()


ROLE_HIERARCHY = {
    UserRole.admin: 6,
    UserRole.command_officer: 5,
    UserRole.rescue_officer: 4,
    UserRole.relief_officer: 3,
    UserRole.shelter_officer: 2,
    UserRole.viewer: 1,
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if jti and is_token_revoked(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(*roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_min_role(min_role: UserRole):
    def min_role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return min_role_checker


PERMISSION_MATRIX = {
    "incidents": {
        "view": ["admin", "command_officer", "rescue_officer", "relief_officer", "shelter_officer", "viewer"],
        "create": ["admin", "command_officer"],
        "update": ["admin", "command_officer"],
        "delete": ["admin"],
    },
    "teams": {
        "view": ["admin", "command_officer", "rescue_officer", "viewer"],
        "manage": ["admin", "command_officer", "rescue_officer"],
    },
    "allocations": {
        "view": ["admin", "command_officer", "rescue_officer", "viewer"],
        "create": ["admin", "command_officer", "rescue_officer"],
        "approve": ["admin", "command_officer"],
        "reallocate": ["admin", "command_officer", "rescue_officer"],
    },
    "warehouses": {
        "view": ["admin", "command_officer", "relief_officer", "viewer"],
        "manage": ["admin", "command_officer", "relief_officer"],
    },
    "relief_inventory": {
        "view": ["admin", "command_officer", "relief_officer", "viewer"],
        "mutate": ["admin", "command_officer", "relief_officer"],
    },
    "relief_requests": {
        "view": ["admin", "command_officer", "relief_officer", "viewer"],
        "create": ["admin", "command_officer", "relief_officer"],
        "approve_dispatch": ["admin", "command_officer", "relief_officer"],
    },
    "shelters": {
        "view": ["admin", "command_officer", "shelter_officer", "viewer"],
        "manage": ["admin", "command_officer", "shelter_officer"],
    },
    "shelter_requests": {
        "view": ["admin", "command_officer", "shelter_officer", "viewer"],
        "create": ["admin", "command_officer", "shelter_officer"],
        "approve_reservations": ["admin", "command_officer", "shelter_officer"],
    },
    "users": {
        "view": ["admin"],
        "manage": ["admin"],
    },
    "audit_logs": {
        "view": ["admin"],
    },
    "research": {
        "view": ["admin", "command_officer"],
    },
}


def check_permission(resource: str, action: str, user_role: UserRole) -> bool:
    role_str = user_role.value if isinstance(user_role, UserRole) else user_role
    permissions = PERMISSION_MATRIX.get(resource, {}).get(action, [])
    return role_str in permissions


def require_permission(resource: str, action: str):
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not check_permission(resource, action, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No permission to {action} {resource}"
            )
        return current_user
    return permission_checker
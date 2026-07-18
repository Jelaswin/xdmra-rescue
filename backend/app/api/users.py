from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole, AuditAction
from app.schemas import UserResponse, UserCreate, UserUpdate, AuditLogResponse, PaginatedAuditLogsResponse, PaginatedUsersResponse
from app.core.security import require_admin, get_current_active_user, hash_password, check_permission, ROLE_HIERARCHY
from app.core.audit import (
    log_user_created,
    log_user_activated,
    log_user_deactivated,
    get_audit_logs,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    user_data: UserCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    try:
        role = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {user_data.role}"
        )

    admin_level = ROLE_HIERARCHY.get(admin_user.role, 0)
    target_level = ROLE_HIERARCHY.get(role, 0)
    if target_level > admin_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create user with role higher than your own"
        )

    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=role,
        is_active=1,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_user_created(
        db=db,
        admin_user_id=admin_user.id,
        admin_email=admin_user.email,
        admin_role=admin_user.role.value,
        new_user_id=new_user.id,
        new_user_email=new_user.email,
    )

    return UserResponse.model_validate(new_user)


@router.get("", response_model=PaginatedUsersResponse)
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total = db.query(User).count()
    users = db.query(User).order_by(User.id).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [UserResponse.model_validate(u) for u in users]
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updates: UserUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if updates.email and updates.email != user.email:
        existing = db.query(User).filter(User.email == updates.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if updates.role:
        try:
            new_role = UserRole(updates.role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {updates.role}")

        admin_level = ROLE_HIERARCHY.get(admin_user.role, 0)
        target_level = ROLE_HIERARCHY.get(new_role, 0)
        if target_level > admin_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign role higher than your own"
            )

        if user.role == admin_user.role and new_role != admin_user.role:
            pass

        user.role = new_role

    if updates.full_name is not None:
        user.full_name = updates.full_name

    if updates.email is not None:
        user.email = updates.email

    if updates.is_active is not None:
        user.is_active = 1 if updates.is_active else 0

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = 1
    db.commit()
    db.refresh(user)

    log_user_activated(
        db=db,
        admin_user_id=admin_user.id,
        admin_email=admin_user.email,
        admin_role=admin_user.role.value,
        target_user_id=user.id,
        target_email=user.email,
    )

    return UserResponse.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == UserRole.admin and user.is_active == 1:
        active_admins = db.query(User).filter(
            User.role == UserRole.admin,
            User.is_active == 1
        ).count()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active administrator"
            )

    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )

    user.is_active = 0
    db.commit()
    db.refresh(user)

    log_user_deactivated(
        db=db,
        admin_user_id=admin_user.id,
        admin_email=admin_user.email,
        admin_role=admin_user.role.value,
        target_user_id=user.id,
        target_email=user.email,
    )

    return UserResponse.model_validate(user)


@router.get("/audit/logs", response_model=PaginatedAuditLogsResponse)
def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    logs, total = get_audit_logs(
        db=db,
        page=page,
        per_page=per_page,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [AuditLogResponse.model_validate(log) for log in logs]
    }
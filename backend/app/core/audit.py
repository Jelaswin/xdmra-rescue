from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import AuditLog, AuditAction


def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    user_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    success: bool = True,
    details: Optional[str] = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_method=request_method,
        request_path=request_path,
        success=1 if success else 0,
        details=details,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def log_login_success(db: Session, user_id: int, email: str, role: str, request_method: str = None, request_path: str = None):
    return create_audit_log(
        db=db,
        action=AuditAction.login_success,
        user_id=user_id,
        user_email=email,
        user_role=role,
        request_method=request_method,
        request_path=request_path,
        success=True,
    )


def log_login_failure(db: Session, email: str, request_method: str = None, request_path: str = None, details: str = None):
    return create_audit_log(
        db=db,
        action=AuditAction.login_failure,
        user_email=email,
        request_method=request_method,
        request_path=request_path,
        success=False,
        details=details,
    )


def log_logout(db: Session, user_id: int, email: str, role: str):
    return create_audit_log(
        db=db,
        action=AuditAction.logout,
        user_id=user_id,
        user_email=email,
        user_role=role,
        success=True,
    )


def log_user_created(db: Session, admin_user_id: int, admin_email: str, admin_role: str, new_user_id: int, new_user_email: str):
    return create_audit_log(
        db=db,
        action=AuditAction.user_created,
        user_id=admin_user_id,
        user_email=admin_email,
        user_role=admin_role,
        resource_type="user",
        resource_id=new_user_id,
        success=True,
        details=f"Created user: {new_user_email}",
    )


def log_user_activated(db: Session, admin_user_id: int, admin_email: str, admin_role: str, target_user_id: int, target_email: str):
    return create_audit_log(
        db=db,
        action=AuditAction.user_activated,
        user_id=admin_user_id,
        user_email=admin_email,
        user_role=admin_role,
        resource_type="user",
        resource_id=target_user_id,
        success=True,
        details=f"Activated user: {target_email}",
    )


def log_user_deactivated(db: Session, admin_user_id: int, admin_email: str, admin_role: str, target_user_id: int, target_email: str):
    return create_audit_log(
        db=db,
        action=AuditAction.user_deactivated,
        user_id=admin_user_id,
        user_email=admin_email,
        user_role=admin_role,
        resource_type="user",
        resource_id=target_user_id,
        success=True,
        details=f"Deactivated user: {target_email}",
    )


def log_incident_action(db: Session, user_id: int, email: str, role: str, action_type: str, incident_id: int, details: str = None):
    create_audit_log(
        db=db,
        action=action_type,
        user_id=user_id,
        user_email=email,
        user_role=role,
        resource_type="incident",
        resource_id=incident_id,
        success=True,
        details=details,
    )


def log_allocation_executed(db: Session, user_id: int, email: str, role: str, allocation_id: int, incident_id: int, details: str = None):
    create_audit_log(
        db=db,
        action=AuditAction.allocation_executed,
        user_id=user_id,
        user_email=email,
        user_role=role,
        resource_type="allocation",
        resource_id=allocation_id,
        success=True,
        details=f"Allocation for incident {incident_id}: {details}" if details else f"Allocation for incident {incident_id}",
    )


def log_reallocation_executed(db: Session, user_id: int, email: str, role: str, incident_id: int, details: str = None):
    create_audit_log(
        db=db,
        action=AuditAction.reallocation_executed,
        user_id=user_id,
        user_email=email,
        user_role=role,
        resource_type="incident",
        resource_id=incident_id,
        success=True,
        details=details,
    )


def log_manual_override(db: Session, user_id: int, email: str, role: str, resource_type: str, resource_id: int, details: str = None):
    create_audit_log(
        db=db,
        action=AuditAction.manual_override,
        user_id=user_id,
        user_email=email,
        user_role=role,
        resource_type=resource_type,
        resource_id=resource_id,
        success=True,
        details=details,
    )


def log_relief_inventory_mutated(db: Session, user_id: int, email: str, role: str, inventory_id: int, details: str = None):
    create_audit_log(
        db=db,
        action=AuditAction.relief_inventory_mutated,
        user_id=user_id,
        user_email=email,
        user_role=role,
        resource_type="relief_inventory",
        resource_id=inventory_id,
        success=True,
        details=details,
    )


def log_shelter_mutated(db: Session, user_id: int, email: str, role: str, shelter_id: int, details: str = None):
    create_audit_log(
        db=db,
        action=AuditAction.shelter_mutated,
        user_id=user_id,
        user_email=email,
        user_role=role,
        resource_type="shelter",
        resource_id=shelter_id,
        success=True,
        details=details,
    )


def get_audit_logs(
    db: Session,
    page: int = 1,
    per_page: int = 50,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> tuple[list[AuditLog], int]:
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return logs, total
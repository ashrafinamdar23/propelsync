from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.user_management import ManagedUserCreate, ManagedUserRead
from app.services.user_management import (
    ManagedUserNotFoundError,
    SocietyAccessInvalidError,
    UserAlreadyExistsError,
    UserManagementPermissionError,
    UserProvisioningError,
    UserRoleInvalidError,
    change_managed_user_membership_status,
    list_managed_users,
    provision_managed_user,
)
from app.tenants.context import TenantContext
from app.tenants.deps import get_tenant_context


router = APIRouter(prefix="/users")


@router.get("", response_model=list[ManagedUserRead])
def read_managed_users(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ManagedUserRead]:
    try:
        return list_managed_users(db, tenant_context=tenant_context)
    except UserManagementPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("", response_model=ManagedUserRead, status_code=status.HTTP_201_CREATED)
def create_managed_user(
    payload: ManagedUserCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ManagedUserRead:
    try:
        return provision_managed_user(
            db,
            tenant_context=tenant_context,
            payload=payload,
            actor=tenant_context.user,
        )
    except UserProvisioningError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except UserRoleInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except UserManagementPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SocietyAccessInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{user_id}/suspend", response_model=ManagedUserRead)
def suspend_managed_user(
    user_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ManagedUserRead:
    try:
        return change_managed_user_membership_status(
            db,
            tenant_context=tenant_context,
            user_id=user_id,
            status="suspended",
            actor=tenant_context.user,
        )
    except ManagedUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UserManagementPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{user_id}/activate", response_model=ManagedUserRead)
def activate_managed_user(
    user_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ManagedUserRead:
    try:
        return change_managed_user_membership_status(
            db,
            tenant_context=tenant_context,
            user_id=user_id,
            status="active",
            actor=tenant_context.user,
        )
    except ManagedUserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UserManagementPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

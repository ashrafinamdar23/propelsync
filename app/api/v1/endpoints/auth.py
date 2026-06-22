from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_platform_superuser
from app.db.deps import get_db
from app.models import User
from app.schemas.access import MyAccessRead
from app.services.access import get_my_access


router = APIRouter(prefix="/auth")


@router.get("/me")
def read_current_user(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, object]:
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "mobile_number": current_user.mobile_number,
        "full_name": current_user.full_name,
        "status": current_user.status,
        "is_platform_superuser": current_user.is_platform_superuser,
    }


@router.get("/platform-superuser")
def read_platform_superuser(
    current_user: Annotated[User, Depends(require_platform_superuser)],
) -> dict[str, object]:
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_platform_superuser": current_user.is_platform_superuser,
    }


@router.get("/my-access", response_model=MyAccessRead)
def read_my_access(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MyAccessRead:
    return get_my_access(db, current_user)

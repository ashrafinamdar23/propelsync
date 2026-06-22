import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class SocietyRoleAssignment(BaseModel):
    society_id: uuid.UUID
    role: str = Field(min_length=1, max_length=50)


class ManagedUserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    mobile_number: str | None = Field(default=None, max_length=20)
    temporary_password: str = Field(min_length=8, max_length=128)
    tenant_roles: list[str] = Field(default_factory=list)
    society_roles: list[SocietyRoleAssignment] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_email_or_mobile(self) -> "ManagedUserCreate":
        if self.email is None and not self.mobile_number:
            raise ValueError("Either email or mobile_number is required.")
        return self


class ManagedUserMembershipRead(BaseModel):
    id: uuid.UUID
    role: str
    status: str


class ManagedUserSocietyMembershipRead(ManagedUserMembershipRead):
    society_id: uuid.UUID
    society_name: str


class ManagedUserRead(BaseModel):
    id: uuid.UUID
    keycloak_subject: str
    email: str | None
    mobile_number: str | None
    full_name: str
    status: str
    is_platform_superuser: bool
    tenant_memberships: list[ManagedUserMembershipRead]
    society_memberships: list[ManagedUserSocietyMembershipRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

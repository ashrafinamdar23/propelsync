import uuid

from pydantic import BaseModel


class AccessTenant(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    roles: list[str]


class AccessSociety(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    status: str
    roles: list[str]


class MyAccessRead(BaseModel):
    is_platform_superuser: bool
    tenants: list[AccessTenant]
    societies: list[AccessSociety]

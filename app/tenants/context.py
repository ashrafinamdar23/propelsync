import uuid
from dataclasses import dataclass

from app.models import Tenant, User


@dataclass(frozen=True)
class TenantContext:
    tenant_id: uuid.UUID
    tenant: Tenant
    user: User


class TenantIsolationError(Exception):
    pass

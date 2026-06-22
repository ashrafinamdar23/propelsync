from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.scheduled_job import ScheduledDueWorkRead, ScheduledJobRunRead, ScheduledRunDueJobsRequest, ScheduledRunDueJobsResponse
from app.services.scheduled_jobs import (
    ScheduledJobExecutionError,
    ScheduledJobSocietyNotFoundError,
    get_due_work,
    list_job_runs,
    run_due_jobs,
)
from app.tenants.context import TenantContext
from app.tenants.deps import require_society_admin_context


router = APIRouter(prefix="/societies/{society_id}/scheduled-jobs")


@router.get("/due", response_model=ScheduledDueWorkRead)
def read_scheduled_due_work(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
    as_of_date: Annotated[date, Query()],
) -> ScheduledDueWorkRead:
    try:
        return get_due_work(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            as_of_date=as_of_date,
        )
    except ScheduledJobSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc


@router.get("/runs", response_model=list[ScheduledJobRunRead])
def read_scheduled_job_runs(
    society_id: uuid.UUID,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ScheduledJobRunRead]:
    try:
        runs = list_job_runs(db, tenant_context=tenant_context, society_id=society_id)
    except ScheduledJobSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    return [ScheduledJobRunRead.model_validate(run) for run in runs]


@router.post("/run-due", response_model=ScheduledRunDueJobsResponse)
def run_scheduled_due_jobs(
    society_id: uuid.UUID,
    payload: ScheduledRunDueJobsRequest,
    tenant_context: Annotated[TenantContext, Depends(require_society_admin_context)],
    db: Annotated[Session, Depends(get_db)],
) -> ScheduledRunDueJobsResponse:
    try:
        return run_due_jobs(
            db,
            tenant_context=tenant_context,
            society_id=society_id,
            payload=payload,
            actor=tenant_context.user,
        )
    except ScheduledJobSocietyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Society not found.") from exc
    except ScheduledJobExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

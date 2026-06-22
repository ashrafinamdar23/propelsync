from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Society
from app.schemas.scheduled_job import ScheduledRunDueJobsRequest
from app.services.scheduled_jobs import get_due_work, run_due_jobs
from app.services.system_actor import ensure_scheduled_jobs_system_actor
from app.tenants.context import TenantContext
from app.worker.celery_app import celery_app


@celery_app.task(name="propelsync.worker.ping")
def ping() -> dict[str, str]:
    return {"status": "ok"}


@celery_app.task(name="propelsync.scheduled_jobs.scan_due_work")
def scan_due_work(as_of_date: str | None = None) -> dict:
    target_date = date.fromisoformat(as_of_date) if as_of_date else date.today()
    session = SessionLocal()
    try:
        societies = list(
            session.scalars(
                select(Society)
                .where(Society.status == "active")
                .order_by(Society.tenant_id, Society.name)
            )
        )
        due_societies = []
        for society in societies:
            tenant_context = TenantContext(
                tenant_id=society.tenant_id,
                tenant=None,  # type: ignore[arg-type]
                user=None,  # type: ignore[arg-type]
            )
            due_work = get_due_work(
                session,
                tenant_context=tenant_context,
                society_id=society.id,
                as_of_date=target_date,
            )
            if due_work.billing_due_count == 0 and due_work.late_fee_due_count == 0:
                continue
            due_societies.append(
                {
                    "tenant_id": str(society.tenant_id),
                    "society_id": str(society.id),
                    "society_name": society.name,
                    "billing_due_count": due_work.billing_due_count,
                    "late_fee_due_count": due_work.late_fee_due_count,
                }
            )
        return {
            "as_of_date": target_date.isoformat(),
            "society_count": len(societies),
            "due_society_count": len(due_societies),
            "due_societies": due_societies,
        }
    finally:
        session.close()


@celery_app.task(name="propelsync.scheduled_jobs.run_due_jobs")
def run_due_jobs_for_all_societies(
    as_of_date: str | None = None,
    include_billing: bool = True,
    include_late_fees: bool = True,
) -> dict:
    target_date = date.fromisoformat(as_of_date) if as_of_date else date.today()
    session = SessionLocal()
    try:
        system_actor = ensure_scheduled_jobs_system_actor(session)
        societies = list(
            session.scalars(
                select(Society)
                .where(Society.status == "active")
                .order_by(Society.tenant_id, Society.name)
            )
        )
        results = []
        failures = []
        for society in societies:
            tenant_context = TenantContext(
                tenant_id=society.tenant_id,
                tenant=None,  # type: ignore[arg-type]
                user=system_actor,
            )
            try:
                due_work = get_due_work(
                    session,
                    tenant_context=tenant_context,
                    society_id=society.id,
                    as_of_date=target_date,
                )
                if due_work.billing_due_count == 0 and due_work.late_fee_due_count == 0:
                    continue

                response = run_due_jobs(
                    session,
                    tenant_context=tenant_context,
                    society_id=society.id,
                    payload=ScheduledRunDueJobsRequest(
                        as_of_date=target_date,
                        include_billing=include_billing,
                        include_late_fees=include_late_fees,
                    ),
                    actor=system_actor,
                    run_mode="scheduled",
                )
                results.append(
                    {
                        "tenant_id": str(society.tenant_id),
                        "society_id": str(society.id),
                        "society_name": society.name,
                        "billing_rule_count": response.billing_rule_count,
                        "late_fee_rule_count": response.late_fee_rule_count,
                        "generated_invoice_count": response.generated_invoice_count,
                        "generated_penalty_invoice_count": response.generated_penalty_invoice_count,
                    }
                )
            except Exception as exc:
                session.rollback()
                failures.append(
                    {
                        "tenant_id": str(society.tenant_id),
                        "society_id": str(society.id),
                        "society_name": society.name,
                        "error": str(exc),
                    }
                )

        return {
            "as_of_date": target_date.isoformat(),
            "society_count": len(societies),
            "processed_society_count": len(results),
            "failed_society_count": len(failures),
            "results": results,
            "failures": failures,
        }
    finally:
        session.close()

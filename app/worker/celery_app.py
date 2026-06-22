from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "propelsync",
    broker=settings.celery_broker_uri,
    backend=settings.celery_result_backend_uri,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    accept_content=["json"],
    result_serializer="json",
    task_serializer="json",
    task_track_started=True,
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
)

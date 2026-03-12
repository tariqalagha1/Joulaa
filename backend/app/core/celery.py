from celery import Celery

from .config import settings


celery_app = Celery(
    "joulaa",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    include=["app.tasks.orchestration_task"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.DEFAULT_TIMEZONE,
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.tasks"])

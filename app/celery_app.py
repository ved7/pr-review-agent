from __future__ import annotations

from celery import Celery

from app.config import settings


celery_app = Celery(
    "pr_reviewer",
    broker=settings.broker_url(),
    backend=settings.result_backend(),
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=60 * 60 * 24,
    task_store_eager_result=True,
)


celery_app.autodiscover_tasks(["app"])  # looks for app/tasks.py

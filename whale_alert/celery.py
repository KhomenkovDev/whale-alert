from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "whale_alert.settings")

app = Celery("whale_alert")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)  # type: ignore[untyped-decorator]
def debug_task(self: object) -> None:
    print(f"Request: {self.request!r}")  # type: ignore[attr-defined]

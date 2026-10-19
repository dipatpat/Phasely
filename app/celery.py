from celery import Celery
from celery.schedules import crontab

import app.models  # noqa: F401  (worker never imports app.main)
from app.core.config import settings

celery_app = Celery("phasely", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.update(
    timezone=settings.APP_TIMEZONE,
    beat_schedule={
        "weekly-reports-monday-6am": {
            "task": "generate_all_weekly_reports",
            "schedule": crontab(hour=6, minute=0, day_of_week="mon"),
        },
    },
)

from app.recipe import tasks as recipe_tasks  # noqa: E402,F401
from app.report import tasks as report_tasks  # noqa: E402,F401

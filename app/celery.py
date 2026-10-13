from celery import Celery

from app.core.config import settings

celery_app = Celery("phasely", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

from app.recipe import tasks as recipe_tasks  # noqa: E402,F401
from app.report import tasks as report_tasks  # noqa: E402,F401

from celery import Celery

from app.core.config import settings

celery_app = Celery("phasely", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

from app.report import tasks  # noqa: E402,F401 - import triggers task registration

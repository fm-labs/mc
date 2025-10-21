import os

from mc.config import DATA_DIR

PROJECTS_DATA_DIR=os.path.join(DATA_DIR, "projects")

MONGODB_URL = os.environ.get("MONGODB_URL", default="mongodb://mongodb:27017")

REDIS_HOST = os.environ.get("REDIS_HOST", default="redis")
REDIS_PORT = os.environ.get("REDIS_PORT", default="6379")
REDIS_DB = os.environ.get("REDIS_DB", default="0")

# Celery settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
CELERY_RESULT_EXPIRES = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "900"))
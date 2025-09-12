import os

DATA_DIR = os.environ.get("DATA_DIR", default=os.path.join(os.getcwd(), "data"))
RESOURCES_DIR = os.environ.get("RESOURCES_DIR", default=os.path.join(os.getcwd(), "resources"))
TMP_DIR = os.environ.get("TMP_DIR", default=None) # None = use system temp dir

MONGODB_URL = os.environ.get("MONGODB_URL", default="mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", default="ansible_jobs")

REDIS_HOST = os.environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", default="6379")
REDIS_DB = os.environ.get("REDIS_DB", default="0")

# Celery settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
CELERY_RESULT_EXPIRES = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "900"))
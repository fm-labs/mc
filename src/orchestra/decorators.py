import datetime
import functools
import json

from orchestra.celery import celery
from orchestra.storage.redis import get_redis_pubsub


def publishable_task(channel_key="job_id"):
    def decorator(fn):
        @celery.task(bind=True)
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            channel_id = kwargs.get(channel_key)

            # determine if the task was delayed
            if hasattr(self, "request") and hasattr(self.request, "is_delayed"):
                is_delayed = self.request.is_delayed
            else:
                is_delayed = False

            # insert in db here

            result = fn(self, *args, **kwargs)


            job_info = {
                "job_id": channel_id,
                "task_name": self.name,
                "status": "submitted" if is_delayed else "completed",
                "result": result,
                "updated_at": datetime.datetime.now(datetime.UTC)
            }

            try:
                get_redis_pubsub().publish(channel_id, json.dumps(job_info))
                # get_jobs_collection().update_one(
                #     {"job_id": job_id},
                #     {"$set": job_info},
                #     upsert=True
                # )
                return job_info
            except Exception as e:
                print(f"Error publishing task result: {e}")
                job_info["status"] = "error"
                job_info["error"] = str(e)
                # get_jobs_collection().update_one(
                #     {"job_id": job_id},
                #     {"$set": job_info},
                #     upsert=True
                # )
                return job_info
        return wrapper
    return decorator

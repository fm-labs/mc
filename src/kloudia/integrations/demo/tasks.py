import time

from orchestra.celery import celery

@celery.task
def long_running_task(duration: int):
    time.sleep(duration)
    return f"Task completed after {duration} seconds"


@celery.task
def echo_task(message: str):
    return f"Echo: {message}"
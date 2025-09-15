import time

from orchestra.celery import celery

@celery.task
def task_demo_sleep(duration: int):
    time.sleep(duration)
    return f"Task completed after {duration} seconds"


@celery.task
def task_demo_echo(message: str):
    return f"Echo: {message}"
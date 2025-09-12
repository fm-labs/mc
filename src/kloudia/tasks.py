from orchestra.celery import celery

# integration tasks
from kloudia.integrations.xscan.tasks import *
from kloudia.integrations.cloudscan.tasks import *

@celery.task
def example_task(x, y):
    return x + y


@celery.task
def sleep_task(duration: int):
    import time
    time.sleep(duration)
    return f"Task completed after {duration} seconds"

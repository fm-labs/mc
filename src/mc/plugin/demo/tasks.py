import time

from orchestra.celery import celery

@celery.task(bind=True)
def task_long_running_with_progress(self, duration: int):
    data = {}
    for i in range(duration):
        time.sleep(1)
        data['progress_' + str(i)] = int(time.time())
        self.update_state(state='PROGRESS', meta={'current': i + 1, 'total': duration, 'status': 'In progress...'})

    return data


@celery.task
def task_demo_sleep(duration: int):
    time.sleep(duration)
    return f"Task completed after {duration} seconds"


@celery.task
def task_demo_echo(message: str):
    return f"Echo: {message}"
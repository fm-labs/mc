# Make sure all tasks are imported, so that Celery can find them
# flake8: noqa
from orchestra.celery import celery
from orchestra.tasks import *
from mc.tasks import *

if __name__ == '__main__':

    print("Starting Kloudia Orchestra Worker ...")
    # Start the Celery worker
    # celery_app.start(argv=['celery', 'worker', '--loglevel=info'])
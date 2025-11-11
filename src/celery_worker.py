# Import all tasks, so that Celery can find them

# flake8: noqa
from orchestra.celery import celery

# flake8: noqa
from orchestra.tasks import *
# flake8: noqa
from mc.tasks import *
# flake8: noqa
from mc.plugin.demo.tasks import *
# flake8: noqa
from mc.plugin.xscan.tasks import *
# flake8: noqa
from mc.plugin.cloudscan.tasks import *
# flake8: noqa
from mc.plugin.tools.tasks import *


# To run the celery worker directly from this file (for development/testing purposes)
# e.g., python src/celery_worker.py
# e.g., uv run src/celery_worker.py
#
# Note: In production, it's better to run celery using the command line interface
# e.g. celery --workdir ./src -A celery_worker.celery worker --loglevel=INFO -E
if __name__ == '__main__':
    print("Starting celery worker ...")
    celery.start(argv=['celery', 'worker', '--loglevel=info'])

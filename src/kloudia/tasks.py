
# tell flake8 to ignore this file
# flake8: noqa

# Import all tasks to register them with Celery
from kloudia.integrations.demo.tasks import *
from kloudia.integrations.xscan.tasks import *
from kloudia.integrations.cloudscan.tasks import *
from kloudia.integrations.tools.tasks import *


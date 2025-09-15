
# tell flake8 to ignore this file
# flake8: noqa

# Import all tasks to register them with Celery
from kloudia.plugin.demo.tasks import *
from kloudia.plugin.xscan.tasks import *
from kloudia.plugin.cloudscan.tasks import *
from kloudia.plugin.tools.tasks import *

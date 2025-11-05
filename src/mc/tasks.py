
# tell flake8 to ignore this file
# flake8: noqa

# Import all tasks to register them with Celery
from mc.plugin.demo.tasks import *
from mc.plugin.xscan.tasks import *
from mc.plugin.cloudscan.tasks import *
from mc.plugin.tools.tasks import *
from mc.plugin.rx.tasks import *

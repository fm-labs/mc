# This files contains all celery tasks for host orchestration

from orchestra.celery import celery
from orchestra.datamodels import KoAnsibleRunModel
from orchestra.interface import ko_playbook_run


@celery.task(bind=True)
def run_ansible_playbook_task(self, project, playbook, **kwargs):
    #todo status_handler = celery_ansible_status_handler
    run: KoAnsibleRunModel = ko_playbook_run(project=project, playbook=playbook, **kwargs)
    return run.model_dump()

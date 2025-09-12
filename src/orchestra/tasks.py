# This files contains all celery tasks for host orchestration

from fastapi.encoders import jsonable_encoder

from orchestra.celery import celery
from orchestra.datamodels import KoAnsibleRunModel
from orchestra.interface import ko_playbook_run


@celery.task(bind=True)
def fake_job_task(self, task_param):
    return {
        "task_param": task_param,
        "success": True
    }


@celery.task(bind=True)
def run_ansible_playbook_task(self, project, playbook, **kwargs):
    #todo status_handler = celery_ansible_status_handler
    run: KoAnsibleRunModel = ko_playbook_run(project=project, playbook=playbook, **kwargs)
    return run.model_dump()

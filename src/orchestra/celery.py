# This file contains the celery app instance which is used to run the tasks
from celery import Celery

from orchestra import settings
from orchestra.datamodels import KoCeleryTaskInstanceModel

celery_config = dict()
celery_config['CELERY_BROKER_URL'] = settings.CELERY_BROKER_URL
celery_config['result_backend'] = settings.CELERY_RESULT_BACKEND
celery_config['result_expires'] = settings.CELERY_RESULT_EXPIRES
celery_config['task_time_limit'] = settings.CELERY_TASK_TIME_LIMIT
celery_config['task_soft_time_limit'] = int(settings.CELERY_TASK_TIME_LIMIT * 0.9)
celery_config['broker_connection_retry_on_startup'] = True

celery = Celery('ko', broker=settings.CELERY_BROKER_URL)
celery.conf.update(celery_config)


def get_celery_task_object(task_id: str):
    task = celery.AsyncResult(task_id)
    return task


def get_celery_task_instance(task_id: str) -> KoCeleryTaskInstanceModel:
    task = celery.AsyncResult(task_id)
    if task is None:
        raise Exception("Task not found")

    print(task_id, task.state, task)
    response_data = {
        'task_id': task_id,
        'task_name': getattr(task, 'task_name', None),
        'status': task.state,
        'root_id': getattr(task, 'root_id', None),
        'parent_id': getattr(task, 'parent_id', None),
        'progress': None,
        'result': None,
        'error': None
    }

    if task.state == 'PROGRESS':
        response_data['progress'] = task.info
    elif task.state == 'SUCCESS':
        try:
            result = task.result
            if isinstance(result, bytes):
                result = result.decode('utf-8')
            response_data['result'] = result
        except Exception as e:
            print(e)
            raise e
    elif task.state == 'FAILURE':
        response_data['error'] = str(task.info)

    return KoCeleryTaskInstanceModel(**response_data)

# This file contains the celery app instance which is used to run the tasks
import time
from datetime import datetime

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_internal_error

from orchestra import settings
from orchestra.mongodb_helper import get_celery_task_log_collection

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
    #global celery
    task = celery.AsyncResult(task_id)
    return task


def get_celery_task_instance(task_id: str) -> dict:
    task = celery.AsyncResult(task_id)
    if task is None:
        raise Exception("Task not found")

    print(task_id, task.state, task.info)
    response_data = {
        'task_id': task_id,
        'task_name': getattr(task, 'task_name', None),
        'status': task.state,
        'root_id': getattr(task, 'root_id', None),
        'parent_id': getattr(task, 'parent_id', None),
        'progress': None,
        'result': None,
        'error': None,
        'info': None,
        '_timestamp': int(time.time()),
    }
    print(response_data)

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

    return response_data



@task_prerun.connect
def task_started_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    print("+++ Task Started:", task_id, sender.name)
    log = {
        "task_id": task_id,
        "parent_task_id": getattr(task, 'parent_id', None),
        "task_name": sender.name,
        "state": "STARTED",
        "args": args,
        "kwargs": kwargs,
        "start_time": datetime.utcnow(),
    }

    try:
        collection = get_celery_task_log_collection()
        collection.insert_one(log)
    except Exception as e:
        print("Failed to log task start:", e)


@task_postrun.connect
def task_finished_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    print("+++ Task Finished:", task_id, state)

    try:
        collection = get_celery_task_log_collection()
        collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "state": state,
                    "end_time": datetime.utcnow(),
                    "result": str(retval),
                }
            }
        )
    except Exception as e:
        print("Failed to log task completion:", e)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    print("!!! Task Failure:", task_id, exception)

    try:
        collection = get_celery_task_log_collection()
        collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "state": "FAILURE",
                    "end_time": datetime.utcnow(),
                    "error": str(exception),
                    "traceback": str(traceback),
                }
            }
        )
    except Exception as e:
        print("Failed to log task failure:", e)


@task_internal_error.connect
def task_internal_error_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, einfo=None, **extra):
    print("!!! Internal error in task:", task_id, exception)

    try:
        collection = get_celery_task_log_collection()
        collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "state": "INTERNAL_ERROR",
                    "end_time": datetime.utcnow(),
                    "error": str(exception),
                }
            }
        )
    except Exception as e:
        print("Failed to log internal error:", e)
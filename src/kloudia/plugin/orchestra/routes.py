import asyncio
import json

from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi import WebSocket, HTTPException
from fastapi.encoders import jsonable_encoder

from kloudia.db.redis import get_redis_pubsub
from orchestra.celery import celery, get_celery_task_instance
from orchestra.datamodels import KoCeleryTaskSubmissionModel, KoCeleryTaskSubmissionResponseModel, \
    KoCeleryTaskInstanceModel, \
    KoAnsibleRunModel
from orchestra.mongodb_helper import get_ansible_runs_collection, get_celery_task_log_collection

router = APIRouter()


@router.get("/celery/jobs")
def get_celery_jobs_list() -> list:
    try:
        jobs = celery.control.inspect().active()
        return jobs if jobs else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/celery/tasks", status_code=201, response_model=KoCeleryTaskSubmissionResponseModel)
def create_celery_task(task: KoCeleryTaskSubmissionModel) -> KoCeleryTaskSubmissionResponseModel:
    """
    Create a new Celery task.
    Task name is in the payload.
    Task name is in the format of "module_name.task_name".
    :return:
    """
    try:
        task: AsyncResult = celery.send_task(task.task_name, kwargs=task.kwargs)
        return KoCeleryTaskSubmissionResponseModel(task_id=task.task_id, status="created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/celery/tasks/{task_id}")
def get_celery_task(task_id: str) -> dict:
    try:
        task_data = get_celery_task_instance(task_id)
        #task_model = KoCeleryTaskInstanceModel(**task_data)
        #return jsonable_encoder(task_model)
        return task_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/celery/logs/{task_id}")
def get_celery_task_logs(task_id: str) -> dict:
    """
    Get Celery task logs from MongoDB.
    """
    try:
        collection = get_celery_task_log_collection()
        task_log = collection.find_one({"task_id": task_id})
        if not task_log:
            raise HTTPException(status_code=404, detail="Logs not found")
        return jsonable_encoder(task_log)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ansible/runs", response_model=list[KoAnsibleRunModel])
async def get_ansible_run_records() -> list[KoAnsibleRunModel]:
    """
    Get Ansible run record from MongoDB.
    """
    collection = get_ansible_runs_collection()
    records = (collection
               .find({}, {"_id": 0, "stdout": 0, "stderr": 0, "events": 0, "stats": 0})
               .sort("created_at", -1).limit(100))

    if not records:
        #raise HTTPException(status_code=404, detail="No records found")
        return []

    # mapped_records = []
    # for record in records:
    #     mapped_records.append(jsonable_encoder(record))
    # return mapped_records
    return records

@router.get("/ansible/runs/{run_id}", response_model=KoAnsibleRunModel)
def get_ansible_run_record(run_id: str) -> KoAnsibleRunModel:
    """
    Get Ansible run record from MongoDB.
    """
    collection = get_ansible_runs_collection()
    record = collection.find_one({"run_id": run_id})
    if not record:
        raise HTTPException(status_code=404, detail="Run ID not found")
    return record


@router.websocket("/ansible/run/{run_id}/stream")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()

    pubsub = get_redis_pubsub()
    pubsub.subscribe(run_id)

    try:
        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                await websocket.send_json(data)
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        pubsub.unsubscribe(run_id)
        await websocket.close()
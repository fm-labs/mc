import asyncio
import json
from typing import AsyncGenerator

from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi import WebSocket, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from starlette.responses import StreamingResponse
from redis import asyncio as aioredis

from kloudia.db.redis import get_async_redis_client
from orchestra.celery import celery, get_celery_task_instance
from orchestra.datamodels import KoCeleryTaskSubmissionModel, KoCeleryTaskSubmissionResponseModel, KoAnsibleRunModel
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
        task: AsyncResult = celery.send_task(task.task_name, kwargs=task.parameters)
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


@router.get("/celery/task/{task_id}/logs")
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

def sse_event(data: str | dict, event: str | None = None, id: str | None = None, retry_ms: int | None = None) -> str:
    """
    Build an SSE frame. Data can be dict (will be JSON-dumped) or str.
    Each frame ends with a blank line.
    """
    if isinstance(data, (dict, list)):
        data = json.dumps(data, separators=(",", ":"))
    lines = []
    if event:
        lines.append(f"event: {event}")
    if id:
        lines.append(f"id: {id}")
    if retry_ms is not None:
        lines.append(f"retry: {retry_ms}")
    # SSE allows multiline data: prefix each with 'data: '
    for line in str(data).splitlines() or [""]:
        lines.append(f"data: {line}")
    return "".join(l + "\n" for l in lines) + "\n"

async def redis_pubsub_stream(
    r: aioredis.Redis,
    channels: list[str],
    heartbeat_interval: float = 15.0,
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE frames from Redis Pub/Sub.
    - Subscribes to channels, relays 'message' events as SSE 'message'
    - Sends heartbeat comments every `heartbeat_interval` seconds
    - Cleanly unsubscribes on client disconnect
    """
    pubsub = r.pubsub()
    await pubsub.subscribe(*channels)
    print(f"Subscribed to Redis channels: {channels}")

    # Send an initial retry suggestion so the browser auto-reconnects quickly.
    yield sse_event({"type": "stream", "status": "connected"})

    # async def pump_messages():
    #     async for msg in pubsub.listen():
    #         # Example msg:
    #         # {'type': 'message', 'pattern': None, 'channel': b'test_channel', 'data': b'{"type":"output","message":"Test message"}'}
    #         # If decode_responses=True in Redis client, then:
    #         # {'type': 'message', 'pattern': None, 'channel': 'test_channel', 'data': '{"type":"output","message":"Test message"}'}
    #
    #         # Parse the pubsub message
    #         print(f"PubSub message", msg)
    #         if msg["type"] == "subscribe":
    #             print(f"Subscribed to {msg['channel']}")
    #             # send a connected event
    #             # yield "event: status\ndata: connected\n\n"
    #             continue
    #         elif msg["type"] == "unsubscribe":
    #             print(f"Unsubscribed from {msg['channel']}")
    #             # yield "event: status\ndata: disconnected\n\n"
    #             break  # exit the pubsub listener loop
    #         elif msg['type'] == 'message':
    #
    #             # Parse the message data (= the actual ansible event payload)
    #             # Check for Ansible run completion
    #             ansible_event = json.loads(msg['data'])
    #             if ansible_event.get("type") == "status":
    #                 if ansible_event.get("data", {}).get("status") in ("successful", "failed", "error", "canceled"):
    #                     yield sse_event(ansible_event)
    #                     print("Ansible run finished, exiting PubSub stream")
    #
    #                     yield sse_event({"type": "stream", "status": "complete"})
    #                     break  # exit the pubsub listener loop
    #             elif ansible_event.get("type") == "event":
    #                 yield sse_event(ansible_event)
    #                 pass
    #
    # pump = pump_messages()
    last_hb = asyncio.get_event_loop().time()

    try:
        listen = True
        while listen:
            # try to get next message quickly without blocking the loop forever
            try:
                #chunk = await asyncio.wait_for(pump.__anext__(), timeout=1.0)
                #yield chunk

                async for msg in pubsub.listen():
                    # Example msg:
                    # {'type': 'message', 'pattern': None, 'channel': b'test_channel', 'data': b'{"type":"output","message":"Test message"}'}
                    # If decode_responses=True in Redis client, then:
                    # {'type': 'message', 'pattern': None, 'channel': 'test_channel', 'data': '{"type":"output","message":"Test message"}'}

                    # Parse the pubsub message
                    print(f"PubSub message", msg)
                    if msg["type"] == "subscribe":
                        print(f"Subscribed to {msg['channel']}")
                        # send a connected event
                        # yield "event: status\ndata: connected\n\n"
                        continue
                    elif msg["type"] == "unsubscribe":
                        print(f"Unsubscribed from {msg['channel']}")
                        # yield "event: status\ndata: disconnected\n\n"
                        break  # exit the pubsub listener loop
                    elif msg['type'] == 'message':

                        # Parse the message data (= the actual ansible event payload)
                        # Check for Ansible run completion
                        ansible_event = json.loads(msg['data'])
                        if ansible_event.get("type") == "status":
                            if ansible_event.get("data", {}).get("status") in ("successful", "failed", "error",
                                                                               "canceled"):
                                yield sse_event(ansible_event)
                                print("Ansible run finished, exiting PubSub stream")

                                yield sse_event({"type": "stream", "status": "complete"})
                                break  # exit the pubsub listener loop
                        elif ansible_event.get("type") == "event":
                            yield sse_event(ansible_event)
                            pass

                listen = False
                break
            except StopAsyncIteration:
                print("PubSub stream ended")
                break  # pubsub closed
            except asyncio.TimeoutError:
                pass  # fall through to heartbeat

            # # heartbeat to keep proxies/CDNs from closing idle connections
            # now = asyncio.get_event_loop().time()
            # if now - last_hb >= heartbeat_interval:
            #     # SSE comment line (starts with ':') is a valid heartbeat
            #     yield b": heartbeat\n\n"
            #     last_hb = now
    except asyncio.CancelledError:
        # client disconnected or server shutdown
        print("PubSub stream cancelled")
        raise
    finally:
        try:
            await pubsub.unsubscribe(*channels)
        finally:
            await pubsub.close()


@router.get("/ansible/runs/{run_id}/sse")
async def ansible_run_sse(run_id: str, request: Request):
    """
    Stream Ansible run output via Server-Sent Events (SSE)
    """
    print(f"SSE connection for run_id: {run_id}")

    # lookup run in MongoDB to verify it exists
    collection = get_ansible_runs_collection()
    record = collection.find_one({"run_id": run_id})
    if not record:
        raise HTTPException(status_code=404, detail="Run ID not found")

    # if run is not active, return the record immediately
    if record.get("status") in ("successful", "failed", "error", "canceled"):
        async def finished_event_generator() -> AsyncGenerator[str, None]:
            for event in record.get("events", []):
                yield sse_event({"type": "event", "data": event})

        return StreamingResponse(
            finished_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    r = await get_async_redis_client()
    channels = [f"ansible_run_{run_id}"]

    async def event_generator():
        # When client disconnects, Request.is_disconnected() turns True
        stream = redis_pubsub_stream(r, channels)
        try:
            async for chunk in stream:
                # Stop if client disappeared (prevents wasteful work)
                if await request.is_disconnected():
                    print("Client disconnected from SSE")
                    break
                yield chunk
        except asyncio.CancelledError:
            # Typical when client cancels
            print("SSE event generator cancelled")
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/ansible/runs/{run_id}/stream")
async def ws_ansible_run_stream(websocket: WebSocket, run_id: str):
    """
    Stream Ansible run output via WebSocket
    :deprecated: use SSE instead
    """
    await websocket.accept()

    r = await get_async_redis_client()
    pubsub = r.pubsub()
    await pubsub.subscribe(run_id)
    try:
        while True:
            message = await pubsub.get_message()
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                await websocket.send_json(data)
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await pubsub.unsubscribe(run_id)
        finally:
            try:
                await websocket.close()
            except Exception as e:
                print(f"WebSocket error: {e}")
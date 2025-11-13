import asyncio
import json
import time
from typing import List, Annotated, Any

import anyio
from docker.models.containers import Container
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query, Path
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool
from starlette.requests import Request, ClientDisconnect
from starlette.responses import StreamingResponse

from mc.plugin.containers.deps import dep_container_connection, dep_container_connections_manager

router = APIRouter()

cache = {}

def cached(cache_key, func, ttl=60):
    global cache
    def wrapper(*args, **kwargs):
        key = cache_key
        if key in cache:
            _cached = cache[key]
            if ttl > 0 and time.time() - _cached["timestamp"] < ttl:
                print(f"Cache hit for key {key}")
                return _cached["data"]
            else:
                print(f"Cache expired for key {key}")

        result = func(*args, **kwargs)
        cache[key] = {"data": result, "timestamp": time.time()}
        print(f"Cache set for key {key}")
        return result
    return wrapper

def clear_cache(cache_key):
    global cache
    if cache_key in cache:
        del cache[cache_key]
        print(f"Cache cleared for key {cache_key}")


@router.get("/containers/hosts")
def get_container_hosts(manager=Depends(dep_container_connections_manager)) -> list[dict]:
    urls = manager.urls()
    print("Container hosts", urls)
    hosts = [{"id": name, "url": url} for name, url in urls.items()]
    return hosts


@router.get("/containers/{alias}/version")
def get_docker_version(client=Depends(dep_container_connection)) -> dict:
    version_info = client.version()
    return jsonable_encoder(version_info)


@router.get("/containers/{alias}/info")
def get_docker_info(client=Depends(dep_container_connection)) -> dict:
    def fetch_info():
        _info = client.info()
        return jsonable_encoder(_info)
    return cached("info", fetch_info, ttl=120)()


@router.get("/containers/{alias}/df")
def get_docker_info(client=Depends(dep_container_connection)) -> dict:
    try:
        summary = client.df()
        return jsonable_encoder(summary)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/containers/{alias}/containers")
def list_docker_containers(alias: str, client=Depends(dep_container_connection)) -> List[dict]:
    def fetch_containers():
        collection = client.containers.list(all=True)
        print("Containers", collection)
        _containers = []
        for c in collection:
            _containers.append(c.attrs)
        return jsonable_encoder(_containers)
    return cached(f"containers_{alias}", fetch_containers, ttl=30)()


@router.get("/containers/{alias}/containers/{container_id}")
def get_docker_container(container_id: str,
                         client=Depends(dep_container_connection)) -> dict:
    def fetch_container():
        _container: Container = client.containers.get(container_id)
        return jsonable_encoder(_container.attrs)
    return cached(f"container_{container_id}", fetch_container, ttl=30)()


@router.post("/containers/{alias}/containers/{container_id}/actions/{action}")
def post_docker_container_action(alias: str, container_id: str, action: str,
                                 client=Depends(dep_container_connection)) -> dict:
    container: Container = client.containers.get(container_id)
    try:
        if action == "start":
            container.start()
        elif action == "stop":
            container.stop()
        elif action == "restart":
            container.restart()
        elif action == "pause":
            container.pause()
        elif action == "unpause":
            container.unpause()
        elif action == "remove":
            container.remove(force=True)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown action {action}")

        # refresh container state
        if action != "remove":
            try:
                container.reload()
            except Exception as e:
                pass
        #cache  cleanup
        cache_key = f"container_{container_id}"
        if cache_key in cache:
            del cache[cache_key]
        return {"action": action, "status": "ok", "message": f"Action {action} was successful"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ExecRequest(BaseModel):
    command: str


@router.post("/containers/{alias}/containers/{container_id}/exec")
def post_docker_container_exec(container_id: Annotated[str, Path()],
                               exec_req: ExecRequest,
                               client=Depends(dep_container_connection),
                               ) -> dict:
    container: Container = client.containers.get(container_id)
    command = exec_req.command
    print(f"Executing command in container {container_id}: {command}")
    if not command or command.strip() == "":
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    try:
        exec_instance = container.exec_run(cmd=command, stdout=True, stderr=True, stdin=False, tty=False)
        output = exec_instance.output.decode('utf-8', errors='replace')
        rc = exec_instance.exit_code
        return {"container_id": container_id, "command": command, "exit_code": rc, "output": output}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/containers/{alias}/containers/{container_id}/logs")
def get_docker_container_logs(container_id: str,
                              since: Annotated[int, Query()] = None,
                              until: Annotated[int, Query()] = None,
                              tail: Annotated[int, Query()] = 1000,
                              client=Depends(dep_container_connection),
                              ) -> dict:
    container: Container = client.containers.get(container_id)

    kwargs = {}
    if since:
        kwargs['since'] = since
    if until:
        kwargs['until'] = until
    if tail:
        kwargs['tail'] = tail
    logs = container.logs(**kwargs).decode('utf-8').splitlines()
    return {"container_id": container_id, "logs": logs}


@router.get("/containers/{alias}/containers/{container_id}/logs/stream")
def stream_docker_container_logs(request: Request,
                                 container_id: str,
                                 since: Annotated[int, Query()] = None,
                                 until: Annotated[int, Query()] = None,
                                 tail: Annotated[int, Query()] = 1000,
                                 follow: Annotated[bool, Query()] = True,
                                 client=Depends(dep_container_connection),
                                 ) -> StreamingResponse:
    print("Streaming logs for container", container_id)
    container: Container = client.containers.get(container_id)

    # only follow logs if container is running
    if not container.attrs['State']['Running']:
        follow = False

    kwargs: dict[str, Any] = {
        "stream": True,
        "follow": follow,
    }
    if since:
        kwargs['since'] = since
    if until:
        kwargs['until'] = until
    if tail:
        kwargs['tail'] = tail

    # get log stream (blocking iterator)
    print(f"Opening log stream, container_id={container_id} follow={follow}")
    log_stream = container.logs(**kwargs)

    # convert to async generator
    async def event_generator():
        counter = 0
        try:
            # Run the blocking iterator in a thread so we don't block the event loop
            async for chunk in iterate_in_threadpool(log_stream):

                # if client went away, stop
                if await request.is_disconnected():
                    break

                payload = chunk.decode("utf-8", errors="replace")
                counter += 1

                # SSE framing
                # yield f"event: log\n"
                yield f"data: {json.dumps({'line': counter, 'log': payload})}\n\n"

        except (ClientDisconnect, anyio.EndOfStream):
            # client disconnected while writing
            print(f"Client disconnected from log stream, container_id={container_id}")
            pass
        except asyncio.CancelledError:
            # task cancelled (some servers cancel the handler on disconnect)
            # raise
            print("Log stream cancelled")
            pass
        finally:
            # Make sure to close the iterator/socket if supported
            try:
                close = getattr(log_stream, "close", None)
                if callable(close):
                    close()
            except Exception:
                pass
            print(f"Log stream closed, container_id={container_id}")

    # return SSE response
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/containers/{alias}/images")
def list_docker_images(client=Depends(dep_container_connection)) -> List[dict]:
    collection = client.images.list()
    print("Images", collection)
    images = []
    for img in collection:
        images.append(img.attrs)
    return jsonable_encoder(images)


@router.get("/containers/{alias}/images/{image_id}")
def get_docker_image(image_id: str, client=Depends(dep_container_connection)) -> dict:
    image = client.images.get(image_id)
    return jsonable_encoder(image.attrs)


@router.get("/containers/{alias}/volumes")
def list_docker_volumes(client=Depends(dep_container_connection)) -> List[dict]:
    collection = client.volumes.list()
    print("Volumes", collection)
    volumes = []
    for img in collection:
        volumes.append(img.attrs)
    return jsonable_encoder(volumes)


@router.post("/containers/{alias}/compose/{project_name}/actions/{action}")
def post_docker_container_action(alias: str, project_name: str, action: str,
                                 client=Depends(dep_container_connection)) -> dict:

    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ExecRequest(BaseModel):
    command: str

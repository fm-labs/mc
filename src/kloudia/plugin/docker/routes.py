import asyncio
import json
from typing import List, Annotated, Any

import anyio
from docker.models.containers import Container
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query
from starlette.concurrency import iterate_in_threadpool
from starlette.requests import Request, ClientDisconnect
from starlette.responses import StreamingResponse

from kloudia.plugin.docker.helper import get_docker_client, DOCKER_HOSTS, init_container_hosts

router = APIRouter()


@router.get("/docker/hosts")
def get_container_hosts(refresh: Annotated[bool, Query()] = False) -> list[dict]:
    hosts = []
    init_container_hosts(refresh=refresh)
    for i, host in enumerate(DOCKER_HOSTS):
        hosts.append({"id": i, "url": host})
    return jsonable_encoder(hosts)


@router.get("/docker/{idx}/version")
def get_docker_version(idx: int) -> dict:
    d = get_docker_client(idx)
    version_info = d.version()
    return jsonable_encoder(version_info)


@router.get("/docker/{idx}/info")
def get_docker_info(idx: int) -> dict:
    d = get_docker_client(idx)
    info = d.info()
    return jsonable_encoder(info)


@router.get("/docker/{idx}/df")
def get_docker_info(idx: int) -> dict:
    d = get_docker_client(idx)
    try:
        summary = d.df()
        return jsonable_encoder(summary)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/docker/{idx}/containers")
def list_docker_containers(idx: int) -> List[dict]:
    d = get_docker_client(idx)
    collection = d.containers.list(all=True)
    print("Containers", collection)
    containers = []
    for c in collection:
        containers.append(c.attrs)
    return jsonable_encoder(containers)


@router.get("/docker/{idx}/containers/{container_id}")
def get_docker_container(idx: int, container_id: str) -> dict:
    d = get_docker_client(idx)
    container: Container = d.containers.get(container_id)
    return jsonable_encoder(container.attrs)


@router.post("/docker/{idx}/containers/{container_id}/actions/{action}")
def post_docker_container_action(idx: int, container_id: str, action: str) -> dict:
    d = get_docker_client(idx)
    container: Container = d.containers.get(container_id)

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
        container.reload()
        return jsonable_encoder(container.attrs)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/docker/{idx}/containers/{container_id}/logs")
def get_docker_container_logs(idx: int,
                              container_id: str,
                              since: Annotated[int, Query()] = None,
                              until: Annotated[int, Query()] = None,
                              tail: Annotated[int, Query()] = 1000,
                              ) -> dict:
    d = get_docker_client(idx)
    container: Container = d.containers.get(container_id)

    kwargs = {}
    if since:
        kwargs['since'] = since
    if until:
        kwargs['until'] = until
    if tail:
        kwargs['tail'] = tail
    logs = container.logs(**kwargs).decode('utf-8').splitlines()
    return {"container_id": container_id, "logs": logs}


@router.get("/docker/{idx}/containers/{container_id}/logs/stream")
def stream_docker_container_logs(request: Request,
                                 idx: int,
                                 container_id: str,
                                 since: Annotated[int, Query()] = None,
                                 until: Annotated[int, Query()] = None,
                                 tail: Annotated[int, Query()] = 1000,
                                 follow: Annotated[bool, Query()] = True,
                                 ) -> StreamingResponse:
    d = get_docker_client(idx)
    print("Streaming logs for container", container_id)
    container: Container = d.containers.get(container_id)

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


@router.get("/docker/{idx}/images")
def list_docker_images(idx: int) -> List[dict]:
    d = get_docker_client(idx)
    collection = d.images.list()
    print("Images", collection)
    images = []
    for img in collection:
        images.append(img.attrs)
    return jsonable_encoder(images)


@router.get("/docker/{idx}/images/{image_id}")
def get_docker_image(idx: int, image_id: str) -> dict:
    d = get_docker_client(idx)
    image = d.images.get(image_id)
    return jsonable_encoder(image.attrs)

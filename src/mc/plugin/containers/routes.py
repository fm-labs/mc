import asyncio
import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Annotated, Any, Literal

import anyio
from docker.models.containers import Container
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.params import Path, Query
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool
from starlette.requests import ClientDisconnect, Request
from starlette.responses import StreamingResponse

from mc.cache import cached_fn, clear_cache
from mc.docker.helper import docker_prune
from mc.plugin.containers.deps import ContainerClientDep, ContainerManagerDep
from mc.plugin.containers.docker_helper import list_container_dir
from mc.plugin.containers.manager import ContainerHost, enumerate_configured_container_hosts, connect_container_host
from mc.rpc import PruneScopeLiteral

router = APIRouter()

logger = logging.getLogger(__name__)

CACHE_TTL = 30  # seconds


class CommandExecRequest(BaseModel):
    command: str


@router.get("/containers/hosts")
def get_hosts(manager: ContainerManagerDep) -> list[ContainerHost]:
    configured_hosts = enumerate_configured_container_hosts()
    # add connection status to each entry
    for host in configured_hosts:
        host.connected = manager.connected(host.id)
    return jsonable_encoder(configured_hosts)

@router.get("/containers/{alias}/connect")
def connect_host(alias: str, manager: ContainerManagerDep) -> dict:
    if not manager.get(alias):
        try:
            connect_container_host(manager, alias)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    return {"id": alias, "connected": True}


@router.get("/containers/{alias}/version")
def get_engine_version(alias: str, client: ContainerClientDep) -> dict:
    def fetch_version():
        version_info = client.version()
        return jsonable_encoder(version_info)

    try:
        return cached_fn(f"containers_{alias}_version", fetch_version, ttl=3600)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/info")
def get_engine_info(alias: str, client: ContainerClientDep) -> dict:
    def fetch_info():
        _info = client.info()
        return jsonable_encoder(_info)

    try:
        return cached_fn(f"containers_{alias}_info", fetch_info, ttl=CACHE_TTL)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/df")
def get_engine_df(alias: str, client: ContainerClientDep) -> dict:
    def fetch_df():
        summary = client.df()
        return jsonable_encoder(summary)

    try:
        return cached_fn(f"containers_{alias}_df", fetch_df, ttl=CACHE_TTL)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/containers")
def list_containers(alias: str, client: ContainerClientDep) -> list[dict]:
    def fetch_containers():
        collection = client.containers.list(all=True, filters={"status": ["running", "exited", "created", "paused"]})
        print("Containers", collection)
        _containers = []
        for c in collection:
            _containers.append(c.attrs)
        return jsonable_encoder(_containers)

    try:
        return cached_fn(f"containers_{alias}_containers", fetch_containers, ttl=CACHE_TTL)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/containers/{container_id}")
def get_container(alias: str, container_id: str, client: ContainerClientDep) -> dict:
    def fetch_container():
        _container: Container = client.containers.get(container_id)
        return jsonable_encoder(_container.attrs)

    try:
        return cached_fn(f"containers_{alias}_container_{container_id}", fetch_container, ttl=CACHE_TTL)()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/containers/{alias}/containers/{container_id}/actions/{action}")
def post_container_action(alias: str, container_id: str, action: str, client: ContainerClientDep) -> dict:
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
            except Exception:
                pass

        # reset relevant caches
        cache_key = f"containers_{alias}_container_{container_id}"
        clear_cache(cache_key)
        cache_key = f"containers_{alias}_df"
        clear_cache(cache_key)
        cache_key = f"containers_{alias}_containers"
        clear_cache(cache_key)

        return {"action": action, "status": "ok", "message": f"Action {action} was successful"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/containers/{alias}/containers/{container_id}/exec")
def post_container_exec(
    alias: str,
    container_id: Annotated[str, Path()],
    exec_req: CommandExecRequest,
    client: ContainerClientDep,
) -> dict:
    container: Container = client.containers.get(container_id)
    command = exec_req.command
    print(f"Executing command in container {container_id}: {command}")
    if not command or command.strip() == "":
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    try:
        exec_instance = container.exec_run(cmd=command, stdout=True, stderr=True, stdin=False, tty=False)
        output = exec_instance.output.decode("utf-8", errors="replace")
        rc = exec_instance.exit_code
        return {"container_id": container_id, "command": command, "exit_code": rc, "output": output}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/containers/{container_id}/top")
def get_container_top(
    alias: str,
    container_id: str,
    client: ContainerClientDep,
    ps_args: Annotated[str | None, Query()] = None,
) -> dict:
    """
    Running processes of a container, like `docker top`.
    Returns {"Titles": [...], "Processes": [[...], ...]}. The container must be running.
    """
    try:
        container: Container = client.containers.get(container_id)
        kwargs = {"ps_args": ps_args} if ps_args else {}
        result = container.top(**kwargs)
        return {"Titles": result.get("Titles") or [], "Processes": result.get("Processes") or []}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/containers/{container_id}/files")
def get_container_files(
    alias: str,
    container_id: str,
    client: ContainerClientDep,
    path: Annotated[str, Query()] = "/",
) -> dict:
    """
    Entries of one directory in a container's filesystem, for a lazy-loaded file tree.
    Returns {"path": ..., "entries": [{"name", "path", "type", "is_dir", "size", "mtime"}], "truncated": bool}.
    The container must be running and have a shell (sh).
    """
    try:
        container: Container = client.containers.get(container_id)
        return list_container_dir(container, path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/containers/{container_id}/diff")
def get_container_diff(alias: str, container_id: str, client: ContainerClientDep) -> list[dict]:
    """
    Filesystem changes of a container compared to its image, like `docker diff`.
    Returns [{"Path": "/etc/hosts", "Kind": 0}, ...] with Kind 0=modified, 1=added, 2=deleted.
    """
    try:
        container: Container = client.containers.get(container_id)
        return container.diff() or []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/containers/{container_id}/logs")
def get_container_logs(
    alias: str,
    container_id: str,
    client: ContainerClientDep,
    since: Annotated[int, Query()] = 0,
    until: Annotated[int, Query()] = 0,
    tail: Annotated[int, Query()] = 100,
) -> dict:
    container: Container = client.containers.get(container_id)

    kwargs = {}
    tail = min(tail, 1000)
    kwargs["tail"] = tail

    if since > 0:
        kwargs["since"] = since
    if until > 0:
        kwargs["until"] = until

    logs = container.logs(**kwargs).decode("utf-8").splitlines()
    return {"container_id": container_id, "logs": logs}


@router.get("/containers/{alias}/containers/{container_id}/logs/stream")
def stream_container_logs(
    request: Request,
    alias: str,
    container_id: str,
    client: ContainerClientDep,
    since: Annotated[int, Query()] = 0,
    until: Annotated[int, Query()] = 0,
    tail: Annotated[int, Query()] = 100,
    follow: Annotated[bool, Query()] = True,
    format: Annotated[Literal["sse", "json"], Query()] = "json",
) -> StreamingResponse:
    print("Streaming logs for container", container_id)
    container: Container = client.containers.get(container_id)

    # only follow logs if container is running
    if not container.attrs["State"]["Running"]:
        follow = False

    kwargs: dict[str, Any] = {
        "stream": True,
        "follow": follow,
    }
    tail = min(tail, 1000)
    kwargs["tail"] = tail

    if since > 0:
        kwargs["since"] = since
    if until > 0:
        kwargs["until"] = until

    # get log stream (blocking iterator)
    print(f"Opening log stream, container_id={container_id} follow={follow}")
    _log_stream = container.logs(**kwargs)

    # convert to async generator
    async def event_generator(log_stream, format: Literal["sse", "json"] = "json"):
        counter = 0
        try:
            # Run the blocking iterator in a thread so we don't block the event loop
            async for chunk in iterate_in_threadpool(log_stream):
                # if client went away, stop
                if await request.is_disconnected():
                    print("Client disconnected from log stream, stopping generator, container_id={container_id}")
                    break

                payload = chunk.decode("utf-8", errors="replace")
                counter += 1

                # SSE framing
                if format == "sse":
                    # yield f"event: log\n"
                    yield f"data: {json.dumps({'line': counter, 'log': payload})}\n\n"
                elif format == "json":
                    yield json.dumps({"line": counter, "log": payload}) + "\n"

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

    if format == "sse":
        return StreamingResponse(
            event_generator(_log_stream, format=format),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"},
        )
    else:
        return StreamingResponse(
            event_generator(_log_stream, format=format),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/x-ndjson",
                "Transfer-Encoding": "chunked",
            },
        )


@router.get("/containers/{alias}/images")
def list_images(alias: str, client: ContainerClientDep) -> list[dict]:
    def fetch_images():
        collection = client.images.list()
        print("Images", collection)
        images = []
        for img in collection:
            images.append(img.attrs)
        return jsonable_encoder(images)

    return cached_fn(f"containers_{alias}_images", fetch_images, ttl=CACHE_TTL)()


@router.get("/containers/{alias}/images/{image_id}")
def get_image(alias: str, image_id: str, client: ContainerClientDep) -> dict:
    def fetch_image_details():
        image = client.images.get(image_id)
        return jsonable_encoder(image.attrs)

    return cached_fn(f"containers_{alias}_image_{image_id}", fetch_image_details, ttl=CACHE_TTL)()


class PullImageRequest(BaseModel):
    image: str


@router.post("/containers/{alias}/images/pull")
def pull_image(alias: str, body: PullImageRequest, client: ContainerClientDep) -> dict:
    try:
        # todo - this can take a long time, make it async and stream progress
        pulled_image = client.images.pull(body.image)
        return jsonable_encoder(pulled_image.attrs)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/containers/{alias}/volumes")
def list_volumes(alias: str, client: ContainerClientDep) -> list[dict]:
    def fetch_volumes():
        collection = client.volumes.list()
        print("Volumes", collection)
        volumes = []
        for img in collection:
            volumes.append(img.attrs)
        return jsonable_encoder(volumes)

    return cached_fn(f"containers_{alias}_volumes", fetch_volumes, ttl=CACHE_TTL)()


@router.get("/containers/{alias}/volumes/{volume_id}")
def get_volume(alias: str, volume_id: str, client: ContainerClientDep) -> dict:
    def fetch_volume_details():
        volume = client.volumes.get(volume_id)
        return jsonable_encoder(volume.attrs)

    return cached_fn(f"containers_{alias}_volume_{volume_id}", fetch_volume_details, ttl=CACHE_TTL)()


@router.get("/containers/{alias}/networks")
def list_networks(alias: str, client: ContainerClientDep) -> list[dict]:
    def fetch_networks():
        collection = client.networks.list()
        print("Networks", collection)
        networks = []
        for img in collection:
            networks.append(img.attrs)
        return jsonable_encoder(networks)

    return cached_fn(f"containers_{alias}_networks", fetch_networks, ttl=CACHE_TTL)()


# Cached list endpoints affected by each prune scope ("info" and "df" are always cleared)
_PRUNE_CACHE_KEYS: dict[str, list[str]] = {
    "containers": ["containers"],
    "images": ["images"],
    "volumes": ["volumes"],
    "networks": ["networks"],
    "buildcache": [],
    "buildx": [],
    "system": ["containers", "images", "volumes", "networks"],
}


@router.get("/containers/{alias}/prune/{scope}")
def prune_resources(alias: str,
                           scope: PruneScopeLiteral,
                           client: ContainerClientDep) -> dict:
    try:
        return docker_prune(client, scope)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        for name in ["info", "df", *_PRUNE_CACHE_KEYS.get(scope, [])]:
            clear_cache(f"containers_{alias}_{name}")


_END_OF_STREAM = object()


def _next_event(events: Iterator[Any]) -> Any:
    """next() for a worker thread: the end of the stream is returned, because StopIteration can't cross threads."""
    return next(events, _END_OF_STREAM)


def _close_event_stream(event_stream: Any) -> None:
    """
    Close the upstream connection of an event stream. The docker SDK's CancellableStream and NodeEventStream can be
    closed while another thread waits for the next event.
    """
    close = getattr(event_stream, "close", None)
    if not callable(close):
        return
    try:
        close()
    except Exception as e:
        # e.g. docker over SSH, or a plain generator that is running in a worker thread
        logger.warning(f"Could not close event stream: {e}")


@router.get("/containers/{alias}/events/stream")
async def stream_events(request: Request, alias: str, client: ContainerClientDep) -> StreamingResponse:
    # opening the stream is a blocking request to the host, so it must not run on the event loop:
    # that would stall every other request until the host answers or the connection times out
    event_stream = await run_in_threadpool(client.events, decode=True)

    async def event_generator() -> AsyncIterator[str]:
        events = iter(event_stream)
        try:
            while True:
                # abandon_on_cancel: when the client disconnects, don't wait for the next event to arrive.
                # The worker thread is freed when close() below ends its read.
                chunk = await anyio.to_thread.run_sync(_next_event, events, abandon_on_cancel=True)
                if chunk is _END_OF_STREAM:
                    break
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from event stream, alias={alias}")
                    break

                yield json.dumps(chunk) + "\n"
        except (ClientDisconnect, anyio.EndOfStream):
            logger.info(f"Client disconnected from event stream, alias={alias}")
        finally:
            _close_event_stream(event_stream)
            logger.info(f"Event stream closed, alias={alias}")

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-ndjson",
            "Transfer-Encoding": "chunked",
        },
    )


# @router.post("/containers/{alias}/compose/{project_name}/actions/{action}")
# def post_compose_action(alias: str, project_name: str, action: str,
#                                  client: ContainerClientDep) -> dict:
#     try:
#         raise HTTPException(status_code=501, detail="Not implemented yet")
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

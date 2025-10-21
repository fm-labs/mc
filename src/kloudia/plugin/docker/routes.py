import asyncio
import json
from typing import List, Annotated, Any

import anyio
from docker import DockerClient
from docker.models.containers import Container
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query, Path
from podman import PodmanClient
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool
from starlette.requests import Request, ClientDisconnect
from starlette.responses import StreamingResponse

from kloudia.inventory.storage import get_inventory_storage_instance
from kloudia.plugin.docker.manager import ContainerClientsManager, get_container_connection_manager, \
    bootstrap_container_connection_manager

router = APIRouter()


def dep_container_connection(
        alias: str,
        manager: ContainerClientsManager = Depends(get_container_connection_manager),
) -> PodmanClient:
    c = manager.get(alias)
    if not c:
       raise HTTPException(404, f"No Podman client named '{alias}'")
    # inventory = get_inventory_storage_instance()
    # item = inventory.get_item_by_name("container_host", alias)
    # if not item:
    #     raise HTTPException(404, f"No container host named '{alias}' in inventory")
    #
    # engine = item.get("properties", {}).get("engine", "docker").lower()
    # url = item.get("properties", {}).get("url")
    # if not url:
    #     raise HTTPException(400, f"Container host '{alias}' has no URL configured")
    #
    # if engine == "docker":
    #     client = DockerClient(base_url=url, timeout=15)
    # else:
    #     client = PodmanClient(base_url=url, timeout=15)
    #return client
    return c


async def dep_container_connections_manager(
        refresh: Annotated[bool, Query()] = False,
        manager: ContainerClientsManager = Depends(get_container_connection_manager),
) -> ContainerClientsManager:
    if refresh:
        print("Refreshing container connections")

        await bootstrap_container_connection_manager()
    return manager


@router.get("/docker/hosts")
def get_container_hosts(manager=Depends(dep_container_connections_manager)) -> list[dict]:
    urls = manager.urls()
    print("Container hosts", urls)
    hosts = [{"id": name, "url": url} for name, url in urls.items()]
    return hosts


@router.get("/docker/{alias}/version")
def get_docker_version(client=Depends(dep_container_connection)) -> dict:
    version_info = client.version()
    return jsonable_encoder(version_info)


@router.get("/docker/{alias}/info")
def get_docker_info(client=Depends(dep_container_connection)) -> dict:
    info = client.info()
    return jsonable_encoder(info)


@router.get("/docker/{alias}/df")
def get_docker_info(client=Depends(dep_container_connection)) -> dict:
    try:
        summary = client.df()
        return jsonable_encoder(summary)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/docker/{alias}/containers")
def list_docker_containers(client=Depends(dep_container_connection)) -> List[dict]:
    collection = client.containers.list(all=True)
    print("Containers", collection)
    containers = []
    for c in collection:
        containers.append(c.attrs)
    return jsonable_encoder(containers)


@router.get("/docker/{alias}/containers/{container_id}")
def get_docker_container(container_id: str,
                         client=Depends(dep_container_connection)) -> dict:
    container: Container = client.containers.get(container_id)
    return jsonable_encoder(container.attrs)


@router.post("/docker/{alias}/containers/{container_id}/actions/{action}")
def post_docker_container_action(container_id: str, action: str,
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
        container.reload()
        return jsonable_encoder(container.attrs)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ExecRequest(BaseModel):
    command: str


@router.post("/docker/{alias}/containers/{container_id}/exec")
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


@router.get("/docker/{alias}/containers/{container_id}/logs")
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


@router.get("/docker/{alias}/containers/{container_id}/logs/stream")
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


@router.get("/docker/{alias}/images")
def list_docker_images(client=Depends(dep_container_connection)) -> List[dict]:
    collection = client.images.list()
    print("Images", collection)
    images = []
    for img in collection:
        images.append(img.attrs)
    return jsonable_encoder(images)


@router.get("/docker/{alias}/images/{image_id}")
def get_docker_image(image_id: str, client=Depends(dep_container_connection)) -> dict:
    image = client.images.get(image_id)
    return jsonable_encoder(image.attrs)

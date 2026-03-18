import asyncio
import json
from typing import List, Annotated, Any, Literal

import anyio
from docker.models.containers import Container
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query, Path
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool
from starlette.requests import Request, ClientDisconnect
from starlette.responses import StreamingResponse

from mc.cache import cached_fn, clear_cache
from mc.inventory.storage import get_inventory_storage_instance
from mc.plugin.containers.deps import dep_container_connection, dep_container_connections_manager
from mc.plugin.containers.manager import ContainerClientsManager, NodeContainerClient

router = APIRouter()

CACHE_TTL = 30  # seconds

class CommandExecRequest(BaseModel):
    command: str


@router.get("/containers/hosts")
def get_container_hosts(manager:ContainerClientsManager=Depends(dep_container_connections_manager)) -> list[dict]:
    #storage = get_inventory_storage_instance()
    #items = storage.list_items("container_host")
    # _items = []
    # for item in items:
    #     item_copy = item.copy()
    #     item_copy["connected"] = item.get("name") in manager.names()
    #     _items.append(item_copy)

    hosts = []
    hosts.append({"id": "localdocker", "name": "localdocker", "connected": True, "properties": {
        "engine": "docker",
        "url": "unix:///var/run/docker.sock",
        "autoconnect": True,
    }})
    try:
        storage = get_inventory_storage_instance()
        items = storage.list_items("mc_node")
        for item in items:
            url = item.get("url")
            name = item.get("id")
            autoconnect = item.get("autoconnect")
            host = {
                "id": name,
                "name": name,
                "connected": False,
                "properties": {
                    "engine": "docker",
                    "url": url,
                    "autoconnect": autoconnect,
                }
            }
            # ensure connection is registered in CCM (if autoconnect is true)
            if autoconnect:
                try:
                    manager._clients.update({name: NodeContainerClient(name, url)})
                    host["connected"] = True
                except Exception as e:
                    print(f"Failed to connect to container host '{name}' at '{url}':", e)
                    host["connected"] = False

            hosts.append(host)
    except Exception as e:
        print("Failed to load container hosts from inventory:", e)

    # for name in manager.names():
    #     if name == "localdocker":
    #         continue
    #     url = f"{name}://"
    #     host = {
    #         "id": name,
    #         "name": name,
    #         "connected": True,
    #         "properties": {
    #             "engine": "docker",
    #             "url": url,
    #             "autoconnect": True,
    #         }
    #     }
    #     hosts.append(host)

    return jsonable_encoder(hosts)


@router.get("/containers/{alias}/version")
def get_docker_version(client=Depends(dep_container_connection)) -> dict:
    version_info = client.version()
    return jsonable_encoder(version_info)


@router.get("/containers/{alias}/info")
def get_docker_info(alias: str, client=Depends(dep_container_connection)) -> dict:
    def fetch_info():
        _info = client.info()
        return jsonable_encoder(_info)
    return cached_fn(f"containers_{alias}_info", fetch_info, ttl=CACHE_TTL)()


@router.get("/containers/{alias}/df")
def get_docker_info(alias: str, client=Depends(dep_container_connection)) -> dict:
    def fetch_df():
        summary = client.df()
        return jsonable_encoder(summary)
    return cached_fn(f"containers_{alias}_df", fetch_df, ttl=CACHE_TTL*2)()


@router.get("/containers/{alias}/containers")
def list_docker_containers(alias: str, client=Depends(dep_container_connection)) -> List[dict]:
    def fetch_containers():
        collection = client.containers.list(all=True, filters={"status": ["running", "exited", "created", "paused"]})
        print("Containers", collection)
        _containers = []
        for c in collection:
            _containers.append(c.attrs)
        return jsonable_encoder(_containers)
    return cached_fn(f"containers_{alias}_containers", fetch_containers, ttl=CACHE_TTL)()


@router.get("/containers/{alias}/containers/{container_id}")
def get_docker_container(alias: str, container_id: str,
                         client=Depends(dep_container_connection)) -> dict:
    def fetch_container():
        _container: Container = client.containers.get(container_id)
        return jsonable_encoder(_container.attrs)
    return cached_fn(f"containers_{alias}_container_{container_id}", fetch_container, ttl=CACHE_TTL)()


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

        # reset relevant caches
        cache_key = f"containers_{alias}_container_{container_id}"
        clear_cache(cache_key)
        cache_key = f"containers_{alias}_containers"
        clear_cache(cache_key)

        return {"action": action, "status": "ok", "message": f"Action {action} was successful"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post("/containers/{alias}/containers/{container_id}/exec")
def post_docker_container_exec(alias: str, container_id: Annotated[str, Path()],
                               exec_req: CommandExecRequest,
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
def get_docker_container_logs(alias: str, container_id: str,
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
                                 alias: str,
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
    _log_stream = container.logs(**kwargs)

    # convert to async generator
    async def event_generator(log_stream, format: Literal["sse","json"] = "json"):
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
                if format == "sse":
                    # yield f"event: log\n"
                    yield f"data: {json.dumps({'line': counter, 'log': payload})}\n\n"
                elif format == "json":
                    yield json.dumps({'line': counter, 'log': payload}) + "\n"

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
        event_generator(_log_stream),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/containers/{alias}/images")
def list_docker_images(alias: str, client=Depends(dep_container_connection)) -> List[dict]:
    def fetch_images():
        collection = client.images.list()
        print("Images", collection)
        images = []
        for img in collection:
            images.append(img.attrs)
        return jsonable_encoder(images)
    return cached_fn(f"containers_{alias}_images", fetch_images, ttl=CACHE_TTL)()


@router.get("/containers/{alias}/images/{image_id}")
def get_docker_image(alias: str, image_id: str, client=Depends(dep_container_connection)) -> dict:
    def fetch_image_details():
        image = client.images.get(image_id)
        return jsonable_encoder(image.attrs)
    return cached_fn(f"containers_{alias}_image_{image_id}", fetch_image_details, ttl=CACHE_TTL)()


@router.get("/containers/{alias}/volumes")
def list_docker_volumes(alias: str, client=Depends(dep_container_connection)) -> List[dict]:
    def fetch_volumes():
        collection = client.volumes.list()
        print("Volumes", collection)
        volumes = []
        for img in collection:
            volumes.append(img.attrs)
        return jsonable_encoder(volumes)
    return cached_fn(f"containers_{alias}_volumes", fetch_volumes, ttl=CACHE_TTL)()


# @router.post("/containers/{alias}/compose/{project_name}/actions/{action}")
# def post_docker_compose_action(alias: str, project_name: str, action: str,
#                                  client=Depends(dep_container_connection)) -> dict:
#     try:
#         raise HTTPException(status_code=501, detail="Not implemented yet")
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


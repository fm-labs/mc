import os
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.params import Query
from starlette.requests import Request

from mc.plugin.containers.manager import ContainerClient, ContainerClientsManager


def dep_ccm(request: Request) -> ContainerClientsManager:
    if not hasattr(request.app.state, "ccm"):
        raise HTTPException(500, "Container connection manager not initialized")
    return request.app.state.ccm


CCMDep = Annotated[ContainerClientsManager, Depends(dep_ccm)]


def dep_container_connection(
    alias: str,
    manager: CCMDep,
) -> ContainerClient:
    c = manager.get(alias)
    if not c:
        raise HTTPException(404, f"No container client registered named '{alias}'")
    # inventory = get_inventory_storage_instance()
    # item = inventory.get_item_by_name("container_host", alias)
    # if not item:
    #     raise HTTPException(404, f"No container host named '{alias}' in inventory")
    #
    # engine = item.get("engine", "docker").lower()
    # url = item.get("url")
    # if not url:
    #     raise HTTPException(400, f"Container host '{alias}' has no URL configured")
    #
    # if engine == "docker":
    #     client = DockerClient(base_url=url, timeout=15)
    # else:
    #     client = PodmanClient(base_url=url, timeout=15)
    # return client
    return c


ContainerClientDep = Annotated[ContainerClient, Depends(dep_container_connection)]


async def dep_container_connections_manager(
    manager: CCMDep,
    refresh: Annotated[bool, Query()] = False,
) -> ContainerClientsManager:
    # check if refresh is needed, due to ssh key changes or similar
    check_file = "/tmp/ssh-load-keys-success"
    if os.path.exists(check_file):
        print("!!! Detected SSH keys refresh, forcing container connections refresh")
        refresh = True
        os.remove(check_file)

    check_file = "/tmp/ssh-load-keys-failed"
    if os.path.exists(check_file):
        print("!!! Detected FAILED SSH key load ... ")
        # todo handle this case properly
        os.remove(check_file)

    # if refresh:
    #    print("Refreshing container connections")
    #    bootstrap_container_connection_manager()
    return manager


ContainerManagerDep = Annotated[ContainerClientsManager, Depends(dep_container_connections_manager)]

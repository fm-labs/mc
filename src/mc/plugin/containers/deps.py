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
    if c:
        return c
    raise HTTPException(404, f"No container client registered named '{alias}'")

ContainerClientDep = Annotated[ContainerClient, Depends(dep_container_connection)]


async def dep_container_connections_manager(
    manager: CCMDep,
    refresh: Annotated[bool, Query()] = False,
) -> ContainerClientsManager:
    # # check if refresh is needed, due to ssh key changes or similar
    # check_file = "/tmp/ssh-load-keys-success"
    # if os.path.exists(check_file):
    #     print("!!! Detected SSH keys refresh, forcing container connections refresh")
    #     os.remove(check_file)
    #
    # check_file = "/tmp/ssh-load-keys-failed"
    # if os.path.exists(check_file):
    #     print("!!! Detected FAILED SSH key load ... ")
    #     # handle this case properly
    #     os.remove(check_file)

    # if refresh:
    #    print("Refreshing container connections")
    #    bootstrap_container_connection_manager()
    return manager


ContainerManagerDep = Annotated[ContainerClientsManager, Depends(dep_container_connections_manager)]

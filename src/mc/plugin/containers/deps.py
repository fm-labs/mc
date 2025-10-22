from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.params import Query
from podman import PodmanClient

from mc.plugin.containers.manager import ContainerClientsManager, get_container_connection_manager, \
    bootstrap_container_connection_manager


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

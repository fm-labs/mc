from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.params import Query
from starlette.requests import Request

from mc import config
from mc.plugin.containers.manager import ContainerClient, ContainerClientsManager
from mc.plugin.containers.node_client import NodeConfig


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

    # lazy-init the container client from config
    # example:
    # "docker_hosts" : {
    #    "localhost": { "url" : "unix:///var/run/docker.sock" },
    #    "remote": { "url" : "ssh://my-remote-host" },
    #    "node": { "url" : "node+https://other-mc-node", "api_key": "..." }
    # }
    docker_host = config.CONFIG.get("docker_hosts", {}).get(alias)
    if isinstance(docker_host, dict) and docker_host.get("url"):
        url = docker_host["url"]
        try:
            if url.startswith("node+"):
                node_conf = NodeConfig.model_validate({**docker_host, "name": alias})
                return manager.ensure_node(node_conf, test_ping=False)
            return manager.ensure(alias, url, test_ping=False)
        except Exception as e:
            # 502, not 401: the UI logs out on 401
            raise HTTPException(502, f"Can't connect to container host '{alias}': {e}") from e

    # localhost fallback, if not explicitly configured
    # todo make auto-localhost fallback configurable
    if alias == "localhost":
        try:
            return manager.ensure(alias, "unix:///var/run/docker.sock", test_ping=False)
        except Exception as e:
            raise HTTPException(502, f"Can't connect to container host '{alias}': {e}") from e

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

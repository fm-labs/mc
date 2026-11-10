from typing import Sequence, Literal, Any

from fastapi.encoders import jsonable_encoder
from fastmcp.server.providers import Provider
from fastmcp.tools import Tool

from mc.plugin.containers.docker_helper import redact_container_envvars
from mc.plugin.containers.manager import enumerate_configured_container_hosts, ContainerHost, ContainerClientsManager, \
    ContainerClient

MCP_CCM: ContainerClientsManager = ContainerClientsManager()

def _get_client(alias: str = "localhost"):
    global MCP_CCM
    if MCP_CCM.get(alias) is not None:
        return MCP_CCM.get(alias)
    if alias == "localhost":
        return MCP_CCM.ensure("localhost", "unix:///var/run/docker.sock")
    raise Exception(f"Unexpected alias '{alias}'")


#@mcp.tool
def list_docker_hosts() -> list[ContainerHost]:
    """
    Returns a list of docker hosts
    """
    global MCP_CCM
    configured_hosts = enumerate_configured_container_hosts()
    # add connection status to each entry
    for host in configured_hosts:
        host.connected = MCP_CCM.connected(host.id)
    return jsonable_encoder(configured_hosts)


def list_containers(host_alias: str = "localhost") -> list[dict]:
    """List all containers"""
    def fetch_containers(client: ContainerClient):
        collection = client.containers.list(all=True, filters={"status": ["running", "exited", "created", "paused"]})
        print("Containers", collection)
        _containers = []
        for c in collection:
            # _containers.append(redact_container_envvars(c.attrs))
            _containers.append({
                "Name": c.attrs.get("Name", "/")[1:],
                "Image": c.attrs.get("Config", {}).get("Image"),
                "State": c.attrs.get("State", ""),
            })
        return jsonable_encoder(_containers)

    try:
        client = _get_client()
        containers = fetch_containers(client)
        return containers
    except Exception as e:
        raise e


def get_container_details(container_name: str, host_alias: str = "localhost") -> dict[str, Any]:
    """Get details for a container by name"""
    try:
        client = _get_client(host_alias)
        container = client.containers.get(container_name)
        return jsonable_encoder(redact_container_envvars(container.attrs))
    except Exception as e:
        raise e


def control_container(container_name: str, action: Literal["start", "stop", "restart"],
                      host_alias: str = "localhost", timeout: int = 10) -> dict:
    """Start/Stop/Restart a container"""
    try:
        client = _get_client(host_alias)
        container = client.containers.get(container_name)
        if action == "start":
            container.start()
        elif action == "stop":
            container.stop()
        elif action == "restart":
            container.restart()

        return jsonable_encoder({
            "message": f"Container action '{action}' for container '{container_name}' was successful.",
        })
    except Exception as e:
        raise e



class ContainersFastMcpProvider(Provider):
    async def _list_tools(self) -> Sequence[Tool]:
        """Return all tools this provider offers."""
        return [
            Tool.from_function(list_docker_hosts),
            Tool.from_function(list_containers),
            Tool.from_function(control_container),
            Tool.from_function(get_container_details),
        ]

    # async def _list_resources(self) -> Sequence[Resource]:
    #     """Return all resources this provider offers."""
    #     return []
    #
    # async def _list_prompts(self) -> Sequence[Prompt]:
    #     """Return all prompts this provider offers."""
    #     return []
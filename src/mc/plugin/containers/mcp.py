from typing import Sequence

from fastmcp.server.providers import Provider
from fastmcp.tools import Tool

from mc.plugin.containers.manager import enumerate_container_hosts, ContainerHost


#@mcp.tool
def list_docker_hosts() -> list[ContainerHost]:
    """
    Returns a list of docker hosts
    """
    return enumerate_container_hosts()



class ContainersFastMcpProvider(Provider):
    async def _list_tools(self) -> Sequence[Tool]:
        """Return all tools this provider offers."""
        return [
            Tool.from_function(list_docker_hosts),
        ]

    # async def _list_resources(self) -> Sequence[Resource]:
    #     """Return all resources this provider offers."""
    #     return []
    #
    # async def _list_prompts(self) -> Sequence[Prompt]:
    #     """Return all prompts this provider offers."""
    #     return []
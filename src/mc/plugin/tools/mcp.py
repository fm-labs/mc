from typing import Sequence

from fastmcp.server.providers import Provider
from fastmcp.tools import Tool

from mc.plugin.tools.toolindex import ToolSpec, enumerate_tools, get_tool_instance


#@mcp.tool
def list_tools() -> dict[str, ToolSpec]:
    """
    Returns a dict of tools installed
    """
    return enumerate_tools()


#@mcp.tool
def exec_tool(tool_name: str, params: dict | None = None) -> str:
    """
    Executes a tool and return the result
    :param tool_name: The name of the tool to execute
    :return: The result of the tool execution
    """
    tool = get_tool_instance(tool_name)
    if not tool:
        raise ValueError("Tool not found")
    try:
        params = params or {}
        return tool.execute(params=params)
    except Exception as e:
        print("exec_tool failed", tool_name)
        raise


class ToolsFastMcpProvider(Provider):
    async def _list_tools(self) -> Sequence[Tool]:
        """Return all tools this provider offers."""

        return [
            Tool.from_function(list_tools),
            Tool.from_function(exec_tool),
        ]

    # async def _list_resources(self) -> Sequence[Resource]:
    #     """Return all resources this provider offers."""
    #     return []
    #
    # async def _list_prompts(self) -> Sequence[Prompt]:
    #     """Return all prompts this provider offers."""
    #     return []
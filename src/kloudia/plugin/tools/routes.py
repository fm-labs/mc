from fastapi import APIRouter

from kloudia.plugin.tools.toolindex import get_tool_index, get_tool_def
from kloudia.plugin.tools.tasks import task_tool_exec

router = APIRouter()


@router.get("/tools")
async def list_tools():
    """
    List tools.
    """
    return get_tool_index()


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """
    Get tool details with list of commands.
    """
    tool = get_tool_def(tool_name)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found."}
    return tool


@router.post("/tools/exec/{tool_name}/{command_name}")
async def execute_tool_command(tool_name: str, command_name: str, args: dict):
    tool = get_tool_def(tool_name)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found."}
    if command_name not in tool.get("commands", {}):
        return {"error": f"Command '{command_name}' not found in tool '{tool_name}'."}

    result = task_tool_exec(tool_name, command_name, **args)
    return result


@router.post("/tools/delay/{tool_name}/{command_name}")
async def execute_tool_command_delayed(tool_name: str, command_name: str, args: dict):

    tool = get_tool_def(tool_name)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found."}
    if command_name not in tool.get("commands", {}):
        return {"error": f"Command '{command_name}' not found in tool '{tool_name}'."}

    task = task_tool_exec.delay(tool_name, command_name, **args)
    return {"task_id": task.id, "status": "started"}
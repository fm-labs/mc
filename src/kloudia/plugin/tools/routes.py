from fastapi import APIRouter

from kloudia.plugin.tools.toolindex import TOOL_INDEX
from kloudia.plugin.tools.tasks import task_tool_exec

router = APIRouter()


@router.get("/tools")
async def list_tools():
    """
    List tools.
    """
    return TOOL_INDEX


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """
    Get tool details with list of commands.
    """
    if tool_name not in TOOL_INDEX:
        return {"error": f"Tool '{tool_name}' not found."}
    return TOOL_INDEX[tool_name]


@router.post("/tools/exec/{tool_name}/{command}")
async def execute_tool_command(tool_name: str, command: str, args: dict):
    if tool_name not in TOOL_INDEX:
        return {"error": f"Tool '{tool_name}' not found."}
    if command not in TOOL_INDEX[tool_name]:
        return {"error": f"Command '{command}' not found in tool '{tool_name}'."}

    result = task_tool_exec(tool_name, command, **args)
    return result


@router.post("/tools/delay/{tool_name}/{command}")
async def execute_tool_command_delayed(tool_name: str, command: str, args: dict):
    if tool_name not in TOOL_INDEX:
        return {"error": f"Tool '{tool_name}' not found."}
    if command not in TOOL_INDEX[tool_name]:
        return {"error": f"Command '{command}' not found in tool '{tool_name}'."}

    task = task_tool_exec.delay(tool_name, command, **args)
    return {"task_id": task.id, "status": "started"}
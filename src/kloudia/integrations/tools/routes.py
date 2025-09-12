from fastapi import APIRouter

from kloudia.integrations.tools.toolindex import TOOL_INDEX
from kloudia.integrations.tools.tasks import tool_exec_task

router = APIRouter()


@router.get("/tools")
async def list_tools():
    return TOOL_INDEX


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    if tool_name not in TOOL_INDEX:
        return {"error": f"Tool '{tool_name}' not found."}
    return TOOL_INDEX[tool_name]


@router.post("/tools/{tool_name}/{command}")
async def execute_tool_command(tool_name: str, command: str, args: dict):
    if tool_name not in TOOL_INDEX:
        return {"error": f"Tool '{tool_name}' not found."}
    if command not in TOOL_INDEX[tool_name]:
        return {"error": f"Command '{command}' not found in tool '{tool_name}'."}

    if "_now" in args and args["_now"]:
        result = tool_exec_task(tool_name, command, **args)
        return result

    task = tool_exec_task.delay(tool_name, command, **args)
    return {"task_id": task.id, "status": "started"}
import json
from typing import Annotated, Literal, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.params import Body
from starlette.requests import Request
from starlette.responses import StreamingResponse

from mc.plugin.tools.toolindex import get_tool_spec, enumerate_tools, ToolSpec, get_tool_instance, CmdTool
from mc.server.stream_helper import starlette_subprocess_stream, sse_event, streaming_response

router = APIRouter()


@router.get("/tools")
async def tools_list():
    """
    List tools.
    """
    try:
        return enumerate_tools()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tools/{tool_name}")
async def tools_get_spec(tool_name: str) -> ToolSpec:
    """
    Get tool details with list of commands.
    """
    tool_spec = get_tool_spec(tool_name)
    if not tool_spec:
        raise HTTPException(status_code=404, detail="Tool not found.")
    return tool_spec


@router.post("/tools/{tool_name}")
async def tools_exec(tool_name: str, params: Annotated[dict, Body()]):
    """
    Execute command

    :param tool_name: tool name
    :param params: parameters for the tool
    :return: result of the tool execution
    """
    tool = get_tool_instance(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")

    try:
        result = tool.execute(params=params)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tools/{tool_name}/stream")
async def stream_cmd(request: Request, tool_name: str, format: Literal["sse", "json"] = "json") -> StreamingResponse:
    """
    Stream command execution

    :param request: the webserver request object
    :param tool_name: tool name
    :param format: format of the output (json or sse)
    :return: streaming response
    """
    tool = get_tool_instance(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")
    if not isinstance(tool, CmdTool):
        raise HTTPException(status_code=400, detail="Invalid tool type.")

    cmd = tool.cmd
    env = tool.env

    async def _stream_process_async() -> AsyncGenerator[str]:
        async for line in starlette_subprocess_stream(cmd, env=env, request=request):
            split = line.split(":", 1)
            if len(split) < 2:
                print("WARN: Unknown subprocess stream output: ", line)
                continue
            if format == "sse":
                yield sse_event(event=split[0], data=split[1])
            yield json.dumps({"event": split[0], "data": split[1]})

    return streaming_response(generator=_stream_process_async(), format=format)
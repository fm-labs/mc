import json
from collections.abc import AsyncGenerator
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from starlette.requests import Request

from mc.server.stream_helper import sse_event, starlette_subprocess_stream, streaming_response

router = APIRouter()


@router.get("/stream/cmd")
async def stream_cmd(request: Request, format: Literal["sse", "json"] = "sse") -> StreamingResponse:
    """
    Stream command
    """
    cmd = ["ping", "-c", "5", "google.com"]

    # def _stream_process() -> AsyncGenerator:
    #     if format == "sse":
    #         return starlette_subprocess_stream_sse(cmd, request=request)
    #     else:
    #         return starlette_subprocess_stream_json(cmd, request=request)

    async def _stream_process_async() -> AsyncGenerator:
        async for line in starlette_subprocess_stream(cmd, request=request):
            split = line.split(":", 1)
            if len(split) < 2:
                print("WARN: Unknown subprocess stream output: ", line)
                continue
            if format == "sse":
                yield sse_event(event=split[0], data=split[1])
            yield json.dumps({"event": split[0], "data": split[1]})

    return streaming_response(generator=_stream_process_async(), format=format)

# @router.get("/stream/tick")
# async def stream():
#     async def event_generator() -> AsyncGenerator:
#         counter = 0
#         try:
#             # Send an initial comment to nudge proxies to flush early
#             yield ": connected\n\n"
#             while True:
#                 counter += 1
#                 payload = {
#                     "type": "tick",
#                     "count": counter,
#                     "at": datetime.utcnow().isoformat() + "Z",
#                 }
#                 # Default message event
#                 yield sse_event(event=None, data=json.dumps(payload), event_id=str(counter))
#
#                 # Also send a named event (useful for selective listeners)
#                 ping = {"at": datetime.utcnow().isoformat() + "Z"}
#                 yield sse_event(event="ping", data=json.dumps(ping))
#
#                 # Heartbeat interval; keep < 30s for some proxies
#                 await asyncio.sleep(2)
#         except asyncio.CancelledError:
#             # Client disconnected
#             return
#
#     headers = {
#         # Recommended for SSE
#         "Cache-Control": "no-cache",
#         "Connection": "keep-alive",
#         # Helps with some reverse proxies (e.g., nginx) to disable buffering
#         "X-Accel-Buffering": "no",
#     }
#
#     return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)

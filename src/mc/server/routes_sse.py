from datetime import datetime
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
from typing import AsyncGenerator

from starlette.requests import Request

from mc.server.sse import run_subprocess_stream_sse, sse_event

router = APIRouter()


@router.get("/stream/ping")
async def stream_ping(request: Request):
    """
    Stream ping command output via SSE
    Example: GET /stream/ping
    """

    def generate() -> AsyncGenerator:
        return run_subprocess_stream_sse(["ping", "-c", "5", "google.com"], request=request)

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/stream/tick")
async def stream():
    async def event_generator() -> AsyncGenerator:
        counter = 0
        try:
            # Send an initial comment to nudge proxies to flush early
            yield ": connected\n\n"
            while True:
                counter += 1
                payload = {
                    "type": "tick",
                    "count": counter,
                    "at": datetime.utcnow().isoformat() + "Z",
                }
                # Default message event
                yield await sse_event(event=None, data=json.dumps(payload), id_=str(counter))

                # Also send a named event (useful for selective listeners)
                ping = {"at": datetime.utcnow().isoformat() + "Z"}
                yield await sse_event(event="ping", data=json.dumps(ping))

                # Heartbeat interval; keep < 30s for some proxies
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            # Client disconnected
            return

    headers = {
        # Recommended for SSE
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # Helps with some reverse proxies (e.g., nginx) to disable buffering
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(event_generator(),
                             media_type="text/event-stream",
                             headers=headers)

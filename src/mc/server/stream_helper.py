import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Literal

from starlette.requests import Request
from starlette.responses import StreamingResponse


async def starlette_subprocess_stream(
        command: list,
        env: dict | None = None,
        cwd: str | None = None,
        terminate_timeout: int = 3,
        kill_timeout: int = 1,
        request: Request | None | None = None,
) -> AsyncGenerator[str]:
    """
    Run a subprocess and yield its output line by line as SSE events.

    :param command: List of command arguments, e.g., ["ping", "-c", "5", "google.com"]
    :param env: Optional environment variables for the subprocess
    :param terminate_timeout: Time to wait after sending terminate signal before killing the process
    :param kill_timeout: Time to wait after sending kill signal before giving up
    :param request: Optional FastAPI Request object to check for client disconnection
    :yield: Lines of subprocess output, return code and error message (prefixed with "STDOUT:", "RC:", "ERROR:")
    """
    process = None
    try:
        # Start the subprocess
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Merge stderr with stdout
            env=env,
            cwd=cwd,
            # text=True
        )

        # Stream the output
        while True:
            # Check if the client has disconnected
            if request and await request.is_disconnected():
                process.terminate()
                # yield "USER:DISCONNECTED"
                break

            # yield each line
            line = await process.stdout.readline()
            if not line:
                break
            yield f"STDOUT:{line.decode('utf-8', errors='replace').strip()}"

        # Wait for the process to complete, yield return code
        rc = await process.wait()
        yield f"RC:{rc}"

        # sleep(1)  # Keep the connection open for a while to ensure client receives all data

    except Exception as e:
        yield f"ERROR:{str(e)}"
    finally:
        # process cleanup
        if process and process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass

            try:
                await asyncio.wait_for(process.wait(), timeout=terminate_timeout)
            except TimeoutError:
                process.kill()
                try:
                    await asyncio.wait_for(process.wait(), timeout=kill_timeout)
                except TimeoutError:
                    pass
            except Exception:
                pass


async def starlette_subprocess_stream_sse(
        command: list,
        env: dict | None = None,
        terminate_timeout: int = 3,
        kill_timeout: int = 1,
        request: Request | None | None = None,
) -> AsyncGenerator[str]:
    async for line in starlette_subprocess_stream(
            command,
            env=env,
            terminate_timeout=terminate_timeout,
            kill_timeout=kill_timeout,
            request=request):
        split = line.split(":", 1)
        if len(split) < 2:
            continue
        yield sse_event(event=split[0], data=split[1])


async def starlette_subprocess_stream_json(
        command: list,
        env: dict | None = None,
        terminate_timeout: int = 3,
        kill_timeout: int = 1,
        request: Request | None | None = None,
) -> AsyncGenerator[str]:
    async for line in starlette_subprocess_stream(
            command,
            env=env,
            terminate_timeout=terminate_timeout,
            kill_timeout=kill_timeout,
            request=request):
        split = line.split(":", 1)
        if len(split) < 2:
            continue
        yield json.dumps({"event": split[0], "data": split[1]})


def sse_event(event: str | None, data: str, event_id: str | None = None, retry_ms: int | None = None) -> str:
    """
    Format an SSE event. Adds required double newlines at the end.
    Lines must not exceed ~8KB.
    """
    parts = []
    if event_id is not None:
        parts.append(f"id: {event_id}")
    if event is not None:
        parts.append(f"event: {event}")
    # `data:` can appear multiple times; here we keep it simple
    for line in data.splitlines() or [""]:
        parts.append(f"data: {line}")
    if retry_ms is not None:
        parts.append(f"retry: {retry_ms}")
    # print("SSE event:", parts)
    return "\n".join(parts) + "\n\n"


def streaming_response(generator: AsyncGenerator, format: Literal["json", "sse"] = "json") -> StreamingResponse:
    media_type = "application/octet-stream"
    headers = {}

    if format == "sse":
        media_type = "text/plain"
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            # Helps with some reverse proxies (e.g., nginx) to disable buffering
            "X-Accel-Buffering": "no",
        }
    elif format == "json":
        media_type = "application/json"
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-ndjson",
            "Transfer-Encoding": "chunked",
        }
    #else:
    #    raise Exception("Unknown format")
    return StreamingResponse(generator, media_type=media_type, headers=headers)
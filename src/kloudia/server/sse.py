import asyncio
import json
from typing import Optional, AsyncGenerator

from starlette.requests import Request


async def run_subprocess_stream_sse(command: list,
                                    env: Optional[dict] = None,
                                    terminate_timeout: int = 3,
                                    kill_timeout: int = 1,
                                    request: Optional[Request] | None = None) -> AsyncGenerator[str, None]:
    """
    Run a subprocess and yield its output line by line as SSE events.

    :param command: List of command arguments, e.g., ["ping", "-c", "5", "google.com"]
    :param env: Optional environment variables for the subprocess
    :param terminate_timeout: Time to wait after sending terminate signal before killing the process
    :param kill_timeout: Time to wait after sending kill signal before giving up
    :param request: Optional FastAPI Request object to check for client disconnection
    :yield: SSE formatted strings
    """
    process = None
    try:
        # Start the subprocess
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Merge stderr with stdout
            env=env,
            # text=True
        )

        # Send initial event
        yield f"data: {json.dumps({'type': 'start', 'message': f'Started command: {' '.join(command)}'})}\n\n"

        # Stream the output
        while True:
            # Check if the client has disconnected
            if request and await request.is_disconnected():
                process.terminate()
                yield f"data: {json.dumps({'type': 'info', 'message': 'Client disconnected, terminating process.'})}\n\n"
                break

            line = await process.stdout.readline()
            if not line:
                break

            # Send each line as an SSE event
            _line = line.decode('utf-8', errors='replace').strip()
            yield f"data: {json.dumps({'type': 'output', 'message': _line})}\n\n"

        # Wait for the process to complete
        rc = await process.wait()

        # Send completion event
        yield f"data: {json.dumps({'type': 'complete', 'message': f'Process finished with exit code: {rc}'})}\n\n"

        # Optionally, send the exit code as a separate event
        #yield f"data: {json.dumps({'type': 'exit', 'code': process.returncode})}\n\n"
        #sleep(1)  # Keep the connection open for a while to ensure client receives all data

    except Exception as e:
        # Send error event
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    finally:
        # process cleanup
        if process and process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass

            try:
                await asyncio.wait_for(process.wait(), timeout=terminate_timeout)
            except asyncio.TimeoutError:
                process.kill()
                try:
                    await asyncio.wait_for(process.wait(), timeout=kill_timeout)
                except asyncio.TimeoutError:
                    pass
            except Exception:
                pass


async def sse_event(event: str | None, data: str, id_: str | None = None, retry_ms: int | None = None) -> str:
    """
    Format an SSE event. Adds required double newlines at the end.
    Lines must not exceed ~8KB.
    """
    parts = []
    if id_ is not None:
        parts.append(f"id: {id_}")
    if event is not None:
        parts.append(f"event: {event}")
    # `data:` can appear multiple times; here we keep it simple
    for line in data.splitlines() or [""]:
        parts.append(f"data: {line}")
    if retry_ms is not None:
        parts.append(f"retry: {retry_ms}")

    print("Sending SSE event:", parts)
    return "\n".join(parts) + "\n\n"

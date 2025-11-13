import asyncio
import threading
import paramiko
from paramiko.agent import AgentRequestHandler
from typing import AsyncGenerator, Tuple

Event = Tuple[str, str]  # ("stdout" | "stderr" | "exit", payload)

def _enqueue_stream(stream, kind: str, q: asyncio.Queue, loop: asyncio.AbstractEventLoop, encoding: str):
    # Read line-by-line; fall back to chunk reads if iteration isn't line-oriented
    try:
        for raw in iter(stream.readline, ""):
            if raw == "":
                break
            #asyncio.run_coroutine_threadsafe(q.put((kind, raw)), asyncio.get_event_loop())
            # push into the asyncio queue from this thread
            loop.call_soon_threadsafe(q.put_nowait, (kind, raw))
    except Exception as e:
        # Fallback to chunked reads if needed
        # while True:
        #     data = stream.read(32768)
        #     if not data:
        #         break
        #     asyncio.run_coroutine_threadsafe(
        #         q.put((kind, data if isinstance(data, str) else data.decode(encoding, "replace"))),
        #         asyncio.get_event_loop()
        #     )
        print(f"[{kind}] {stream}: Exception while reading stream: {e}")
    finally:
        #asyncio.run_coroutine_threadsafe(q.put((f"{kind}_done", "")), asyncio.get_event_loop())
        loop.call_soon_threadsafe(q.put_nowait, (f"{kind}_done", ""))


async def ssh_exec_command_stream(
    client: paramiko.SSHClient,
    command: str,
    *,
    agent_forward: bool = False,
    encoding: str = "utf-8",
) -> AsyncGenerator[Event, None]:
    """
    Yields ("stdout", line_or_chunk) / ("stderr", line_or_chunk) as soon as they arrive.
    Finishes with ("exit", "<code>").
    """
    transport = client.get_transport()
    chan = transport.open_session()
    if agent_forward:
        AgentRequestHandler(chan)

    chan.exec_command(command)

    stdout = chan.makefile("r", -1) #, encoding=encoding, errors="replace")
    stderr = chan.makefile_stderr("r", -1) #, encoding=encoding, errors="replace")

    q: asyncio.Queue[Tuple[str, str]] = asyncio.Queue()
    #loop = asyncio.get_event_loop()
    loop = asyncio.get_running_loop() # since Python 3.10, captures the current running loop

    t_out = threading.Thread(target=_enqueue_stream, args=(stdout, "stdout", q, loop, encoding), daemon=True)
    t_err = threading.Thread(target=_enqueue_stream, args=(stderr, "stderr", q, loop, encoding), daemon=True)
    t_out.start(); t_err.start()

    stdout_done = False
    stderr_done = False

    while True:
        # If both streams done and exit status ready, finish
        if stdout_done and stderr_done and chan.exit_status_ready():
            yield "exit", str(chan.recv_exit_status())
            chan.close()
            return

        try:
            kind, payload = await asyncio.wait_for(q.get(), timeout=0.05)
        except asyncio.TimeoutError:
            # Periodically check for exit status even if no output arrives
            if chan.exit_status_ready() and stdout_done and stderr_done:
                yield "exit", str(chan.recv_exit_status())
                chan.close()
                return
            continue

        if kind == "stdout_done":
            stdout_done = True
        elif kind == "stderr_done":
            stderr_done = True
        else:
            yield kind, payload

"""
The container events stream route: opening the stream must not block the event loop, and the upstream connection
must be closed as soon as the client disconnects, not when the next event arrives.
"""

import asyncio
import json
import socket
import threading
import time
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mc.plugin.containers.manager import ContainerClientsManager
from mc.plugin.containers.node_client import NodeApiError, NodeContainerClient

EVENT = {"Type": "container", "Action": "start"}


class BlockingEventStream:
    """Yields one event, then blocks like a quiet docker host until close() is called from another thread."""

    def __init__(self) -> None:
        self.sent = False
        self.waiting = threading.Event()
        self.closed = threading.Event()

    def __iter__(self):
        return self

    def __next__(self):
        if not self.sent:
            self.sent = True
            return EVENT
        self.waiting.set()
        # the timeout only keeps a broken test from leaving the thread behind for good
        self.closed.wait(timeout=10)
        raise StopIteration

    def close(self):
        self.closed.set()


class FakeEventsClient:
    def __init__(self, stream) -> None:
        self.stream = stream
        self.opened_on_event_loop: bool | None = None

    def events(self, decode=True):
        try:
            asyncio.get_running_loop()
            self.opened_on_event_loop = True
        except RuntimeError:
            self.opened_on_event_loop = False
        if isinstance(self.stream, Exception):
            raise self.stream
        return self.stream

    def close(self):
        pass


def make_app(client) -> FastAPI:
    from mc.plugin.containers.routes import router

    app = FastAPI()
    app.state.ccm = ContainerClientsManager()
    app.state.ccm.register("host1", client, "docker+fake")
    app.include_router(router, prefix="/api")
    return app


def test_streams_events_and_opens_off_the_event_loop():
    client = FakeEventsClient(iter([EVENT, {"Type": "container", "Action": "stop"}]))
    r = TestClient(make_app(client)).get("/api/containers/host1/events/stream")
    assert r.status_code == 200
    assert [json.loads(line) for line in r.text.splitlines()] == [EVENT, {"Type": "container", "Action": "stop"}]
    assert client.opened_on_event_loop is False


def test_open_error_is_returned():
    client = FakeEventsClient(NodeApiError(502, "Node http://srv04:3080 is unreachable"))
    r = TestClient(make_app(client)).get("/api/containers/host1/events/stream")
    assert r.status_code == 502


async def test_disconnect_closes_upstream_without_waiting_for_an_event():
    stream = BlockingEventStream()
    app = make_app(FakeEventsClient(stream))
    request_sent = False

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        # the client goes away while the server waits for the next event
        await asyncio.to_thread(stream.waiting.wait, 5)
        return {"type": "http.disconnect"}

    async def send(message):
        pass

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/containers/host1/events/stream",
        "raw_path": b"/api/containers/host1/events/stream",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    # before the fix, the response only ended when the next event arrived (never, here)
    await asyncio.wait_for(app(scope, receive, send), timeout=3)
    assert stream.closed.is_set()


@pytest.fixture
def quiet_node() -> Iterator[str]:
    """A node that sends one event on its event stream and then keeps the connection open without sending more."""
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    done = threading.Event()

    def serve():
        conn, _ = server.accept()
        with conn:
            conn.recv(65536)
            line = json.dumps(EVENT).encode() + b"\n"
            conn.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/x-ndjson\r\nTransfer-Encoding: chunked\r\n\r\n"
                + f"{len(line):x}\r\n".encode()
                + line
                + b"\r\n"
            )
            done.wait(timeout=10)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.getsockname()[1]}"
    done.set()
    thread.join(timeout=5)
    server.close()


def test_node_event_stream_close_ends_a_blocked_read(quiet_node):
    events = NodeContainerClient(base_url=quiet_node).events(decode=True)
    assert next(events) == EVENT

    result: list[object] = []
    reader = threading.Thread(target=lambda: result.append(next(events, "end")), daemon=True)
    reader.start()
    time.sleep(0.2)
    assert reader.is_alive(), "the read should wait for the next event"

    events.close()
    reader.join(timeout=2)
    assert not reader.is_alive(), "close() should end the blocked read"
    assert result == ["end"]

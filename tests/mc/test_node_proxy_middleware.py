"""
Tests for mc.server.middleware.node_proxy_middleware: forwarding requests with an `x-mc-node` header to another node.

The upstream node is an httpx.MockTransport, so no network is used.
"""

import gzip
from collections.abc import Callable, Iterator

import httpx
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mc.server.auth_helper import create_jwt_access_token
from mc.server.middleware import node_proxy_middleware as npm
from mc.server.middleware.node_proxy_middleware import NodeProxyMiddleware

NODES = {"node1": ("http://node1:3080/", "node1-key"), "nokey": ("http://nokey:3080", None)}


class _Stream(httpx.AsyncByteStream):
    def __init__(self, body: bytes):
        self.body = body

    async def __aiter__(self):
        yield self.body


def _response(status: int = 200, body: bytes = b"", headers=None) -> httpx.Response:
    """An upstream response with a streamed body, like a real one (a bytes body counts as already read)."""
    return httpx.Response(status, headers=headers, stream=_Stream(body))


class Upstream:
    """Fake upstream node: records the requests it gets and answers with `handler`."""

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self.bodies: list[bytes] = []
        self.handler: Callable[[httpx.Request], httpx.Response] = lambda r: _response(200, b"from node")

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.bodies.append(await request.aread())
        self.requests.append(request)
        return self.handler(request)


async def local_endpoint(request: Request):
    return PlainTextResponse(f"local {request.method} {request.url.path}")


@pytest.fixture
def upstream(monkeypatch) -> Upstream:
    upstream = Upstream()
    real_async_client = httpx.AsyncClient
    # The middleware creates its client lazily, so inject the mock transport there and keep its other settings.
    transport = httpx.MockTransport(upstream)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real_async_client(transport=transport, **kw))
    monkeypatch.setattr(npm, "get_node_proxy_config", NODES.get)
    return upstream


@pytest.fixture
def middleware(upstream) -> NodeProxyMiddleware:
    app = Starlette(routes=[Route("/{path:path}", local_endpoint, methods=["GET", "POST", "PUT", "DELETE"])])
    return NodeProxyMiddleware(app)


@pytest.fixture
def client(middleware) -> Iterator[TestClient]:
    # `with` runs the lifespan and keeps one event loop for all requests of a test
    with TestClient(middleware) as client:
        yield client


@pytest.fixture
def auth() -> dict[str, str]:
    return {"authorization": f"Bearer {create_jwt_access_token({'sub': 'operator'})}"}


def _node(auth: dict[str, str], node: str = "node1") -> dict[str, str]:
    return {**auth, "x-mc-node": node}


# --- requests that stay local --------------------------------------------------------------------------------------


def test_without_header_is_handled_locally(client, upstream):
    response = client.get("/api/ping")
    assert response.text == "local GET /api/ping"
    assert upstream.requests == []


def test_localhost_node_is_handled_locally(client, upstream, auth):
    response = client.get("/api/ping", headers=_node(auth, "localhost"))
    assert response.text == "local GET /api/ping"
    assert upstream.requests == []


def test_default_node_is_handled_locally(client, upstream, auth):
    response = client.get("/api/ping", headers=_node(auth, "default"))
    assert response.text == "local GET /api/ping"
    assert upstream.requests == []


# --- disabled proxy ------------------------------------------------------------------------------------------------


def test_disabled_proxy_refuses_to_forward(middleware, upstream, auth):
    disabled = NodeProxyMiddleware(middleware.app, enabled=False)
    with TestClient(disabled) as client:
        response = client.get("/api/ping", headers=_node(auth))

    assert response.status_code == 404
    assert upstream.requests == []


def test_disabled_proxy_still_handles_local_requests(middleware, upstream, auth):
    disabled = NodeProxyMiddleware(middleware.app, enabled=False)
    with TestClient(disabled) as client:
        assert client.get("/api/ping").text == "local GET /api/ping"
        assert client.get("/api/ping", headers=_node(auth, "localhost")).text == "local GET /api/ping"


def test_empty_header_is_handled_locally(client, upstream):
    response = client.get("/api/ping", headers={"x-mc-node": ""})
    assert response.text == "local GET /api/ping"
    assert upstream.requests == []


# --- auth and node lookup ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("headers", [
    {},
    {"authorization": "Bearer not-a-jwt"},
    {"authorization": "Basic dXNlcjpwYXNz"},
    {"x-api-key": "some-api-key"},  # API keys are not accepted for proxying, only JWTs
])
def test_unauthenticated_request_is_rejected(client, upstream, headers):
    response = client.get("/api/ping", headers={**headers, "x-mc-node": "node1"})
    assert response.status_code == 401
    assert upstream.requests == []


def test_unknown_node_returns_404(client, upstream, auth):
    response = client.get("/api/ping", headers=_node(auth, "nope"))
    assert response.status_code == 404
    assert response.text == "Node not found"
    assert upstream.requests == []


# --- forwarded request ---------------------------------------------------------------------------------------------


def test_forwards_method_path_and_body(client, upstream, auth):
    response = client.post("/api/rpc", headers=_node(auth), content=b'{"jsonrpc": "2.0"}')

    assert response.status_code == 200
    assert response.text == "from node"
    [request] = upstream.requests
    assert request.method == "POST"
    assert str(request.url) == "http://node1:3080/api/rpc"
    assert upstream.bodies == [b'{"jsonrpc": "2.0"}']


def test_keeps_raw_path_and_query_string(client, upstream, auth):
    client.get("/api/a%2Fb/x%20y?a=1&a=2&flag=&q=%C3%A4", headers=_node(auth))

    [request] = upstream.requests
    assert request.url.raw_path == b"/api/a%2Fb/x%20y?a=1&a=2&flag=&q=%C3%A4"


def test_replaces_credentials_with_node_api_key(client, upstream, auth):
    client.get("/api/ping", headers={**_node(auth), "x-api-key": "client-key", "cookie": "session=secret"})

    [request] = upstream.requests
    assert request.headers.get_list("x-api-key") == ["node1-key"]
    assert "authorization" not in request.headers
    assert "cookie" not in request.headers


def test_node_without_api_key_gets_no_key(client, upstream, auth):
    response = client.get("/api/ping", headers={**_node(auth, "nokey"), "x-api-key": "client-key"})

    assert response.status_code == 200
    [request] = upstream.requests
    assert "x-api-key" not in request.headers


def test_strips_node_header_and_hop_by_hop_headers(client, upstream, auth):
    client.get("/api/ping", headers={**_node(auth), "connection": "keep-alive", "keep-alive": "timeout=5"})

    [request] = upstream.requests
    # removing x-mc-node keeps the target node from proxying the request again
    assert "x-mc-node" not in request.headers
    assert "keep-alive" not in request.headers
    # httpx sets its own host for the target node
    assert request.headers["host"] == "node1:3080"


def test_keeps_other_and_repeated_request_headers(client, upstream, auth):
    headers = [*_node(auth).items(), ("x-custom", "1"), ("x-custom", "2"), ("accept", "application/json")]
    client.get("/api/ping", headers=headers)

    [request] = upstream.requests
    assert request.headers.get_list("x-custom") == ["1", "2"]
    assert request.headers["accept"] == "application/json"


# --- forwarded response --------------------------------------------------------------------------------------------


def test_returns_upstream_status_and_headers(client, upstream, auth):
    upstream.handler = lambda r: _response(
        404,
        b'{"detail": "No such container"}',
        headers=[("content-type", "application/json"), ("x-dup", "a"), ("x-dup", "b"), ("set-cookie", "s=1")],
    )
    response = client.get("/api/ping", headers=_node(auth))

    assert response.status_code == 404
    assert response.json() == {"detail": "No such container"}
    assert response.headers["content-type"] == "application/json"
    assert response.headers.get_list("x-dup") == ["a", "b"]
    assert "set-cookie" not in response.headers


def test_passes_compressed_body_through_unchanged(client, upstream, auth):
    upstream.handler = lambda r: _response(200, gzip.compress(b"compressed body"), headers={"content-encoding": "gzip"})
    response = client.get("/api/ping", headers=_node(auth))

    assert response.headers["content-encoding"] == "gzip"
    assert response.text == "compressed body"


def test_does_not_store_node_cookies(client, upstream, auth):
    upstream.handler = lambda r: _response(200, headers={"set-cookie": "session=node-secret; Path=/"})
    client.get("/api/ping", headers=_node(auth))
    client.get("/api/ping", headers=_node(auth))

    assert [r.headers.get("cookie") for r in upstream.requests] == [None, None]


# --- upstream errors -----------------------------------------------------------------------------------------------


def test_rejected_api_key_returns_502(client, upstream, auth):
    # a 401 from the node means our api_key is wrong; it must not log the user out of the local UI
    upstream.handler = lambda r: _response(401, b"Unauthenticated")
    response = client.get("/api/ping", headers=_node(auth))

    assert response.status_code == 502
    assert response.text == "Proxy authentication error"


def test_timeout_returns_504(client, upstream, auth):
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    upstream.handler = handler
    response = client.get("/api/ping", headers=_node(auth))

    assert response.status_code == 504
    assert response.text == "Upstream node timed out"


def test_unreachable_node_returns_502(client, upstream, auth):
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    upstream.handler = handler
    response = client.get("/api/ping", headers=_node(auth))

    assert response.status_code == 502
    assert response.text == "Upstream node unreachable"


# --- client lifecycle ----------------------------------------------------------------------------------------------


def test_client_is_closed_on_shutdown(middleware, auth):
    with TestClient(middleware) as client:
        client.get("/api/ping", headers=_node(auth))
        http_client = middleware._client
        assert http_client is not None and not http_client.is_closed

    assert http_client.is_closed


def test_client_is_reused_between_requests(client, middleware, auth):
    client.get("/api/ping", headers=_node(auth))
    first = middleware._client
    client.get("/api/ping", headers=_node(auth))
    assert middleware._client is first


def test_client_settings(middleware):
    proxy = NodeProxyMiddleware(middleware.app, timeout=5.0, follow_redirects=True)
    assert proxy.client.timeout == httpx.Timeout(5.0)
    assert proxy.client.follow_redirects is True
    assert NodeProxyMiddleware(middleware.app).client.follow_redirects is False


# --- target url ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("base_url", "path", "query", "expected"), [
    ("http://node1:3080", "/api/x", b"", "http://node1:3080/api/x"),
    ("http://node1:3080/", "/api/x", b"", "http://node1:3080/api/x"),
    ("https://node1:3443/mc", "/api/x", b"a=1", "https://node1:3443/mc/api/x?a=1"),
])
def test_build_target_url(base_url, path, query, expected):
    request = Request({"type": "http", "path": path, "raw_path": path.encode(), "query_string": query, "headers": []})
    assert str(NodeProxyMiddleware._build_target_url(base_url, request)) == expected

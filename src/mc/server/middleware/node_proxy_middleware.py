import logging
from http.cookiejar import CookieJar, DefaultCookiePolicy

import httpx
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import PlainTextResponse, StreamingResponse

from mc.config import get_node_proxy_config
from mc.server.auth_helper import verify_jwt_access_token

logger = logging.getLogger(__name__)

_EXCLUDED_REQUEST_HEADERS = {
    b"host", b"content-length", b"connection", b"keep-alive", b"proxy-authorization",
    b"te", b"trailer", b"transfer-encoding", b"upgrade",
    b"cookie", # never forward client cookies
    b"authorization",  # replaced by the target node's API key
    b"x-api-key",  # never forward a client-supplied key
    b"x-mc-node",  # prevents the target node from proxying again (loop)
}
_EXCLUDED_RESPONSE_HEADERS = {
    b"content-length", b"connection", b"keep-alive", b"transfer-encoding",
    b"te", b"trailer", b"upgrade", b"proxy-authenticate", b"set-cookie"
}


class NodeProxyMiddleware:
    """
    Proxies HTTP requests carrying an `x-mc-node` header to that node.

    Example:
        app.add_middleware(NodeProxyMiddleware, timeout=30.0)
    """

    def __init__(self, app, timeout: float = 30.0, follow_redirects: bool = False, enabled: bool = True):
        self.app = app
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.enabled = enabled
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        # Created lazily so it binds to the running event loop.
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=self.follow_redirects,
                # The client is shared by every caller, so it must never store
                # cookies from a node and replay them on someone else's request.
                cookies=CookieJar(policy=DefaultCookiePolicy(allowed_domains=[])),
            )
        return self._client

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            await self.app(scope, self._wrap_lifespan_receive(receive), send)
            return

        if scope["type"] == "http":
            request = Request(scope, receive)
            node_name = request.headers.get("x-mc-node")
            if node_name and node_name != "localhost" and node_name != "default":
                response = await self.proxy_request(request, node_name)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    def _wrap_lifespan_receive(self, receive):
        # Starlette never calls __aenter__/__aexit__ on middleware, so close the
        # client when the server shuts down instead.
        async def wrapped():
            message = await receive()
            if message["type"] == "lifespan.shutdown" and self._client is not None:
                await self._client.aclose()
            return message

        return wrapped

    @staticmethod
    def _validate_request(request: Request) -> bool:
        authorization_header = request.headers.get("authorization")
        if authorization_header and authorization_header.lower().startswith("bearer "):
            token = authorization_header[len("bearer "):].strip()
            try:
                verify_jwt_access_token(token)
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def _build_target_url(base_url: str, request: Request) -> httpx.URL:
        # Use the raw path and query string from the ASGI scope so the original
        # percent-encoding, repeated keys (?a=1&a=2) and blank values (?flag=)
        # reach the node exactly as the client sent them.
        raw_path = request.scope.get("raw_path") or request.scope["path"].encode()
        url = httpx.URL(base_url.rstrip("/") + raw_path.decode("latin-1"))
        query = request.scope.get("query_string", b"")
        return url.copy_with(query=query) if query else url

    async def proxy_request(self, request: Request, node_name: str):
        if not self.enabled:
            return PlainTextResponse("Node not found", status_code=404)

        # Validate the request first!
        if not self._validate_request(request):
            logger.warning("Unauthorized proxy request for node %s", node_name)
            return PlainTextResponse("Unauthorized", status_code=401)

        node_proxy = get_node_proxy_config(node_name)
        if node_proxy is None:
            return PlainTextResponse("Node not found", status_code=404)

        base_url, api_key = node_proxy
        target_url = self._build_target_url(base_url, request)

        # A list of tuples keeps repeated headers that a dict would collapse.
        headers = [
            (k, v) for k, v in request.headers.raw
            if k.lower() not in _EXCLUDED_REQUEST_HEADERS
        ]
        # Inject api key. Without one the node decides; if it requires a key, its 401 becomes a 502 below.
        if api_key:
            headers.append((b"x-api-key", api_key.encode()))

        logger.debug("Proxying %s %s to node %s", request.method, request.url.path, node_name)

        upstream_request = self.client.build_request(
            request.method,
            target_url,
            headers=headers,
            content=request.stream(),  # stream the body instead of buffering it
        )
        try:
            upstream = await self.client.send(upstream_request, stream=True)
        except httpx.TimeoutException:
            logger.warning("Timeout proxying to node %s", node_name)
            return PlainTextResponse("Upstream node timed out", status_code=504)
        except httpx.RequestError as e:
            logger.warning("Error proxying to node %s: %r", node_name, e)
            return PlainTextResponse("Upstream node unreachable", status_code=502)

        if upstream.status_code == 401:
            # Our API key for that node was rejected; that's a gateway problem,
            # not the caller's credentials.
            await upstream.aclose()
            logger.error("Node %s rejected the proxy API key", node_name)
            return PlainTextResponse("Proxy authentication error", status_code=502)

        response = StreamingResponse(
            upstream.aiter_raw(),  # raw bytes, so content-encoding stays valid
            status_code=upstream.status_code,
            background=BackgroundTask(upstream.aclose),
        )
        # raw_headers keeps duplicates such as multiple set-cookie headers.
        response.raw_headers = [
            (k.lower(), v) for k, v in upstream.headers.raw
            if k.lower() not in _EXCLUDED_RESPONSE_HEADERS
        ]
        # response.raw_headers.append((b"x-mc-gateway", b"localhost"))
        return response

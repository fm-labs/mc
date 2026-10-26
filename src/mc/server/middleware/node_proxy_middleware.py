"""
MC Node Proxy Middleware for FastAPI

This middleware proxies requests that carry an "x-mc-node" header to an external server.
Useful for API gateways and service routing.
"""

import httpx
from fastapi import Request, Response
from fastapi.responses import StreamingResponse


class NodeProxyMiddleware:
    """
    Middleware that proxies requests to an external server.
    
    Args:
        app: FastAPI application instance
        timeout: Request timeout in seconds (default: 30.0)
        follow_redirects: Whether to follow redirects (default: False)
    
    Example:
        app.add_middleware(
            NodeProxyMiddleware
        )
    """
    
    def __init__(
        self, 
        app,
        timeout: float = 30.0,
        follow_redirects: bool = False
    ):
        self.app = app
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=follow_redirects
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Check if the request has the "x-mc-node" header
            if "x-mc-node" in request.headers:
                response = await self.proxy_request(request)
                await response(scope, receive, send)
                return
        
        # If not a proxy request, continue with normal processing
        await self.app(scope, receive, send)

    async def proxy_request(self, request: Request) -> Response:
        """
        Proxy the request to the target server.
        
        Args:
            request: The incoming FastAPI request
            
        Returns:
            Response: The proxied response
        """
        # Remove the proxy prefix and construct target URL
        target_path = request.url.path[len(self.path_prefix):].lstrip("/")
        target_url = f"{self.target_url}/{target_path}"
        
        # Include query parameters
        if request.url.query:
            target_url += f"?{request.url.query}"

        # Prepare headers (exclude host and other problematic headers)
        headers = {}
        excluded_headers = {"host", "content-length", "connection"}
        
        for name, value in request.headers.items():
            if name.lower() not in excluded_headers:
                headers[name] = value

        try:
            # Get request body
            body = await request.body()
            
            # Make the proxy request
            proxy_response = await self.client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body
            )

            # Prepare response headers (exclude problematic ones)
            response_headers = {}
            excluded_response_headers = {
                "content-length", "transfer-encoding", "connection"
            }
            
            for name, value in proxy_response.headers.items():
                if name.lower() not in excluded_response_headers:
                    response_headers[name] = value

            # Return streaming response for better memory efficiency
            async def generate():
                async for chunk in proxy_response.aiter_bytes():
                    yield chunk

            return StreamingResponse(
                generate(),
                status_code=proxy_response.status_code,
                headers=response_headers
            )

        except httpx.RequestError as e:
            return Response(
                content=f"Proxy error: {str(e)}",
                status_code=502,
                headers={"content-type": "text/plain"}
            )
        except Exception as e:
            return Response(
                content=f"Internal proxy error: {str(e)}",
                status_code=500,
                headers={"content-type": "text/plain"}
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

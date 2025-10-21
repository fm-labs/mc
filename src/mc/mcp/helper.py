from fastmcp import FastMCP
from fastmcp.server.http import StarletteWithLifespan

def init_mcp_http_app(mcp: FastMCP, transport: str = "http") -> 'StarletteWithLifespan':
    # Create ASGI app from MCP server
    if transport not in ["streamable-http", "sse", "http"]:
        raise ValueError(f"Unsupported MCP_TRANSPORT: {transport}")
    mcp_http_app = mcp.http_app(path='/', transport=transport)
    return mcp_http_app

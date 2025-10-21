import asyncio
import os
import sys

from fastmcp import FastMCP

sys.path.append('.')

async def init_mcp() -> 'FastMCP':
    try:
        from kloudia.mcp.app import mcp as mcp_app
        return mcp_app
    except ImportError:
        print("Kloudia MCP not installed")
        raise

async def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", 8000))
    path = os.getenv("MCP_PATH", None)
    log_level = os.getenv("MCP_LOG_LEVEL", "info")

    available_transports = ["streamable-http", "sse", "http", "stdio"]
    if transport not in available_transports:
        raise ValueError(f"Unsupported transport type: {transport}. Supported types are: {available_transports}")

    kwargs = {}
    if transport != "stdio":
        kwargs.update({
            "host": host,
            "port": port,
            "path": path,
            "log_level": log_level,
        })

    _mcp = None
    try:
        _mcp = await init_mcp()
        await _mcp.run_async(transport=transport, **kwargs)
    except asyncio.CancelledError:
        print("MCP server stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

    # app = asyncio.run(init_starlette_app())
    # uvicorn.run(app, host=host, port=port)

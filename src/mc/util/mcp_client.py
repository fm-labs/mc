import asyncio
import sys
import time

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport


def build_streamable_http_client(url: str, token: str = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    transport = StreamableHttpTransport(
        url=url,
        headers=headers
    )
    return Client(transport)

def build_stdio_client(command: str, args: list = None, env: dict = None):
    transport = StdioTransport(
        command=command,
        args=args,
        env=env
    )
    return Client(transport)

async def list_mcp_tools(client) -> list:
    async with client:
        print("CONNECTED TO MCP SERVER")
        time.sleep(1)
        tools = await client.list_tools()
        print("Available MCP tools:")
        for tool in tools:
            tool_desc_line = tool.description.split("\n")[0]
            print(f"- {tool.name}: {tool_desc_line}")
        return tools


if __name__ == "__main__":
    # take the URL from the command line arguments if provided
    server_url = None
    if len(sys.argv) > 1:
        server_url = sys.argv[1]

    #mcp_transport = build_streamable_http_transport(server_url)
    mcpclient = build_stdio_client(command="uv",
                                   args=["run", "--with", "fastmcp", "--with", "requests", "mcp-server.py"])
    asyncio.run(list_mcp_tools(mcpclient))
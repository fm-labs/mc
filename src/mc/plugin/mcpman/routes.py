from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from mc.inventory.item.mcp_server import build_mcp_client_from_item
from mc.inventory.storage import get_inventory_storage_instance

router = APIRouter()

@router.get("/mcp-servers")
async def list_mcp_servers():
    inventory_storage = get_inventory_storage_instance()
    mcp_servers = inventory_storage.list_items("mcp_server")
    server_data = [jsonable_encoder(server["properties"]) for server in mcp_servers]
    return server_data

@router.get("/mcp-servers/{server_id}/tools")
async def list_mcp_server_tools(server_id: str):
    inventory_storage = get_inventory_storage_instance()
    item = inventory_storage.get_item_by_name("mcp_server", server_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        mcpclient = build_mcp_client_from_item(item)
        async with mcpclient:
            tools = await mcpclient.list_tools()
            tools_data = [jsonable_encoder(tool) for tool in tools]
            return tools_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@router.post("/mcp-servers/{server_id}/tools/{tool_name}/call")
async def call_mcp_server_tool(server_id: str, tool_name: str, tool_args: dict | None = None):
    if tool_args is None:
        tool_args = {}
    inventory_storage = get_inventory_storage_instance()
    item = inventory_storage.get_item_by_name("mcp_server", server_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        mcpclient = build_mcp_client_from_item(item)
        async with mcpclient:
            result = await mcpclient.call_tool(tool_name, tool_args)
            return jsonable_encoder(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to call tool: {str(e)}")
from fastmcp import FastMCP

mcp = FastMCP("Secondary MCP", version="1.0.0")


@mcp.tool
def say_hello() -> str:
    """
    Add a JSON schema for a specific inventory item type.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").
        schema (dict): The JSON schema that defines the structure of the inventory item.
    """
    return "Hello from Secondary MCP!"

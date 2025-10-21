from fastmcp import FastMCP

from kloudia.inventory.metadata import retrieve_inventory_json_schema, store_inventory_json_schema

mcp = FastMCP("Kloudia MCP", version="1.0.0")


@mcp.tool
def add_inventory_json_schema(item_type: str, schema: dict) -> dict:
    """
    Add a JSON schema for a specific inventory item type.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").
        schema (dict): The JSON schema that defines the structure of the inventory item.
    """
    existing = retrieve_inventory_json_schema(item_type)
    if existing:
        raise Exception(f"Item type '{item_type}' already exists")


@mcp.tool
def get_inventory_json_schema(item_type: str) -> dict:
    """
    Retrieve the JSON schema for a specific inventory item type.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").

    Returns:
        dict: The JSON schema if found, otherwise raises an exception.
    """
    schema = retrieve_inventory_json_schema(item_type)
    if not schema:
        raise Exception(f"Item type '{item_type}' does not exist")
    return schema


@mcp.tool
def update_inventory_json_schema(item_type: str, schema: dict) -> dict:
    """
    Update the JSON schema for a specific inventory item type.

    Args:
        item_type (str): The type of inventory item (e.g., "server", "network", "application").
        schema (dict): The updated JSON schema that defines the structure of the inventory item.
    """
    existing = retrieve_inventory_json_schema(item_type)
    if not existing:
        raise Exception(f"Item type '{item_type}' does not exist")

    # todo validate schema changes (e.g., prevent removing required fields)
    store_inventory_json_schema(item_type, schema)
    return {"status": "success", "item_type": item_type}
from typing import List

from fastapi import APIRouter, HTTPException

from mc.inventory.actions import handle_inventory_item_action
from mc.inventory.helper import get_schema_handler, get_meta_handler
from mc.inventory import items
from mc.inventory.metadata import list_inventory_item_types, InventoryMetadata, enumerate_inventories_metadata_from_schema_dir

router = APIRouter()

@router.get("/inventory", response_model=list[InventoryMetadata])
async def get_inventory() -> list[InventoryMetadata]:
    """
    Get a list of all inventory item types that have associated JSON schemas.
    Schema files are located in the resources dir or in the database.
    """
    metadata = enumerate_inventories_metadata_from_schema_dir()
    # sort metadata dict by item_type
    metadata.sort(key=lambda x: x.item_type)
    return metadata


@router.get("/inventory/{item_type}/_schema", response_model=dict)
async def get_inventory_schema(item_type: str) -> dict:
    """
    Get the JSON schema for a specific inventory item type.
    The schema files are located in "mc.inventory" module under "schemas" directory.
    """
    schema = get_schema_handler(item_type)
    if not schema or len(schema) == 0:
        raise HTTPException(404, detail=f"Schema for item type '{item_type}' not found.")
    return schema


@router.get("/inventory/{item_type}/_meta", response_model=dict)
async def get_inventory_metadata(item_type: str) -> dict:
    """
    Get metadata for a specific inventory item type.
    The metadata files are located in "mc.inventory" module under "schemas" directory.
    """
    metadata = get_meta_handler(item_type)
    if not metadata or len(metadata) == 0:
        raise HTTPException(404, detail=f"Metadata for item type '{item_type}' not found.")
    return metadata


@router.get("/inventory/{item_type}", response_model=List[dict])
async def list_inventory_items(item_type: str) -> List[dict]:
    _items = items.list_inventory_items(item_type)
    # sort items by name
    _items.sort(key=lambda x: x.get("name", ""))
    return _items


@router.post("/inventory/{item_type}", response_model=dict)
async def create_inventory_item(item_type: str, item: dict) -> dict:
    return items.create_inventory_item(item_type, item)


@router.get("/inventory/{item_type}/{item_key}", response_model=dict)
async def read_inventory_item(item_type: str, item_key: str) -> dict:
    return items.read_inventory_item(item_type, item_key)


@router.put("/inventory/{item_type}/{item_key}", response_model=dict)
async def update_inventory_item(item_type: str, item_key: str, data: dict) -> dict:
    return items.update_inventory_item(item_type, item_key, data)


@router.delete("/inventory/{item_type}/{item_key}", response_model=bool)
async def delete_inventory_item(item_type: str, item_key: str) -> bool:
    return items.delete_inventory_item(item_type, item_key)


@router.post("/inventory/{item_type}/{item_key}/action/{action_name}", response_model=dict)
async def request_inventory_item_action(item_type: str, item_key: str, action_name: str, action_params: dict) -> dict:
    try:
        return handle_inventory_item_action(item_type, item_key, action_name, action_params)
    except (ValueError, NotImplementedError, Exception) as e:
        print(e)
        # print stack trace
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inventory/{item_type}/{item_key}/view/{view_name}", response_model=dict)
async def request_inventory_item_view(item_type: str, item_key: str, view_name: str, view_params: dict) -> dict:
    try:
        # return handle_inventory_item_view(item_type, item_key, view_name, view_params)
        raise NotImplementedError("Views are not implemented yet.")
    except (ValueError, NotImplementedError, Exception) as e:
        raise HTTPException(status_code=400, detail=str(e))


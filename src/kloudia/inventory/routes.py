import os
import json
import uuid
from typing import List

from fastapi import APIRouter

from kloudia.config import CONFIG_DIR
from kloudia.inventory.actions import handle_inventory_item_action
from kloudia.inventory.storage import get_inventory_storage_instance

router = APIRouter()


@router.get("/{item_type}/_schema", response_model=dict)
async def get_inventory_schema(item_type: str) -> dict:
    """
    Get the JSON schema for a specific inventory item type.
    The schema files are located in "kloudia.inventory" module under "schemas" directory.
    """
    schema_file = os.path.join(CONFIG_DIR, "schemas", "inventory", f"{item_type.lower()}.schema.json")
    if not os.path.exists(schema_file):
        return {"error": f"Schema for item type '{item_type}' not found."}

    try:
        with open(schema_file, "r") as f:
            schema = json.load(f)#
    except json.JSONDecodeError as e:
        return {"error": f"Error parsing schema for item type '{item_type}': {str(e)}"}
    except FileNotFoundError as e:
        return {"error": f"Schema file for item type '{item_type}' not found: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}
    return schema



@router.get("/{item_type}", response_model=List[dict])
async def list_inventory_items(item_type: str) -> List[dict]:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    return storage.list_items(_item_type)

@router.post("/{item_type}", response_model=dict)
async def create_inventory_item(item_type: str, item: dict) -> dict:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    _new_uuid = str(uuid.uuid4())
    item["uuid"] = _new_uuid
    if not storage.save_item(_item_type, item):
        return {"error": "Failed to save item"}
    return storage.get_item(_item_type, _new_uuid)

@router.get("/{item_type}/{uuid}", response_model=dict)
async def read_inventory_item(item_type: str, uuid: str) -> dict:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    return storage.get_item(_item_type, uuid)

@router.put("/{item_type}/{uuid}", response_model=dict)
async def update_inventory_item(item_type: str, uuid: str, data: dict) -> dict:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    item = storage.get_item(_item_type, uuid)
    if not item:
        return {"error": "Item not found"}

    item.update(data)
    print("Updated item:", item)
    if not storage.save_item(_item_type, item):
        return {"error": "Failed to update item"}
    return item

# @router.delete("/{item_type}/{uuid}", response_model=bool)
# async def delete_inventory_item(item_type: str, uuid: str) -> bool:
#     storage = get_inventory_storage_instance()
#     return storage.delete_item(item_type, uuid)

# @router.get("/{item_type}/_/actions", response_model=list)
# async def get_inventory_item_actions(item_type: str, uuid: str, action_name: str) -> dict:
#     try:
#         _item_type = item_type.lower().replace("-", "_")
#         #return list_inventory_item_actions(_item_type, uuid, action_name, {})
#         return {"actions": [
#             {"name": "sample_action", "description": "This is a sample action", "input_schema": {
#                 "type": "object",
#                 "properties": {
#                     "param1": {"type": "string", "description": "Parameter 1"},
#                     "param2": {"type": "integer", "description": "Parameter 2"}
#                 },
#                 "required": ["param1"]
#             }}
#         ]}
#     except (ValueError, NotImplementedError, Exception) as e:
#         return {"error": str(e)}

@router.post("/{item_type}/{uuid}/action/{action_name}", response_model=dict)
async def request_inventory_item_action(item_type: str, uuid: str, action_name: str, action_params: dict) -> dict:
    try:
        _item_type = item_type.lower().replace("-", "_")
        return handle_inventory_item_action(_item_type, uuid, action_name, action_params)
    except (ValueError, NotImplementedError, Exception) as e:
        return {"error": str(e)}

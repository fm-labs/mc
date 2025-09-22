from typing import List

from fastapi import APIRouter

from kloudia.inventory.actions import handle_inventory_item_action
from kloudia.inventory.storage import get_inventory_storage_instance

router = APIRouter()


@router.get("/{item_type}", response_model=List[dict])
async def get_inventory_index(item_type: str) -> List[dict]:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    return storage.list_items(_item_type)


@router.get("/{item_type}/{uuid}", response_model=dict)
async def get_inventory_item(item_type: str, uuid: str) -> dict:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    return storage.get_item(_item_type, uuid)


@router.post("/{item_type}", response_model=bool)
async def save_inventory_item(item_type: str, item: dict) -> bool:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    return storage.save_item(_item_type, item)

# @router.put("/{item_type}", response_model=bool)
# async def put_inventory_item(item_type: str, item: dict) -> bool:
#     storage = get_inventory_storage_instance()
#     return storage.save_item(item_type, item)

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

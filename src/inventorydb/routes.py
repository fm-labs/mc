from typing import List

from fastapi import APIRouter, HTTPException, Depends, Request
from objbase import Storage

from inventorydb.handler import handle_inventory_item_action, handle_inventory_item_view
from inventorydb.metadata import InventoryShortInfo, enumerate_inventories_from_schema_dir, lookup_inventory_schema, \
    lookup_inventory_metadata

router = APIRouter(prefix="/inventory")

def dep_storage(request: Request) -> Storage:
    storage = request.app.state.storage
    return storage


@router.get("/", response_model=list[InventoryShortInfo])
def get_inventory() -> list[InventoryShortInfo]:
    """
    Get a list of all inventory item types that have associated JSON schemas.
    Schema files are located in the resources dir or in the database.
    """
    metadata = enumerate_inventories_from_schema_dir()
    # sort metadata dict by item_type
    metadata.sort(key=lambda x: x.item_type)
    return metadata


@router.get("/{item_type}/_schema", response_model=dict)
def get_inventory_schema(item_type: str) -> dict:
    """
    Get the JSON schema for a specific inventory item type.
    The schema files are located in "mc.inventory" module under "schemas" directory.
    """
    schema = lookup_inventory_schema(item_type)
    if not schema or len(schema) == 0:
        raise HTTPException(404, detail=f"Schema for item type '{item_type}' not found.")
    return schema


@router.get("/{item_type}/_meta", response_model=dict)
def get_inventory_metadata(item_type: str) -> dict:
    """
    Get metadata for a specific inventory item type.
    The metadata files are located in "mc.inventory" module under "schemas" directory.
    """
    metadata = lookup_inventory_metadata(item_type)
    if not metadata or len(metadata) == 0:
        raise HTTPException(404, detail=f"Metadata for item type '{item_type}' not found.")
    return metadata


def _sanitize_item(item: dict) -> dict:
    # remove keys that start with underscore and mask sensitive properties
    props = item.get("properties", {})
    if props and isinstance(props, dict):
        for prop_key, prop_value in props.items():
            if prop_key in ["password", "secret"]:
                props[prop_key] = "*****"
    props = {k: v for k, v in props.items() if not k.startswith("_")}
    item["properties"] = props
    return item


@router.get("/{item_type}", response_model=List[dict])
def list_inventory_items(item_type: str, storage: Storage = Depends(dep_storage)) -> List[dict]:
    _item_type = item_type.lower().replace("-", "_")
    _items = storage.items(_item_type)
    # sort items by name
    _items.sort(key=lambda x: x.get("name", ""))
    _items = [_sanitize_item({"id": item.get("id"), "properties": item}) for item in _items]
    print("Listing items:", _items)
    return _items


@router.post("/{item_type}", response_model=dict)
def create_inventory_item(item_type: str, payload: dict, storage: Storage = Depends(dep_storage)) -> dict:
    item = payload.get("properties", {})
    _item_type = item_type.lower().replace("-", "_")
    _id = item.get("id")
    if not _id:
        raise RuntimeError("Item id is required.")

    #_id = gen_inventory_key(item_type, _id)
    #item["id"] = _id
    if not storage.write(_item_type, item):
        raise HTTPException(status_code=400, detail="Item was not created.")
    return storage.read(_item_type, _id)


@router.get("/{item_type}/{id}", response_model=dict)
def read_inventory_item(item_type: str, id: str, storage: Storage = Depends(dep_storage)) -> dict:
    _item_type = item_type.lower().replace("-", "_")
    item = storage.read(_item_type, id)
    if not item:
        raise HTTPException(404, detail=f"Item '{id}' of type '{item_type}' not found.")

    payload = {"id": id, "properties": item}
    print("Reading item:", payload)
    return _sanitize_item(payload)


@router.put("/{item_type}/{id}", response_model=dict)
def update_inventory_item(item_type: str, id: str, payload: dict, storage: Storage = Depends(dep_storage)) -> dict:
    _item_type = item_type.lower().replace("-", "_")
    item = storage.read(_item_type, id)
    if not item:
        raise HTTPException(404, detail=f"Item '{id}' of type '{item_type}' not found.")

    data = payload.get("properties", {})
    data["id"] = id
    item.update(data)

    # fix: remove item_type from data if exists, since it's not stored in item properties
    if "item_type" in item:
        del item["item_type"]

    print("Updated item:", item)
    if not storage.write(_item_type, item):
        raise HTTPException(status_code=400, detail="Item was not updated.")
    return item


@router.delete("/{item_type}/{id}", response_model=bool)
def delete_inventory_item(item_type: str, id: str, storage: Storage = Depends(dep_storage)) -> bool:
    raise NotImplementedError("Delete inventory item is not implemented yet.")


@router.post("/{item_type}/{id}/action/{action_name}", response_model=dict)
async def request_inventory_item_action(item_type: str, id: str, action_name: str, action_params: dict, storage: Storage = Depends(dep_storage)) -> dict:
    try:
        item_type = item_type.lower().replace("-", "_")
        item = storage.read(item_type, id)
        if not item:
            raise ValueError(f"Item '{id}' of type '{item_type}' not found.")

        return await handle_inventory_item_action(item_type, item, action_name, action_params)
    except (ValueError, NotImplementedError, Exception) as e:
        print(e)
        # print stack trace
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{item_type}/{id}/view/{view_name}", response_model=dict)
async def request_inventory_item_view(item_type: str, id: str, view_name: str, storage: Storage = Depends(dep_storage)) -> dict:
    try:
        item_type = item_type.lower().replace("-", "_")
        item = storage.read(item_type, id)
        if not item:
            raise ValueError(f"Item '{id}' of type '{item_type}' not found.")

        return await handle_inventory_item_view(item_type, item, view_name, {})
    except (ValueError, NotImplementedError, Exception) as e:
        print(e)
        # print stack trace
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


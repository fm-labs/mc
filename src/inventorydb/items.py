from typing import List

# from inventorydb.storage import InventoryStorage
from objbase import Storage as InventoryStorage


# def get_inventory_schema(item_type: str) -> dict:
#     """
#     Get the JSON schema for a specific inventory item type.
#     The schema files are located in "mc.inventory" module under "schemas" directory.
#     """
#     schema = lookup_inventory_schema(item_type)
#     if not schema or len(schema) == 0:
#         raise RuntimeError(f"Schema for item type '{item_type}' not found.")
#     return schema
#
#
# def get_inventory_metadata(item_type: str) -> dict:
#     """
#     Get metadata for a specific inventory item type.
#     The metadata files are located in "mc.inventory" module under "schemas" directory.
#     """
#     metadata = lookup_inventory_metadata(item_type)
#     if not metadata or len(metadata) == 0:
#         raise RuntimeError(f"Metadata for item type '{item_type}' not found.")
#     return metadata


def list_inventory_items(storage: InventoryStorage, item_type: str) -> List[dict]:
    _item_type = item_type.lower().replace("-", "_")
    return storage.items(_item_type)


def create_inventory_item(storage: InventoryStorage, item_type: str, item: dict) -> dict:
    _item_type = item_type.lower().replace("-", "_")
    # todo check if item_type is valid
    _id = item.get("id")
    if not _id:
        raise RuntimeError("Item id is required.")

    #_id = gen_inventory_key(item_type, _id)
    #item["id"] = _id
    if not storage.write(_item_type, item):
        return {"error": "Failed to save item"}
    return storage.read(_item_type, _id)


def read_inventory_item(storage: InventoryStorage, item_type: str, id: str) -> dict:
    _item_type = item_type.lower().replace("-", "_")
    return storage.read(_item_type, id)


def update_inventory_item(storage: InventoryStorage, item_type: str, id: str, data: dict) -> dict:
    _item_type = item_type.lower().replace("-", "_")
    item = storage.read(_item_type, id)
    if not item:
        return {"error": "Item not found"}

    data["id"] = id
    # fix: remove item_type from data if exists, since it's not stored in item properties
    if "item_type" in item:
        del item["item_type"]
    item.update(data)
    print("Updated item:", item)
    if not storage.write(_item_type, item):
        return {"error": "Failed to update item"}
    return item


def delete_inventory_item(storage: InventoryStorage, item_type: str, id: str) -> bool:
    #return storage.delete_item(item_type, id)
    raise NotImplementedError("Delete inventory item is not implemented yet.")


# def request_inventory_item_action(item_type: str, id: str, action_name: str, action_params: dict) -> dict:
#     try:
#         return handle_inventory_item_action(item_type, id, action_name, action_params)
#     except (ValueError, NotImplementedError, Exception) as e:
#         raise RuntimeError(str(e))

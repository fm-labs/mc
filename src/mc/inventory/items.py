from typing import List


from mc.inventory.helper import gen_inventory_key, get_schema_handler, get_meta_handler
from mc.inventory.storage import get_inventory_storage_instance



def get_inventory_schema(item_type: str) -> dict:
    """
    Get the JSON schema for a specific inventory item type.
    The schema files are located in "mc.inventory" module under "schemas" directory.
    """
    schema = get_schema_handler(item_type)
    if not schema or len(schema) == 0:
        raise RuntimeError(f"Schema for item type '{item_type}' not found.")
    return schema


def get_inventory_metadata(item_type: str) -> dict:
    """
    Get metadata for a specific inventory item type.
    The metadata files are located in "mc.inventory" module under "schemas" directory.
    """
    metadata = get_meta_handler(item_type)
    if not metadata or len(metadata) == 0:
        raise RuntimeError(f"Metadata for item type '{item_type}' not found.")
    return metadata


def list_inventory_items(item_type: str) -> List[dict]:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    return storage.list_items(_item_type)


def create_inventory_item(item_type: str, item: dict) -> dict:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    # todo check if item_type is valid
    _item_name = item.get("name")
    if not _item_name:
        raise RuntimeError("Item name is required.")

    _item_key = gen_inventory_key(item_type, _item_name)
    item["item_key"] = _item_key
    if not storage.save_item(_item_type, item):
        return {"error": "Failed to save item"}
    return storage.get_item(_item_type, _item_key)


def read_inventory_item(item_type: str, item_key: str) -> dict:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    return storage.get_item(_item_type, item_key)


def update_inventory_item(item_type: str, item_key: str, data: dict) -> dict:
    storage = get_inventory_storage_instance()
    _item_type = item_type.lower().replace("-", "_")
    item = storage.get_item(_item_type, item_key)
    if not item:
        return {"error": "Item not found"}

    if "item_key" in data:
        del data["item_key"]
    if "item_type" in data:
        del data["item_type"]
    if item["name"] != data.get("name", item["name"]):
        #_item_key = gen_inventory_key(item_type, item.get("name"))
        #data["item_key"] = _item_key
        return {"error": "Cannot change item name"}
    item.update(data)
    print("Updated item:", item)
    if not storage.save_item(_item_type, item):
        return {"error": "Failed to update item"}
    return item


def delete_inventory_item(item_type: str, item_key: str) -> bool:
    storage = get_inventory_storage_instance()
    #return storage.delete_item(item_type, item_key)
    raise NotImplementedError("Delete inventory item is not implemented yet.")


# def request_inventory_item_action(item_type: str, item_key: str, action_name: str, action_params: dict) -> dict:
#     try:
#         return handle_inventory_item_action(item_type, item_key, action_name, action_params)
#     except (ValueError, NotImplementedError, Exception) as e:
#         raise RuntimeError(str(e))

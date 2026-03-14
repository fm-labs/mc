import abc
import json
import os
from typing import List, Optional

from mc.config import DATA_DIR
from mc.db.mongodb import get_mongo_client, get_mongo_collection

DEFAULT_INVENTORY_STORAGE = "directory"  # Options: file, mongodb, redis

# global variable to hold the storage instance
_inventory_storage_instance = None

def get_inventory_storage_instance() -> 'InventoryStorage':

    global _inventory_storage_instance
    if _inventory_storage_instance is not None:
        return _inventory_storage_instance

    storage_type: str = os.environ.get("INVENTORY_STORAGE", DEFAULT_INVENTORY_STORAGE)
    if storage_type == "file":
        base_dir = f"{DATA_DIR}/inventory"
        os.makedirs(base_dir, exist_ok=True)
        _inventory_storage_instance = FileBasedInventoryStorage(base_dir)
    elif storage_type == "directory":
        base_dir = f"{DATA_DIR}/inventory"
        os.makedirs(base_dir, exist_ok=True)
        _inventory_storage_instance = DirectoryBasedInventoryStorage(base_dir)
    elif storage_type == "mongodb":
        mongo_client = get_mongo_client()
        _inventory_storage_instance = MongoDBInventoryStorage(mongo_client)
    # elif storage_type == "redis":
    #     redis_client = get_redis_client()
    #     _inventory_storage_instance = RedisInventoryStorage(redis_client)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")

    return _inventory_storage_instance



class InventoryStorage(abc.ABC):

    @abc.abstractmethod
    def list_items(self, inventory_type: str) -> List[dict]:
        pass

    @abc.abstractmethod
    def save_item(self, inventory_type: str, item: dict) -> bool:
        pass

    @abc.abstractmethod
    def get_item(self, inventory_type: str, id: str) -> dict:
        pass

    @abc.abstractmethod
    def delete_item(self, inventory_type: str, id: str) -> bool:
        pass

    def get_item_by_name(self, inventory_type: str, name: str) -> dict:
        items = self.list_items(inventory_type)
        for item in items:
            if item.get("name") == name:
                return item
        return {}


class FileBasedInventoryStorage(InventoryStorage):
    """Simple file-based storage that saves all items of a given inventory type in a single JSON file."""

    def __init__(self, base_dir: str):
        self.inventory_dir = base_dir
        if not os.path.exists(self.inventory_dir):
            raise ValueError(f"Base directory {self.inventory_dir} does not exist.")

    def list_items(self, inventory_type: str) -> List[dict]:
        return self._read_file(inventory_type)

    def save_item(self, inventory_type: str, item: dict) -> bool:
        items = self.list_items(inventory_type)
        for i, existing_item in enumerate(items):
            if existing_item["id"] == item["id"]:
                items[i] = item
                break
        else:
            items.append(item)
        self._write_file(inventory_type, items)
        return True

    def get_item(self, inventory_type: str, id: str) -> dict:
        items = self.list_items(inventory_type)
        for item in items:
            if item["id"] == id:
                return item
        return {}

    def delete_item(self, inventory_type: str, id: str) -> bool:
        items = self.list_items(inventory_type)
        items = [item for item in items if item["id"] != id]
        self._write_file(inventory_type, items)
        return True

    def _read_file(self, file_name: str) -> dict | list:
        file_path = f"{self.inventory_dir}/{file_name}.json"
        with open(file_path, 'r') as f:
            return json.load(f)

    def _write_file(self, file_name: str, data: dict | list) -> None:
        file_path = f"{self.inventory_dir}/{file_name}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)


class DirectoryBasedInventoryStorage(InventoryStorage):
    """Alternative file-based storage that uses a directory per inventory type and individual files per item."""

    def __init__(self, base_dir: str):
        self.inventory_dir = base_dir
        if not os.path.exists(self.inventory_dir):
            raise ValueError(f"Base directory {self.inventory_dir} does not exist.")

    def list_items(self, inventory_type: str) -> List[dict]:
        type_dir = f"{self.inventory_dir}/{inventory_type}"
        if not os.path.exists(type_dir):
            return []
        items = []
        for filename in os.listdir(type_dir):
            if filename.endswith(".json"):
                with open(f"{type_dir}/{filename}", 'r') as f:
                    items.append(json.load(f))
        return items

    def save_item(self, inventory_type: str, item: dict) -> bool:
        type_dir = f"{self.inventory_dir}/{inventory_type}"
        os.makedirs(type_dir, exist_ok=True)
        item_id = item.get("id")
        if not item_id:
            raise ValueError("Item must have an 'id' field.")
        with open(f"{type_dir}/{item_id}.json", 'w') as f:
            json.dump(item, f, indent=4)
        return True

    def get_item(self, inventory_type: str, id: str) -> dict:
        type_dir = f"{self.inventory_dir}/{inventory_type}"
        item_path = f"{type_dir}/{id}.json"
        if not os.path.exists(item_path):
            return {}
        with open(item_path, 'r') as f:
            return json.load(f)

    def delete_item(self, inventory_type: str, id: str) -> bool:
        type_dir = f"{self.inventory_dir}/{inventory_type}"
        item_path = f"{type_dir}/{id}.json"
        if os.path.exists(item_path):
            os.remove(item_path)
            return True
        return False



class MongoDBInventoryStorage(InventoryStorage):
    """MongoDB-based storage implementation for inventory items."""

    def __init__(self, mongo_client):
        self.mongo_client = mongo_client

    def list_items(self, inventory_type: str, query: Optional[dict] = None) -> List[dict]:
        if query is None:
            query = {}
        collection = get_mongo_collection('inventory', inventory_type)
        records = list(collection.find(query))
        filtered_records = []
        for record in records:
            record.pop('_id', None)
            filtered_records.append(record)
        return filtered_records

    def save_item(self, inventory_type: str, item: dict) -> bool:
        collection = get_mongo_collection('inventory', inventory_type)
        collection.update_one({'id': item['id']}, {'$set': item}, upsert=True)
        return True

    def get_item(self, inventory_type: str, id: str) -> dict:
        db = self.mongo_client['inventory']
        collection = db[inventory_type]
        item = collection.find_one({'id': id})
        print("Fetched item from MongoDB:", item)
        if item:
            item.pop('_id', None)
        return item if item else None

    def delete_item(self, inventory_type: str, id: str) -> bool:
        collection = get_mongo_collection('inventory', inventory_type)
        result = collection.delete_one({'id': id})
        return result.deleted_count > 0


# class RedisInventoryStorage(InventoryStorage):
#
#     def __init__(self, redis_client):
#         self.redis_client = redis_client
#
#     def list_items(self, inventory_type: str) -> List[dict]:
#         keys = self.redis_client.keys(f"{inventory_type}:*")
#         items = []
#         for key in keys:
#             item = self.redis_client.hgetall(key)
#             items.append({k.decode('utf-8'): v.decode('utf-8') for k, v in item.items()})
#         return items
#
#     def save_item(self, inventory_type: str, item: dict) -> bool:
#         key = f"{inventory_type}:{item['id']}"
#         self.redis_client.hmset(key, item)
#         return True
#
#     def get_item(self, inventory_type: str, id: str) -> dict:
#         key = f"{inventory_type}:{id}"
#         item = self.redis_client.hgetall(key)
#         return {k.decode('utf-8'): v.decode('utf-8') for k, v in item.items()} if item else {}
#
#     def delete_item(self, inventory_type: str, id: str) -> bool:
#         key = f"{inventory_type}:{id}"
#         result = self.redis_client.delete(key)
#         return result > 0
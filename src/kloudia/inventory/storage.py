import abc
import os
from typing import List

from kloudia.config import load_config_json, save_config_json
from kloudia.db.mongodb import get_mongo_client, get_mongo_collection
from kloudia.db.redis import get_redis_client

DEFAULT_INVENTORY_STORAGE = "mongodb"  # Options: file, mongodb, redis

# global variable to hold the storage instance
_inventory_storage_instance = None

def get_inventory_storage_instance() -> 'InventoryStorage':

    global _inventory_storage_instance
    if _inventory_storage_instance is not None:
        return _inventory_storage_instance

    storage_type: str = os.environ.get("INVENTORY_STORAGE", DEFAULT_INVENTORY_STORAGE)
    if storage_type == "file":
        _inventory_storage_instance = FileBasedInventoryStorage()
    elif storage_type == "mongodb":
        mongo_client = get_mongo_client()
        _inventory_storage_instance = MongoDBInventoryStorage(mongo_client)
    elif storage_type == "redis":
        redis_client = get_redis_client()
        _inventory_storage_instance = RedisInventoryStorage(redis_client)
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
    def get_item(self, inventory_type: str, uuid: str) -> dict:
        pass


class FileBasedInventoryStorage(InventoryStorage):

    def list_items(self, inventory_type: str) -> List[dict]:
        return load_config_json(inventory_type)

    def save_item(self, inventory_type: str, item: dict) -> bool:
        items = self.list_items(inventory_type)
        for i, existing_item in enumerate(items):
            if existing_item["item_key"] == item["item_key"]:
                items[i] = item
                break
        else:
            items.append(item)
        save_config_json(inventory_type, items)
        return True

    def get_item(self, inventory_type: str, uuid: str) -> dict:
        items = self.list_items(inventory_type)
        for item in items:
            if item["item_key"] == uuid:
                return item
        return {}


class MongoDBInventoryStorage(InventoryStorage):

    def __init__(self, mongo_client):
        self.mongo_client = mongo_client

    def list_items(self, inventory_type: str) -> List[dict]:
        collection = get_mongo_collection('inventory', inventory_type)
        records = list(collection.find({}))
        filtered_records = []
        for record in records:
            record.pop('_id', None)
            filtered_records.append(record)
        return filtered_records

    def save_item(self, inventory_type: str, item: dict) -> bool:
        collection = get_mongo_collection('inventory', inventory_type)
        collection.update_one({'item_key': item['item_key']}, {'$set': item}, upsert=True)
        return True

    def get_item(self, inventory_type: str, uuid: str) -> dict:
        db = self.mongo_client['inventory']
        collection = db[inventory_type]
        item = collection.find_one({'item_key': uuid})
        print("Fetched item from MongoDB:", item)
        if item:
            item.pop('_id', None)
        return item if item else {}


class RedisInventoryStorage(InventoryStorage):

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def list_items(self, inventory_type: str) -> List[dict]:
        keys = self.redis_client.keys(f"{inventory_type}:*")
        items = []
        for key in keys:
            item = self.redis_client.hgetall(key)
            items.append({k.decode('utf-8'): v.decode('utf-8') for k, v in item.items()})
        return items

    def save_item(self, inventory_type: str, item: dict) -> bool:
        key = f"{inventory_type}:{item['item_key']}"
        self.redis_client.hmset(key, item)
        return True

    def get_item(self, inventory_type: str, uuid: str) -> dict:
        key = f"{inventory_type}:{uuid}"
        item = self.redis_client.hgetall(key)
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in item.items()} if item else {}
import logging
from typing import Any

from objbase import Storage as InventoryStorage
from objbase.errors import ItemNotFoundError
from objbase.interface import Item

logger = logging.getLogger(__name__)

# Placeholder returned to clients in place of sensitive values
MASK = "*****"

# Keys (case-insensitive substring match) whose values are never returned to clients
SENSITIVE_KEY_PARTS = ("password", "secret", "token", "passphrase", "private_key", "api_key")

# Keys managed by the server, which clients can't set
RESERVED_KEYS = ("item_type",)


class ItemExistsError(ValueError):
    def __init__(self, item_type: str, id: str):
        self.item_type = item_type
        self.id = id
        super().__init__(f"Item '{id}' of type '{item_type}' already exists.")


def storage_key(item_type: str) -> str:
    """Normalize an item type (e.g. 'app-stack') to its storage collection name (e.g. 'app_stack')."""
    return item_type.lower().replace("-", "_")


def _is_sensitive(key: str) -> bool:
    key = key.lower()
    return any(part in key for part in SENSITIVE_KEY_PARTS)


def _mask(value: Any) -> Any:
    """Recursively mask sensitive values and drop private (underscore-prefixed) keys."""
    if isinstance(value, dict):
        return {
            k: (MASK if _is_sensitive(k) and v not in (None, "") else _mask(v))
            for k, v in value.items()
            if not k.startswith("_")
        }
    if isinstance(value, list):
        return [_mask(v) for v in value]
    return value


def _unmask(incoming: Any, stored: Any) -> Any:
    """
    Recursively replace masked placeholders in client data with the stored values,
    so that a client round-tripping a masked item doesn't overwrite its secrets.
    """
    if isinstance(incoming, dict):
        stored = stored if isinstance(stored, dict) else {}
        result = {}
        for k, v in incoming.items():
            if v == MASK and k in stored:
                result[k] = stored[k]
            else:
                result[k] = _unmask(v, stored.get(k))
        return result
    return incoming


def _clean_input(data: dict[str, Any]) -> Item:
    """Remove keys clients aren't allowed to write."""
    return {k: v for k, v in data.items() if not k.startswith("_") and k not in RESERVED_KEYS}


def to_response(item: Item) -> dict[str, Any]:
    """Wrap a stored item in the API representation, with sensitive values masked."""
    return {"id": item.get("id"), "properties": _mask(item)}


def list_inventory_items(storage: InventoryStorage, item_type: str) -> list[Item]:
    items = storage.items(storage_key(item_type))
    items.sort(key=lambda x: str(x.get("name") or x.get("label") or x.get("id") or ""))
    return items


def create_inventory_item(storage: InventoryStorage, item_type: str, data: dict[str, Any]) -> Item:
    _item_type = storage_key(item_type)
    item = _clean_input(data)
    _id = item.get("id")
    if not _id or not isinstance(_id, str):
        raise ValueError("Item id is required.")
    if storage.read(_item_type, _id):
        raise ItemExistsError(item_type, _id)

    if not storage.write(_item_type, item):
        raise RuntimeError(f"Item '{_id}' of type '{item_type}' could not be saved.")
    logger.info("Created inventory item %s/%s", _item_type, _id)
    return read_inventory_item(storage, item_type, _id)


def read_inventory_item(storage: InventoryStorage, item_type: str, id: str) -> Item:
    item = storage.read(storage_key(item_type), id)
    if not item:
        raise ItemNotFoundError(item_type, id)
    return item


def update_inventory_item(storage: InventoryStorage, item_type: str, id: str, data: dict[str, Any]) -> Item:
    """Merge client data into the stored item. Masked values and private keys are preserved."""
    _item_type = storage_key(item_type)
    item = read_inventory_item(storage, item_type, id)

    item.update(_unmask(_clean_input(data), item))
    item["id"] = id
    for key in RESERVED_KEYS:
        item.pop(key, None)

    if not storage.write(_item_type, item):
        raise RuntimeError(f"Item '{id}' of type '{item_type}' could not be saved.")
    logger.info("Updated inventory item %s/%s", _item_type, id)
    return item


def delete_inventory_item(storage: InventoryStorage, item_type: str, id: str) -> bool:
    _item_type = storage_key(item_type)
    if not storage.delete(_item_type, id):
        raise ItemNotFoundError(item_type, id)
    logger.info("Deleted inventory item %s/%s", _item_type, id)
    return True

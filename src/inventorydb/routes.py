import logging
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from objbase import Storage
from objbase.errors import ItemNotFoundError

from inventorydb import items
from inventorydb.handler import invoke_item_handler
from inventorydb.metadata import InventoryShortInfo
from inventorydb.registry import HandlerKind, InventoryItemType, InventoryRegistry, get_inventory_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory")


def dep_storage(request: Request) -> Storage:
    storage: Storage = request.app.state.storage
    return storage


RegistryDep = Annotated[InventoryRegistry, Depends(get_inventory_registry)]


def _lookup_item_type(registry: InventoryRegistry, item_type: str) -> InventoryItemType:
    found = registry.get(item_type)
    if found is None:
        raise HTTPException(404, detail=f"Unknown item type '{item_type}'.")
    return found


def dep_item_type(item_type: str, registry: RegistryDep) -> str:
    """Only allow registered item types."""
    _lookup_item_type(registry, item_type)
    return item_type


StorageDep = Annotated[Storage, Depends(dep_storage)]
ItemTypeDep = Annotated[str, Depends(dep_item_type)]


def _storage_call[T](fn: Callable[..., T], *args: Any) -> T:
    """Run an inventory operation and map its errors to HTTP errors."""
    try:
        return fn(*args)
    except ItemNotFoundError as e:
        raise HTTPException(404, detail=str(e)) from e
    except items.ItemExistsError as e:
        raise HTTPException(409, detail=str(e)) from e
    except ValueError as e:
        # objbase raises ValueError for invalid ids
        raise HTTPException(400, detail=str(e)) from e


def _properties(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("properties") or {}
    if not isinstance(data, dict):
        raise HTTPException(400, detail="'properties' must be an object.")
    return data


@router.get("/", response_model=list[InventoryShortInfo])
def get_inventory(registry: RegistryDep) -> list[InventoryShortInfo]:
    """Get a list of all inventory item types, sorted by name."""
    return [item_type.info() for item_type in registry.types()]


@router.get("/{item_type}/_schema", response_model=dict)
def get_inventory_schema(item_type: str, registry: RegistryDep) -> dict[str, Any]:
    """Get the JSON schema of an inventory item type."""
    return _lookup_item_type(registry, item_type).schema


@router.get("/{item_type}/_meta", response_model=dict)
def get_inventory_metadata(item_type: str, registry: RegistryDep) -> dict[str, Any]:
    """Get the UI metadata (meta.json) of an inventory item type."""
    metadata = _lookup_item_type(registry, item_type).meta
    if not metadata:
        raise HTTPException(404, detail=f"Metadata for item type '{item_type}' not found.")
    return metadata


@router.get("/{item_type}", response_model=list[dict[str, Any]])
def list_inventory_items(item_type: ItemTypeDep, storage: StorageDep) -> list[dict[str, Any]]:
    _items = _storage_call(items.list_inventory_items, storage, item_type)
    return [items.to_response(item) for item in _items]


@router.post("/{item_type}", response_model=dict, status_code=201)
def create_inventory_item(payload: dict[str, Any], item_type: ItemTypeDep, storage: StorageDep) -> dict[str, Any]:
    data = _properties(payload)
    if not data.get("id") and payload.get("id"):
        data["id"] = payload["id"]
    item = _storage_call(items.create_inventory_item, storage, item_type, data)
    return items.to_response(item)


@router.get("/{item_type}/{id}", response_model=dict)
def read_inventory_item(id: str, item_type: ItemTypeDep, storage: StorageDep) -> dict[str, Any]:
    item = _storage_call(items.read_inventory_item, storage, item_type, id)
    return items.to_response(item)


@router.put("/{item_type}/{id}", response_model=dict)
def update_inventory_item(
    id: str, payload: dict[str, Any], item_type: ItemTypeDep, storage: StorageDep
) -> dict[str, Any]:
    item = _storage_call(items.update_inventory_item, storage, item_type, id, _properties(payload))
    return items.to_response(item)


@router.delete("/{item_type}/{id}", response_model=bool)
def delete_inventory_item(id: str, item_type: ItemTypeDep, storage: StorageDep) -> bool:
    return _storage_call(items.delete_inventory_item, storage, item_type, id)


async def _run_item_handler(
    registry: InventoryRegistry,
    kind: HandlerKind,
    item_type: str,
    id: str,
    name: str,
    params: dict[str, Any],
    storage: Storage,
) -> dict[str, Any]:
    """Load the item and run an action/view handler on it, mapping errors to HTTP errors."""
    item = _storage_call(items.read_inventory_item, storage, item_type, id)
    try:
        method = registry.get_handler(item_type, kind, name)
        return await invoke_item_handler(method, item, params)
    except NotImplementedError as e:
        raise HTTPException(404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Handler '%s' failed for %s/%s", name, item_type, id)
        raise HTTPException(500, detail=f"'{name}' failed: {e}") from e


@router.post("/{item_type}/{id}/action/{action_name}", response_model=dict)
async def request_inventory_item_action(
    id: str,
    action_name: str,
    item_type: ItemTypeDep,
    storage: StorageDep,
    registry: RegistryDep,
    action_params: Annotated[dict[str, Any] | None, Body()] = None,
) -> dict[str, Any]:
    return await _run_item_handler(registry, "actions", item_type, id, action_name, action_params or {}, storage)


@router.get("/{item_type}/{id}/view/{view_name}", response_model=dict)
async def request_inventory_item_view(
    id: str, view_name: str, item_type: ItemTypeDep, storage: StorageDep, registry: RegistryDep
) -> dict[str, Any]:
    return await _run_item_handler(registry, "views", item_type, id, view_name, {}, storage)

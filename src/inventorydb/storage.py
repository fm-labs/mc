import os
import threading

from objbase import Storage

from inventorydb.settings import InventorySettings, get_inventory_settings

STORAGE_TYPES = ("directory", "file", "sqlite")

# the shared storage instance, and the settings it was built with
_inventory_storage_instance: Storage | None = None
_inventory_storage_settings: InventorySettings | None = None
_inventory_storage_lock = threading.Lock()


def build_objbase_storage(settings: InventorySettings | None = None) -> Storage:
    """Build the storage configured in the settings (default: the current inventory settings)."""
    settings = settings or get_inventory_settings()
    base_dir = settings.storage_dir
    storage: Storage
    if settings.storage_type == "file":
        from objbase import LocalFileStorage

        os.makedirs(base_dir, exist_ok=True)
        storage = LocalFileStorage(base_dir=base_dir)
    elif settings.storage_type == "directory":
        from objbase import LocalDirectoryStorage

        os.makedirs(base_dir, exist_ok=True)
        storage = LocalDirectoryStorage(base_dir=base_dir)
    elif settings.storage_type == "sqlite":
        from objbase import SQLiteStorage

        os.makedirs(base_dir, exist_ok=True)
        storage = SQLiteStorage(db_path=os.path.join(base_dir, "inventory.db"))
    # todo add support for redis and mongodb storages
    else:
        raise ValueError(f"Unknown storage type '{settings.storage_type}', expected one of {', '.join(STORAGE_TYPES)}")
    return storage


def get_inventory_storage_instance() -> Storage:
    """The shared storage, built from the current inventory settings on first use (and when they change)."""
    global _inventory_storage_instance, _inventory_storage_settings
    settings = get_inventory_settings()
    with _inventory_storage_lock:
        if _inventory_storage_instance is None or _inventory_storage_settings is not settings:
            _inventory_storage_instance = build_objbase_storage(settings)
            _inventory_storage_settings = settings
        return _inventory_storage_instance

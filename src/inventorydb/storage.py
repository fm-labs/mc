import os

from objbase import Storage

from mc.config import DATA_DIR

DEFAULT_INVENTORY_STORAGE = "directory"  # Options: file, directory, sqlite

# global variable to hold the storage instance
_inventory_storage_instance: Storage | None = None


def build_objbase_storage() -> Storage:
    storage_type: str = os.environ.get("INVENTORY_STORAGE", DEFAULT_INVENTORY_STORAGE)
    base_dir = f"{DATA_DIR}/inventory"
    os.makedirs(base_dir, exist_ok=True)
    storage: Storage
    if storage_type == "file":
        from objbase import LocalFileStorage

        storage = LocalFileStorage(base_dir=base_dir)
    elif storage_type == "directory":
        from objbase import LocalDirectoryStorage

        storage = LocalDirectoryStorage(base_dir=base_dir)
    elif storage_type == "sqlite":
        from objbase import SQLiteStorage

        storage = SQLiteStorage(db_path=f"{base_dir}/inventory.db")
    # todo add support for redis and mongodb storages
    else:
        raise Exception(f"Unknown storage type: {storage_type}")
    return storage


def get_inventory_storage_instance() -> Storage:
    global _inventory_storage_instance
    if _inventory_storage_instance is None:
        _inventory_storage_instance = build_objbase_storage()
    return _inventory_storage_instance

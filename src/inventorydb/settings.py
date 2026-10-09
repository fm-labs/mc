"""
Settings of inventorydb.

The defaults make inventorydb usable on its own: items are stored in `./inventory`, and item types come only from
installed packages that register under the `inventorydb.item_types` entry point group. Applications set their
own settings once at startup:

    from inventorydb.settings import InventorySettings, configure_inventory

    configure_inventory(InventorySettings(storage_dir="/var/lib/myapp/inventory", item_packages=("myapp.items",)))
"""

import threading
from dataclasses import dataclass

DEFAULT_ENTRY_POINT_GROUP = "inventorydb.item_types"
DEFAULT_PLUGIN_SUBPACKAGE = "inventory"
DEFAULT_USER_MODULE_PACKAGE = "inventorydb_user_types"


@dataclass(frozen=True)
class InventorySettings:
    # storage backend: "directory" (one JSON file per item), "file" (one JSON file per type) or "sqlite"
    storage_type: str = "directory"
    storage_dir: str = "inventory"

    # item type sources, in order of precedence

    # packages whose subpackages are item types, e.g. "myapp.items" -> myapp.items.<type>/
    item_packages: tuple[str, ...] = ()
    # plugin packages: each plugin `<package>.<plugin>` may provide item types in `<plugin>.<plugin_subpackage>`
    plugin_packages: tuple[str, ...] = ()
    plugin_subpackage: str = DEFAULT_PLUGIN_SUBPACKAGE
    # entry point group of installed packages that provide item types (None: don't use entry points)
    entry_point_group: str | None = DEFAULT_ENTRY_POINT_GROUP
    # directory with user item types, one folder per type (None: no user types)
    user_dir: str | None = None
    # load the Python modules of user item types (schema-only user types always load)
    user_code: bool = False
    # package name user item modules are loaded under
    user_module_package: str = DEFAULT_USER_MODULE_PACKAGE

    # TOML file with item type overrides (None: no overrides)
    overrides_file: str | None = None


_settings = InventorySettings()
_settings_lock = threading.Lock()


def configure_inventory(settings: InventorySettings) -> None:
    """
    Set the inventory settings. The shared registry and storage are rebuilt with the new settings on next use.
    Call this at startup, before the inventory is used.
    """
    global _settings
    with _settings_lock:
        _settings = settings


def get_inventory_settings() -> InventorySettings:
    return _settings

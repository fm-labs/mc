"""
mc's use of inventorydb: item types from mc's own packages and plugins, storage and user types in the data dir.

Every process that uses the inventory calls setup_inventory() once at startup.
"""

import os

from inventorydb.settings import InventorySettings, configure_inventory
from mc import config

# core item types: mc.inventory.item.<type>
ITEM_PACKAGE = "mc.inventory.item"
# plugins provide item types in mc.plugin.<plugin>.inventory.<type>
PLUGIN_PACKAGE = "mc.plugin"
# installed packages provide item types with: [project.entry-points."mc.inventory_types"] name = "package"
ENTRY_POINT_GROUP = "mc.inventory_types"
# user item modules are loaded as mc_user_inventory.<type>
USER_MODULE_PACKAGE = "mc_user_inventory"


def inventory_settings() -> InventorySettings:
    return InventorySettings(
        storage_type=config.INVENTORY_STORAGE,
        storage_dir=os.path.join(config.DATA_DIR, "inventory"),
        item_packages=(ITEM_PACKAGE,),
        plugin_packages=(PLUGIN_PACKAGE,),
        entry_point_group=ENTRY_POINT_GROUP,
        user_dir=os.path.join(config.CONFIG_DIR, "inventory"),
        user_code=config.INVENTORY_USER_CODE,
        user_module_package=USER_MODULE_PACKAGE,
        overrides_file=os.path.join(config.CONFIG_DIR, "inventory.toml"),
    )


def setup_inventory() -> None:
    """Configure inventorydb for mc."""
    configure_inventory(inventory_settings())

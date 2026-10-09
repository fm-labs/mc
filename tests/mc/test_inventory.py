"""mc's configuration of inventorydb, and the item types that ship with mc."""

from pathlib import Path

import pytest

from inventorydb.registry import InventoryRegistry, build_inventory_registry, get_inventory_registry
from inventorydb.settings import InventorySettings, get_inventory_settings
from inventorydb.storage import get_inventory_storage_instance
from mc import config
from mc.inventory import inventory_settings


def test_settings():
    assert inventory_settings() == InventorySettings(
        storage_type="directory",
        storage_dir=f"{config.DATA_DIR}/inventory",
        item_packages=("mc.inventory.item",),
        plugin_packages=("mc.plugin",),
        plugin_subpackage="inventory",
        entry_point_group="mc.inventory_types",
        user_dir=f"{config.CONFIG_DIR}/inventory",
        user_code=False,
        user_module_package="mc_user_inventory",
        overrides_file=f"{config.CONFIG_DIR}/inventory.toml",
    )


def test_settings_follow_config(monkeypatch):
    monkeypatch.setattr(config, "INVENTORY_STORAGE", "sqlite")
    monkeypatch.setattr(config, "INVENTORY_USER_CODE", True)
    settings = inventory_settings()
    assert settings.storage_type == "sqlite"
    assert settings.user_code is True


def test_tests_run_with_mc_settings():
    # conftest calls setup_inventory(), like the server and CLI do
    assert get_inventory_settings() == inventory_settings()


def test_shared_storage_is_in_data_dir():
    storage = get_inventory_storage_instance()
    storage.write("variable", {"id": "v1"})
    try:
        assert (Path(config.DATA_DIR) / "inventory" / "variable" / "v1.json").exists()
    finally:
        storage.delete("variable", "v1")


def test_shared_registry_has_mc_types():
    assert "app-stack" in get_inventory_registry()


class TestShippedTypes:
    """The item types that ship with mc: core types and the types of the built-in plugins."""

    @pytest.fixture
    def reg(self) -> InventoryRegistry:
        return build_inventory_registry(inventory_settings())

    def test_types(self, reg):
        assert [t.name for t in reg.types()] == [
            "app-stack",
            "app-template",
            "configuration",
            "container-node",
            "container-registry",
            "secret",
            "ssh-key",
            "variable",
        ]

    def test_load_without_warnings(self, reg):
        assert reg.warnings == []

    @pytest.mark.parametrize(
        "name, source",
        [
            ("configuration", "mc.inventory.item.configuration"),
            ("ssh-key", "mc.inventory.item.ssh_key"),
            ("app-stack", "mc.plugin.apps.inventory.app_stack"),
            ("app-template", "mc.plugin.apps.inventory.app_template"),
            ("container-node", "mc.plugin.containers.inventory.container_node"),
            ("container-registry", "mc.plugin.containers.inventory.container_registry"),
        ],
    )
    def test_sources(self, reg, name, source):
        item_type = reg.get(name)
        assert item_type is not None
        assert item_type.source == source

    def test_handlers(self, reg):
        from mc.inventory.item import ssh_key

        item_type = reg.get("ssh-key")
        assert item_type is not None
        assert item_type.get_handler("actions", "set_content") is ssh_key.actions["set_content"]

    def test_schemas_have_title(self, reg):
        assert all(t.schema.get("title") for t in reg.types())

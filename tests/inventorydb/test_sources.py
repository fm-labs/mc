import importlib.metadata
import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from inventorydb.itemtype import InventoryItemType
from inventorydb.registry import InventoryRegistry
from inventorydb.settings import DEFAULT_USER_MODULE_PACKAGE as USER_MODULE_PACKAGE
from inventorydb.sources import PackageSource, PluginSource, UserDirSource, plugin_item_packages

PING_CODE = "def ping(item, params):\n    return {'pong': item['id']}\n\nactions = {'ping': ping}\n"


@pytest.fixture(autouse=True)
def unload_test_modules() -> Iterator[None]:
    """Remove modules loaded by a test, so tests don't see each other's code."""
    yield
    prefixes = (USER_MODULE_PACKAGE, "mc_test_")
    for name in [n for n in sys.modules if n.startswith(prefixes)]:
        del sys.modules[name]


@pytest.fixture
def user_dir(tmp_path: Path) -> Path:
    path = tmp_path / "inventory"
    path.mkdir()
    return path


def write_type(root: Path, name: str, schema: Any = None, meta: Any = None, code: str | None = None) -> Path:
    path = root / name
    path.mkdir()
    (path / "schema.json").write_text(json.dumps(schema if schema is not None else {}))
    if meta is not None:
        (path / "meta.json").write_text(json.dumps(meta))
    if code is not None:
        (path / "__init__.py").write_text(code)
    return path


def load_user_types(path: Path, allow_code: bool = True) -> InventoryRegistry:
    return InventoryRegistry([UserDirSource(str(path), allow_code=allow_code)])


def get_type(reg: InventoryRegistry, name: str) -> InventoryItemType:
    found = reg.get(name)
    assert found is not None
    return found


class TestUserDirSource:
    def test_missing_dir_is_fine(self, tmp_path):
        reg = load_user_types(tmp_path / "missing")
        assert reg.types() == []
        assert reg.warnings == []

    def test_schema_only_type(self, user_dir):
        write_type(user_dir, "backup-target", {"title": "Backup Target"}, meta={"actions": []})
        reg = load_user_types(user_dir)
        item_type = get_type(reg, "backup-target")
        assert item_type.info().title == "Backup Target"
        assert item_type.meta == {"actions": []}
        assert item_type.source == str(user_dir / "backup-target")
        assert reg.warnings == []

    def test_loads_code(self, user_dir):
        write_type(user_dir, "backup-target", code=PING_CODE, meta={"actions": [{"id": "ping", "type": "form"}]})
        reg = load_user_types(user_dir)
        handler = reg.get_handler("backup-target", "actions", "ping")
        assert handler({"id": "b1"}, {}) == {"pong": "b1"}
        assert handler.__module__ == f"{USER_MODULE_PACKAGE}.backup_target"
        assert reg.warnings == []

    def test_relative_imports(self, user_dir):
        path = write_type(user_dir, "thing", code="from .helper import ping\nactions = {'ping': ping}\n")
        (path / "helper.py").write_text(PING_CODE)
        reg = load_user_types(user_dir)
        assert reg.get_handler("thing", "actions", "ping")({"id": "x"}, {}) == {"pong": "x"}

    def test_code_disabled(self, user_dir):
        write_type(user_dir, "thing", code="raise RuntimeError('must not run')\n")
        reg = load_user_types(user_dir, allow_code=False)
        # the type is available, without handlers
        assert "thing" in reg
        assert get_type(reg, "thing").module is None
        assert reg.warnings == ["thing: ignored __init__.py, user code is disabled"]

    @pytest.mark.skipif(os.name == "nt", reason="POSIX permissions")
    @pytest.mark.parametrize("target", ["root", "type_dir", "init", "helper"])
    def test_rejects_code_writable_by_others(self, user_dir, target):
        path = write_type(user_dir, "thing", code="raise RuntimeError('must not run')\n")
        (path / "helper.py").write_text("")
        unsafe = {"root": user_dir, "type_dir": path, "init": path / "__init__.py", "helper": path / "helper.py"}[
            target
        ]
        unsafe.chmod(unsafe.stat().st_mode | 0o002)
        reg = load_user_types(user_dir)
        assert get_type(reg, "thing").module is None
        assert reg.warnings == [f"thing: ignored __init__.py, {unsafe} is writable by other users"]

    def test_code_error(self, user_dir):
        write_type(user_dir, "thing", code="raise ValueError('boom')\n")
        reg = load_user_types(user_dir)
        assert f"{USER_MODULE_PACKAGE}.thing" not in sys.modules
        with pytest.raises(RuntimeError, match="ValueError: boom"):
            reg.get_handler("thing", "actions", "ping")

    @staticmethod
    def rewrite_keeping_stat(path: Path, content: str) -> None:
        """Change a file without changing its size and mtime, like an edit within the same second."""
        before = path.stat()
        assert len(content.encode()) == before.st_size
        path.write_text(content)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))

    def test_reload_runs_changed_code(self, user_dir):
        path = write_type(user_dir, "thing", code="actions = {'a': print}\n")
        reg = load_user_types(user_dir)
        assert set(get_type(reg, "thing").handlers("actions")) == {"a"}
        self.rewrite_keeping_stat(path / "__init__.py", "actions = {'b': print}\n")
        reg.load()
        assert set(get_type(reg, "thing").handlers("actions")) == {"b"}

    def test_reload_runs_changed_submodule_code(self, user_dir):
        path = write_type(user_dir, "thing", code="from .names import NAME\nactions = {NAME: print}\n")
        (path / "names.py").write_text("NAME = 'a'\n")
        (path / "sub").mkdir()
        (path / "sub" / "__init__.py").write_text("")
        (path / "sub" / "more.py").write_text("X = 1\n")
        (path / "__init__.py").write_text("from .names import NAME\nfrom .sub.more import X\nactions = {NAME: print}\n")
        reg = load_user_types(user_dir)
        assert set(get_type(reg, "thing").handlers("actions")) == {"a"}
        self.rewrite_keeping_stat(path / "names.py", "NAME = 'b'\n")
        self.rewrite_keeping_stat(path / "sub" / "more.py", "X = 2\n")
        reg.load()
        item_type = get_type(reg, "thing")
        assert set(item_type.handlers("actions")) == {"b"}
        assert item_type.module is not None
        assert item_type.module.X == 2

    def test_does_not_write_bytecode(self, user_dir):
        path = write_type(user_dir, "thing", code="from .helper import ping\nactions = {'ping': ping}\n")
        (path / "helper.py").write_text(PING_CODE)
        load_user_types(user_dir)
        assert list(user_dir.rglob("__pycache__")) == []

    def test_skips_hidden_folders_and_files(self, user_dir):
        write_type(user_dir, ".hidden")
        write_type(user_dir, "_private")
        (user_dir / "notes.txt").write_text("")
        reg = load_user_types(user_dir)
        assert reg.types() == []
        assert reg.warnings == []

    def test_folder_without_schema(self, user_dir):
        (user_dir / "thing").mkdir()
        reg = load_user_types(user_dir)
        assert reg.warnings == [f"{user_dir / 'thing'} is not an item type (no schema.json)"]

    @pytest.mark.parametrize("folder", ["my.type", "1st", "my--type", "Ünicode"])
    def test_invalid_type_name(self, user_dir, folder):
        write_type(user_dir, folder)
        reg = load_user_types(user_dir)
        assert reg.types() == []
        assert "invalid item type name" in reg.warnings[0]

    def test_underscores_become_hyphens(self, user_dir):
        write_type(user_dir, "my_type")
        assert [t.name for t in load_user_types(user_dir).types()] == ["my-type"]

    def test_cannot_replace_builtin_type(self, user_dir):
        write_type(user_dir, "ssh-key", {"title": "Mine"}, code="raise RuntimeError('must not run')\n")
        reg = InventoryRegistry([PackageSource("mc.inventory.item"), UserDirSource(str(user_dir), allow_code=True)])
        item_type = get_type(reg, "ssh-key")
        assert item_type.source == "mc.inventory.item.ssh_key"
        # the user code was not run (it would have raised)
        assert f"{USER_MODULE_PACKAGE}.ssh_key" not in sys.modules
        assert any("ssh-key: skipped definition from" in w for w in reg.warnings)


@pytest.fixture
def plugin_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An importable package `mc_test_plugins` with plugins `alpha` (with item types) and `beta` (without)."""
    root = tmp_path / "mc_test_plugins"
    for path in (root, root / "alpha", root / "alpha" / "inventory", root / "beta"):
        path.mkdir()
        (path / "__init__.py").write_text("")
    write_type(root / "alpha" / "inventory", "widget", {"title": "Widget"}, code="")
    monkeypatch.syspath_prepend(str(tmp_path))
    return root


class FakeEntryPoint:
    def __init__(self, name: str, value: str) -> None:
        self.name = name
        self.value = value
        self.module, _, self.attr = value.partition(":")


class TestPluginSource:
    def test_finds_plugin_item_packages(self, plugin_package):
        assert plugin_item_packages("mc_test_plugins") == (["mc_test_plugins.alpha.inventory"], [])

    def test_ignores_inventory_module_that_is_not_a_package(self, plugin_package):
        (plugin_package / "beta" / "inventory.py").write_text("")
        assert plugin_item_packages("mc_test_plugins") == (["mc_test_plugins.alpha.inventory"], [])

    def test_broken_plugin(self, plugin_package, monkeypatch):
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda group: [])
        (plugin_package / "beta" / "__init__.py").write_text("raise ValueError('boom')\n")
        reg = InventoryRegistry([PluginSource(["mc_test_plugins"])])
        # other plugins still load
        assert "widget" in reg
        assert reg.warnings == ["Can't load plugin mc_test_plugins.beta: ValueError: boom"]

    def test_missing_plugin_package(self):
        assert plugin_item_packages("mc_test_no_such_package") == ([], [])

    def test_loads_plugin_types(self, plugin_package, monkeypatch):
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda group: [])
        reg = InventoryRegistry([PluginSource(["mc_test_plugins"])])
        assert get_type(reg, "widget").source == "mc_test_plugins.alpha.inventory.widget"
        assert reg.warnings == []

    def test_loads_entry_points(self, plugin_package, monkeypatch):
        # an installed package, here simulated by the "alpha" plugin's item package
        entry_points = [FakeEntryPoint("ext", "mc_test_plugins.alpha.inventory")]
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda group: entry_points)
        reg = InventoryRegistry([PluginSource()])
        assert "widget" in reg

    def test_entry_point_must_name_a_package(self, monkeypatch):
        entry_points = [FakeEntryPoint("ext", "some.module:attr")]
        monkeypatch.setattr(importlib.metadata, "entry_points", lambda group: entry_points)
        reg = InventoryRegistry([PluginSource()])
        assert reg.warnings == [
            "Entry point 'ext' (some.module:attr) in inventorydb.item_types must name a package, not an attribute"
        ]

    def test_entry_points_can_be_disabled(self, monkeypatch):
        def entry_points(group):
            raise AssertionError("entry points must not be read")

        monkeypatch.setattr(importlib.metadata, "entry_points", entry_points)
        reg = InventoryRegistry([PluginSource(entry_point_group=None)])
        assert reg.types() == []

    def test_custom_entry_point_group_and_subpackage(self, plugin_package, monkeypatch):
        groups: list[str] = []

        def entry_points(group):
            groups.append(group)
            return []

        monkeypatch.setattr(importlib.metadata, "entry_points", entry_points)
        (plugin_package / "alpha" / "inventory").rename(plugin_package / "alpha" / "types")
        reg = InventoryRegistry([PluginSource(["mc_test_plugins"], "myapp.types", subpackage="types")])
        assert "widget" in reg
        assert groups == ["myapp.types"]

    def test_builtin_plugin_item_packages(self):
        assert plugin_item_packages("mc.plugin") == (["mc.plugin.apps.inventory", "mc.plugin.containers.inventory"], [])

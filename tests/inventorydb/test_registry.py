import json
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from inventorydb.metadata import InventoryShortInfo
from inventorydb.registry import (
    InventoryItemType,
    InventoryRegistry,
    build_inventory_registry,
    default_sources,
    get_inventory_registry,
    reset_inventory_registry,
    validate_item_type,
)
from inventorydb.settings import InventorySettings, configure_inventory, get_inventory_settings
from inventorydb.sources import PackageSource, PluginSource, UserDirSource

PACKAGE = "mc_test_items"

MakePackage = Callable[[str], Path]


@pytest.fixture
def make_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[MakePackage]:
    """Create empty, importable item packages; they are removed from sys.modules after the test."""
    monkeypatch.syspath_prepend(str(tmp_path))
    names: list[str] = []

    def make(name: str) -> Path:
        path = tmp_path / name
        path.mkdir()
        (path / "__init__.py").write_text("")
        names.append(name)
        return path

    yield make
    for loaded in [n for n in sys.modules if any(n == name or n.startswith(f"{name}.") for name in names)]:
        del sys.modules[loaded]


@pytest.fixture
def restore_settings() -> Iterator[None]:
    """Restore the inventory settings after the test."""
    settings = get_inventory_settings()
    yield
    configure_inventory(settings)


@pytest.fixture
def package_dir(make_package: MakePackage) -> Path:
    return make_package(PACKAGE)


def write_type(package_dir: Path, name: str, schema: Any = None, meta: Any = None, code: str = "") -> Path:
    """Write an item type package: <name>/__init__.py, schema.json and meta.json (if given)."""
    path = package_dir / name
    path.mkdir()
    (path / "__init__.py").write_text(code)
    (path / "schema.json").write_text(json.dumps(schema if schema is not None else {}))
    if meta is not None:
        (path / "meta.json").write_text(json.dumps(meta))
    return path


def get_type(reg: InventoryRegistry, name: str) -> InventoryItemType:
    found = reg.get(name)
    assert found is not None
    return found


def load(package: str = PACKAGE) -> InventoryRegistry:
    return InventoryRegistry([PackageSource(package)])


class TestPackageSource:
    def test_loads_types(self, package_dir):
        write_type(package_dir, "thing", {"title": "Thing", "description": "A thing", "version": "1", "$icon": "box"})
        write_type(package_dir, "untitled")
        reg = load()
        assert [t.name for t in reg.types()] == ["thing", "untitled"]
        assert get_type(reg, "thing").info() == InventoryShortInfo("thing", "Thing", "A thing", "1", "box")
        assert get_type(reg, "untitled").info().title == "untitled"
        assert get_type(reg, "thing").source == f"{PACKAGE}.thing"
        assert reg.warnings == []

    def test_underscored_package_is_hyphenated_type(self, package_dir):
        write_type(package_dir, "my_thing")
        assert [t.name for t in load().types()] == ["my-thing"]

    def test_loads_meta(self, package_dir):
        write_type(package_dir, "thing", meta={"index": {"columns": []}})
        write_type(package_dir, "plain")
        reg = load()
        assert get_type(reg, "thing").meta == {"index": {"columns": []}}
        assert get_type(reg, "plain").meta == {}

    def test_loads_handlers(self, package_dir):
        code = "def ping(item, params):\n    return {}\n\nactions = {'ping': ping}\n"
        write_type(package_dir, "thing", meta={"actions": [{"id": "ping", "name": "Ping", "type": "form"}]}, code=code)
        reg = load()
        assert reg.get_handler("thing", "actions", "ping").__name__ == "ping"
        assert reg.warnings == []

    def test_package_may_contain_other_modules(self, package_dir):
        path = write_type(package_dir, "thing", code="from .helper import ping\nactions = {'ping': ping}\n")
        (path / "helper.py").write_text("def ping(item, params):\n    return {}\n")
        assert load().get_handler("thing", "actions", "ping").__name__ == "ping"

    def test_skips_private_packages(self, package_dir):
        write_type(package_dir, "_private")
        reg = load()
        assert reg.types() == []
        assert reg.warnings == []

    def test_warns_about_modules_and_packages_without_schema(self, package_dir):
        write_type(package_dir, "thing")
        (package_dir / "helper.py").write_text("")
        (package_dir / "nested").mkdir()
        (package_dir / "nested" / "__init__.py").write_text("")
        reg = load()
        assert [t.name for t in reg.types()] == ["thing"]
        assert reg.warnings == [
            f"{PACKAGE}.helper is not an item type (not a package)",
            f"{PACKAGE}.nested is not an item type (no schema.json)",
        ]

    @pytest.mark.parametrize("content", ["{not json", "[]"])
    def test_skips_invalid_schema(self, package_dir, content):
        path = write_type(package_dir, "broken")
        (path / "schema.json").write_text(content)
        reg = load()
        assert "broken" not in reg
        assert reg.warnings == [f"broken: skipped, invalid schema.json in {PACKAGE}.broken"]

    def test_ignores_invalid_meta(self, package_dir):
        path = write_type(package_dir, "thing")
        (path / "meta.json").write_text("{not json")
        reg = load()
        assert get_type(reg, "thing").meta == {}
        assert reg.warnings == [f"thing: ignored invalid meta.json in {PACKAGE}.thing"]

    def test_missing_package(self):
        reg = load("mc_no_such_package")
        assert reg.types() == []
        assert reg.warnings[0].startswith("Can't import item package mc_no_such_package")

    def test_module_with_missing_dependency(self, package_dir):
        write_type(package_dir, "thing", code="import somedep_that_does_not_exist\n")
        reg = load()
        # the type stays usable, only its handlers fail with the real error
        assert "thing" in reg
        assert any("item module failed to load" in w for w in reg.warnings)
        with pytest.raises(RuntimeError, match="somedep_that_does_not_exist"):
            reg.get_handler("thing", "actions", "ping")

    def test_module_with_error(self, package_dir):
        write_type(package_dir, "thing", code="raise ValueError('boom')\n")
        with pytest.raises(RuntimeError, match="ValueError: boom"):
            load().get_handler("thing", "actions", "ping")


class TestRegistry:
    @pytest.mark.parametrize("name", ["app-stack", "app_stack", "App-Stack", " app-stack "])
    def test_lookup_accepts_name_variants(self, package_dir, name):
        write_type(package_dir, "app_stack")
        reg = load()
        assert get_type(reg, name).name == "app-stack"
        assert name in reg

    def test_unknown_type(self, package_dir):
        reg = load()
        assert reg.get("nope") is None
        with pytest.raises(NotImplementedError, match="Unknown item type 'nope'"):
            reg.get_handler("nope", "actions", "ping")

    def test_first_source_wins(self, make_package):
        first, second = make_package("mc_test_first"), make_package("mc_test_second")
        write_type(first, "thing", {"title": "First"})
        write_type(second, "thing", {"title": "Second"})
        write_type(second, "other")
        reg = InventoryRegistry([PackageSource("mc_test_first"), PackageSource("mc_test_second")])
        assert get_type(reg, "thing").schema["title"] == "First"
        assert "other" in reg
        assert reg.warnings == [
            "thing: skipped definition from mc_test_second.thing, already defined by mc_test_first.thing"
        ]

    def test_reload(self, package_dir):
        reg = load()
        write_type(package_dir, "thing")
        assert "thing" not in reg
        reg.load()
        assert "thing" in reg


class FakeModule:
    def __init__(self, actions=None, views=None):
        self.actions = actions or {}
        self.views = views or {}


def handler(item, params):
    return {}


def item_type(meta: dict[str, Any], **handlers: Any) -> InventoryItemType:
    return InventoryItemType(name="thing", schema={}, meta=meta, module=FakeModule(**handlers))  # type: ignore[arg-type]


class TestValidate:
    def test_matching_actions_and_handlers(self):
        meta = {
            "actions": [
                {"id": "run", "type": "form"},
                {"type": "separator"},
                {"id": "info", "type": "view"},
                {"id": "docs", "type": "link", "href": "https://example.com"},
            ]
        }
        assert validate_item_type(item_type(meta, actions={"run": handler}, views={"info": handler})) == []

    def test_action_without_handler(self):
        meta = {"actions": [{"id": "run", "type": "form"}, {"id": "info", "type": "view"}]}
        assert validate_item_type(item_type(meta)) == [
            "thing: form action 'run' has no handler in actions",
            "thing: view action 'info' has no handler in views",
        ]

    def test_handler_without_action(self):
        assert validate_item_type(item_type({}, actions={"run": handler}, views={"info": handler})) == [
            "thing: handler actions['run'] is not offered in meta.json",
            "thing: handler views['info'] is not offered in meta.json",
        ]

    @pytest.mark.parametrize("action_type", ["action", None])
    def test_unsupported_action_type(self, action_type):
        warnings = validate_item_type(item_type({"actions": [{"id": "run", "type": action_type}]}))
        assert len(warnings) == 1
        assert f"action 'run' has unsupported type {action_type!r}" in warnings[0]

    def test_invalid_entries(self):
        meta = {"actions": ["run", {"type": "form"}, {"id": "docs", "type": "link"}]}
        assert validate_item_type(item_type(meta)) == [
            "thing: meta.json action 'run' is not an object",
            "thing: meta.json has a 'form' action without id",
            "thing: link action 'docs' has no href",
        ]

    def test_actions_not_a_list(self):
        assert validate_item_type(item_type({"actions": {}})) == ["thing: meta.json 'actions' is not a list"]


class TestSharedRegistry:
    def test_is_cached(self):
        assert get_inventory_registry() is get_inventory_registry()

    def test_rebuilt_when_settings_change(self, package_dir, restore_settings):
        write_type(package_dir, "thing")
        before = get_inventory_registry()
        configure_inventory(InventorySettings(item_packages=(PACKAGE,), entry_point_group=None))
        reg = get_inventory_registry()
        assert reg is not before
        assert [t.name for t in reg.types()] == ["thing"]

    def test_reset(self):
        before = get_inventory_registry()
        reset_inventory_registry()
        assert get_inventory_registry() is not before


class TestDefaultSources:
    def test_standalone_defaults(self):
        # without configuration, only entry points of installed packages provide item types
        [plugins] = default_sources(InventorySettings())
        assert isinstance(plugins, PluginSource)
        assert plugins.plugin_packages == ()
        assert plugins.entry_point_group == "inventorydb.item_types"

    def test_from_settings(self):
        settings = InventorySettings(
            item_packages=("a.items", "b.items"),
            plugin_packages=("a.plugins",),
            plugin_subpackage="types",
            entry_point_group="a.types",
            user_dir="/etc/a/types",
            user_code=True,
            user_module_package="a_user_types",
        )
        first, second, plugins, user = default_sources(settings)
        assert isinstance(first, PackageSource) and first.package == "a.items"
        assert isinstance(second, PackageSource) and second.package == "b.items"
        assert isinstance(plugins, PluginSource)
        assert (plugins.plugin_packages, plugins.entry_point_group, plugins.subpackage) == (
            ("a.plugins",),
            "a.types",
            "types",
        )
        assert isinstance(user, UserDirSource)
        assert (user.path, user.allow_code, user.module_package) == ("/etc/a/types", True, "a_user_types")

    def test_overrides_file(self, tmp_path, package_dir):
        write_type(package_dir, "thing")
        overrides = tmp_path / "overrides.toml"
        overrides.write_text("[types.thing]\nenabled = false\n")
        settings = InventorySettings(item_packages=(PACKAGE,), entry_point_group=None, overrides_file=str(overrides))
        reg = build_inventory_registry(settings)
        assert reg.types() == []

"""
Sources of inventory item types.

Every source uses the same layout, one directory per item type:

    <type>/
        __init__.py     # item module: may define the handlers, actions = {...} and views = {...}
        schema.json     # required
        meta.json       # optional

Sources only discover item types; they don't import item modules. Each type gets a module loader that the
registry calls once it has accepted the type.
"""

import importlib
import importlib.metadata
import importlib.resources
import importlib.util
import json
import logging
import os
import pkgutil
import re
import stat
import sys
from collections.abc import Sequence
from functools import partial
from importlib.resources.abc import Traversable
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

from inventorydb.itemtype import InventoryItemType, type_name
from inventorydb.settings import DEFAULT_ENTRY_POINT_GROUP, DEFAULT_PLUGIN_SUBPACKAGE, DEFAULT_USER_MODULE_PACKAGE

logger = logging.getLogger(__name__)

SCHEMA_FILE = "schema.json"
META_FILE = "meta.json"
INIT_FILE = "__init__.py"

# user type folders must be named like this (after normalization), since the name is used in URLs and modules
USER_TYPE_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


class ItemTypeSource(Protocol):
    """A place item types are loaded from."""

    def load(self) -> tuple[list[InventoryItemType], list[str]]:
        """Return the item types found and warnings about the source."""
        ...


def _load_json_object(path: Traversable) -> dict[str, Any] | None:
    """Read a JSON file containing an object. Returns None (and logs) if it can't be read or isn't an object."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Can't read %s: %s", path, e)
        return None
    if not isinstance(data, dict):
        logger.error("Can't read %s: not a JSON object", path)
        return None
    return data


def read_type_files(
    type_dir: Traversable, name: str, label: str
) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    """
    Read schema.json and meta.json of an item type directory.

    :return: (schema, meta, warnings); schema is None if the directory isn't a valid item type.
    """
    schema_file = type_dir.joinpath(SCHEMA_FILE)
    if not schema_file.is_file():
        return None, {}, [f"{label} is not an item type (no {SCHEMA_FILE})"]
    schema = _load_json_object(schema_file)
    if schema is None:
        return None, {}, [f"{name}: skipped, invalid {SCHEMA_FILE} in {label}"]

    meta_file = type_dir.joinpath(META_FILE)
    if not meta_file.is_file():
        return schema, {}, []
    meta = _load_json_object(meta_file)
    if meta is None:
        return schema, {}, [f"{name}: ignored invalid {META_FILE} in {label}"]
    return schema, meta, []


class PackageSource:
    """
    Item types defined as the subpackages of a Python package, e.g. `myapp.items.server` for the type `server`.
    The schema and meta files are read as package resources, so they ship with the code.
    Subpackages starting with `_` are ignored.
    """

    def __init__(self, package: str) -> None:
        self.package = package

    def load(self) -> tuple[list[InventoryItemType], list[str]]:
        try:
            package = importlib.import_module(self.package)
        except ImportError as e:
            return [], [f"Can't import item package {self.package}: {e}"]

        root = importlib.resources.files(package)
        item_types: list[InventoryItemType] = []
        warnings: list[str] = []
        for info in sorted(pkgutil.iter_modules(getattr(package, "__path__", [])), key=lambda i: i.name):
            if info.name.startswith("_"):
                continue
            module_name = f"{self.package}.{info.name}"
            if not info.ispkg:
                warnings.append(f"{module_name} is not an item type (not a package)")
                continue
            name = type_name(info.name)
            schema, meta, file_warnings = read_type_files(root.joinpath(info.name), name, module_name)
            warnings.extend(file_warnings)
            if schema is None:
                continue
            item_types.append(
                InventoryItemType(
                    name=name,
                    schema=schema,
                    meta=meta,
                    source=module_name,
                    module_loader=partial(importlib.import_module, module_name),
                )
            )
        return item_types, warnings


def plugin_item_packages(
    plugin_package: str, subpackage: str = DEFAULT_PLUGIN_SUBPACKAGE
) -> tuple[list[str], list[str]]:
    """
    Find the `<plugin>.<subpackage>` item packages of all plugins in the plugin package.
    This imports the plugin packages themselves (their `__init__.py`), not their item packages. It uses the import
    system rather than the file system, so it also works in a PyInstaller binary.

    :return: (item package names, warnings)
    """
    try:
        package = importlib.import_module(plugin_package)
    except ImportError:
        return [], []

    packages: list[str] = []
    warnings: list[str] = []
    for info in sorted(pkgutil.iter_modules(getattr(package, "__path__", [])), key=lambda i: i.name):
        if not info.ispkg:
            continue
        item_package = f"{plugin_package}.{info.name}.{subpackage}"
        try:
            spec = importlib.util.find_spec(item_package)
        except Exception as e:
            warnings.append(f"Can't load plugin {plugin_package}.{info.name}: {type(e).__name__}: {e}")
            continue
        if spec is not None and spec.submodule_search_locations is not None:
            packages.append(item_package)
    return packages, warnings


class PluginSource:
    """
    Item types provided by plugins:

    - plugin packages: the `inventory` subpackage (see `subpackage`) of each plugin in the plugin packages,
      e.g. `myapp.plugins.<plugin>.inventory`
    - installed packages: entry points in the entry point group, whose value is the item package, e.g.
      `[project.entry-points."inventorydb.item_types"] my_plugin = "my_plugin.inventory"`

    Each item package uses the PackageSource layout.
    """

    def __init__(
        self,
        plugin_packages: Sequence[str] = (),
        entry_point_group: str | None = DEFAULT_ENTRY_POINT_GROUP,
        subpackage: str = DEFAULT_PLUGIN_SUBPACKAGE,
    ) -> None:
        self.plugin_packages = tuple(plugin_packages)
        self.entry_point_group = entry_point_group
        self.subpackage = subpackage

    def load(self) -> tuple[list[InventoryItemType], list[str]]:
        packages: list[str] = []
        warnings: list[str] = []
        for plugin_package in self.plugin_packages:
            found, found_warnings = plugin_item_packages(plugin_package, self.subpackage)
            packages.extend(found)
            warnings.extend(found_warnings)

        entry_points = importlib.metadata.entry_points(group=self.entry_point_group) if self.entry_point_group else []
        for entry_point in entry_points:
            if entry_point.attr:
                warnings.append(
                    f"Entry point '{entry_point.name}' ({entry_point.value}) in {self.entry_point_group} "
                    "must name a package, not an attribute"
                )
                continue
            packages.append(entry_point.module)

        item_types: list[InventoryItemType] = []
        for package in packages:
            package_types, package_warnings = PackageSource(package).load()
            item_types.extend(package_types)
            warnings.extend(package_warnings)
        return item_types, warnings


def _writable_by_others(paths: list[Path]) -> Path | None:
    """The first path that is writable by other users (world-writable), if any."""
    if os.name == "nt":
        return None
    for path in paths:
        if path.stat().st_mode & stat.S_IWOTH:
            return path
    return None


def load_user_module(type_dir: Path, module_name: str) -> ModuleType:
    """
    Load `<type_dir>/__init__.py` as the package `module_name`, without adding the directory to sys.path.
    Other modules in the directory can be imported relatively (`from .helper import ...`).
    """
    # drop a previously loaded version (registry reload), including its submodules
    for loaded in [n for n in sys.modules if n == module_name or n.startswith(f"{module_name}.")]:
        del sys.modules[loaded]

    spec = importlib.util.spec_from_file_location(
        module_name, type_dir / INIT_FILE, submodule_search_locations=[str(type_dir)]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Can't load {type_dir / INIT_FILE}")
    module = importlib.util.module_from_spec(spec)
    # must be registered before it runs, for relative imports
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


class UserDirSource:
    """
    User-defined item types in a directory outside the code, one folder per type.
    Folders starting with `.` or `_` are ignored. A missing directory is fine.

    Item modules (`__init__.py`) are only loaded if `allow_code` is set, and never from files or folders that are
    writable by other users. They are loaded as `<module_package>.<type_with_underscores>`.
    """

    def __init__(self, path: str, allow_code: bool = False, module_package: str = DEFAULT_USER_MODULE_PACKAGE) -> None:
        self.path = path
        self.allow_code = allow_code
        self.module_package = module_package

    def load(self) -> tuple[list[InventoryItemType], list[str]]:
        root = Path(self.path)
        if not root.is_dir():
            return [], []

        item_types: list[InventoryItemType] = []
        warnings: list[str] = []
        for type_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            if type_dir.name.startswith((".", "_")):
                continue
            name = type_name(type_dir.name)
            if not USER_TYPE_NAME_RE.match(name):
                warnings.append(f"{type_dir} skipped: invalid item type name (use lowercase letters, digits and -)")
                continue
            schema, meta, file_warnings = read_type_files(type_dir, name, str(type_dir))
            warnings.extend(file_warnings)
            if schema is None:
                continue

            module_loader = None
            if (type_dir / INIT_FILE).is_file():
                module_loader, code_warning = self._module_loader(root, type_dir, name)
                if code_warning:
                    warnings.append(code_warning)
            item_types.append(
                InventoryItemType(
                    name=name, schema=schema, meta=meta, source=str(type_dir), module_loader=module_loader
                )
            )
        return item_types, warnings

    def _module_loader(self, root: Path, type_dir: Path, name: str) -> tuple[partial[ModuleType] | None, str | None]:
        if not self.allow_code:
            return None, f"{name}: ignored {INIT_FILE}, user code is disabled"
        unsafe = _writable_by_others([root, type_dir, *sorted(type_dir.rglob("*.py"))])
        if unsafe:
            return None, f"{name}: ignored {INIT_FILE}, {unsafe} is writable by other users"
        module_name = f"{self.module_package}.{name.replace('-', '_')}"
        return partial(load_user_module, type_dir, module_name), None

"""
Registry of inventory item types.

An item type is made of a JSON schema, optional UI metadata (meta.json) and an item module that may
expose `actions` and `views` handler dicts. The registry collects item types from one or more sources once,
validates them, and serves all lookups from memory.
"""

import importlib
import importlib.resources
import json
import logging
import pkgutil
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from importlib.resources.abc import Traversable
from types import ModuleType
from typing import Any, Literal, Protocol

from inventorydb.metadata import InventoryShortInfo

logger = logging.getLogger(__name__)

# Item handlers take (item, params) and return a result dict; they may be sync or async
ItemMethod = Callable[[dict[str, Any], dict[str, Any]], Any]
HandlerKind = Literal["actions", "views"]

ITEM_PACKAGE = "mc.inventory.item"
SCHEMA_FILE = "schema.json"
META_FILE = "meta.json"

# action types in meta.json, and the handler dict of the item module they call (None: handled by the UI)
ACTION_TYPE_HANDLERS: dict[str, HandlerKind | None] = {
    "form": "actions",
    "view": "views",
    "link": None,
    "separator": None,
}


def type_name(item_type: str) -> str:
    """Canonical item type name, lowercase and hyphenated ('App_Stack' -> 'app-stack')."""
    return item_type.strip().lower().replace("_", "-")


@dataclass
class InventoryItemType:
    name: str
    schema: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)
    module: ModuleType | None = None
    # set if the item module exists but failed to import
    module_error: str | None = None
    # where the item type was loaded from, for log messages
    source: str = ""

    def handlers(self, kind: HandlerKind) -> dict[str, ItemMethod]:
        """The `actions` or `views` dict of the item module ({} if there is none)."""
        handlers = getattr(self.module, kind, None) if self.module else None
        return handlers if isinstance(handlers, dict) else {}

    def get_handler(self, kind: HandlerKind, name: str) -> ItemMethod:
        """
        :raises RuntimeError: If the item module failed to load.
        :raises NotImplementedError: If there is no such handler.
        """
        if self.module_error:
            raise RuntimeError(f"Item module of '{self.name}' failed to load: {self.module_error}")
        method = self.handlers(kind).get(name)
        if method is None:
            label = "Action" if kind == "actions" else "View"
            raise NotImplementedError(f"{label} '{name}' for item type '{self.name}' is not implemented.")
        return method

    def info(self) -> InventoryShortInfo:
        return InventoryShortInfo(
            item_type=self.name,
            title=self.schema.get("title", self.name),
            description=self.schema.get("description"),
            version=self.schema.get("version"),
            icon=self.schema.get("$icon"),
        )


class ItemTypeSource(Protocol):
    """A place item types are loaded from."""

    def load(self) -> tuple[list[InventoryItemType], list[str]]:
        """Return the item types and warnings about the source."""
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


def _import_item_module(module_name: str) -> tuple[ModuleType | None, str | None]:
    """Import an item module. Returns (module, None), or (None, error) if the import fails."""
    try:
        return importlib.import_module(module_name), None
    except Exception as e:
        logger.exception("Failed to import item module %s", module_name)
        return None, f"{type(e).__name__}: {e}"


class PackageSource:
    """
    Item types defined as the subpackages of a Python package, one per type:

        <package>/<type_with_underscores>/
            __init__.py     # may define the handlers: actions = {...}, views = {...}
            schema.json     # required
            meta.json       # optional

    The schema and meta files are read as package resources, so they ship with the code.
    """

    def __init__(self, package: str = ITEM_PACKAGE) -> None:
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
            schema_file = root.joinpath(info.name, SCHEMA_FILE)
            if not info.ispkg or not schema_file.is_file():
                warnings.append(f"{module_name} is not an item type (no {info.name}/{SCHEMA_FILE})")
                continue

            name = type_name(info.name)
            schema = _load_json_object(schema_file)
            if schema is None:
                warnings.append(f"{name}: skipped, invalid {SCHEMA_FILE} in {module_name}")
                continue

            meta: dict[str, Any] = {}
            meta_file = root.joinpath(info.name, META_FILE)
            if meta_file.is_file():
                loaded_meta = _load_json_object(meta_file)
                if loaded_meta is None:
                    warnings.append(f"{name}: ignored invalid {META_FILE} in {module_name}")
                else:
                    meta = loaded_meta

            module, module_error = _import_item_module(module_name)
            item_types.append(
                InventoryItemType(
                    name=name,
                    schema=schema,
                    meta=meta,
                    module=module,
                    module_error=module_error,
                    source=module_name,
                )
            )
        return item_types, warnings


def validate_item_type(item_type: InventoryItemType) -> list[str]:
    """Check that the actions offered in meta.json and the handlers of the item module match."""
    name = item_type.name
    warnings: list[str] = []
    if item_type.module_error:
        warnings.append(f"{name}: item module failed to load: {item_type.module_error}")

    actions_def = item_type.meta.get("actions", [])
    if not isinstance(actions_def, list):
        warnings.append(f"{name}: meta.json 'actions' is not a list")
        actions_def = []

    referenced: dict[HandlerKind, set[str]] = {"actions": set(), "views": set()}
    for entry in actions_def:
        if not isinstance(entry, dict):
            warnings.append(f"{name}: meta.json action {entry!r} is not an object")
            continue
        action_id = entry.get("id")
        action_type = entry.get("type")
        if action_type not in ACTION_TYPE_HANDLERS:
            supported = ", ".join(ACTION_TYPE_HANDLERS)
            warnings.append(f"{name}: action '{action_id}' has unsupported type {action_type!r} (use {supported})")
            continue
        if action_type == "link" and not entry.get("href"):
            warnings.append(f"{name}: link action '{action_id}' has no href")
        kind = ACTION_TYPE_HANDLERS[action_type]
        if kind is None:
            continue
        if not action_id:
            warnings.append(f"{name}: meta.json has a '{action_type}' action without id")
            continue
        referenced[kind].add(action_id)
        if not item_type.module_error and action_id not in item_type.handlers(kind):
            warnings.append(f"{name}: {action_type} action '{action_id}' has no handler in {kind}")

    kinds: tuple[HandlerKind, ...] = ("actions", "views")
    for kind in kinds:
        for handler_name in sorted(set(item_type.handlers(kind)) - referenced[kind]):
            warnings.append(f"{name}: handler {kind}['{handler_name}'] is not offered in meta.json")
    return warnings


class InventoryRegistry:
    """Item types from all sources. If several sources define a type, the first one wins."""

    def __init__(self, sources: Iterable[ItemTypeSource]) -> None:
        self._sources = list(sources)
        self._types: dict[str, InventoryItemType] = {}
        self.warnings: list[str] = []
        self.load()

    def load(self) -> None:
        """(Re)load all item types from the sources and log validation warnings."""
        item_types: dict[str, InventoryItemType] = {}
        warnings: list[str] = []
        for source in self._sources:
            loaded, source_warnings = source.load()
            warnings.extend(source_warnings)
            for item_type in loaded:
                if item_type.name in item_types:
                    warnings.append(
                        f"{item_type.name}: skipped definition from {item_type.source}, "
                        f"already defined by {item_types[item_type.name].source}"
                    )
                    continue
                item_types[item_type.name] = item_type

        for item_type in item_types.values():
            warnings.extend(validate_item_type(item_type))

        self._types = item_types
        self.warnings = warnings
        for warning in warnings:
            logger.warning("Inventory: %s", warning)
        logger.info("Inventory: loaded %d item types", len(item_types))

    def get(self, item_type: str) -> InventoryItemType | None:
        """Look up an item type; accepts hyphenated and underscored names."""
        return self._types.get(type_name(item_type))

    def __contains__(self, item_type: str) -> bool:
        return self.get(item_type) is not None

    def types(self) -> list[InventoryItemType]:
        """All item types, sorted by name."""
        return sorted(self._types.values(), key=lambda t: t.name)

    def get_handler(self, item_type: str, kind: HandlerKind, name: str) -> ItemMethod:
        """
        :raises NotImplementedError: If the item type or the handler doesn't exist.
        :raises RuntimeError: If the item module failed to load.
        """
        found = self.get(item_type)
        if found is None:
            raise NotImplementedError(f"Unknown item type '{item_type}'.")
        return found.get_handler(kind, name)


def default_sources() -> list[ItemTypeSource]:
    return [PackageSource(ITEM_PACKAGE)]


_registry: InventoryRegistry | None = None
_registry_lock = threading.Lock()


def get_inventory_registry() -> InventoryRegistry:
    """The shared registry, loaded from the default sources on first use."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = InventoryRegistry(default_sources())
    return _registry


def reset_inventory_registry() -> None:
    """Drop the shared registry; the next get_inventory_registry() call loads it again."""
    global _registry
    with _registry_lock:
        _registry = None

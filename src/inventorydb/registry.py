"""
Registry of inventory item types.

An item type is made of a JSON schema, optional UI metadata (meta.json) and an item module that may
expose `actions` and `views` handler dicts. The registry collects item types from its sources once,
applies the overrides from inventory.toml, validates them, and serves all lookups from memory.

Default sources, in order of precedence (if several define a type, the first one wins):

1. built-in types: the packages in `mc.inventory.item`
2. plugin types: `mc.plugin.<plugin>.inventory` packages and `mc.inventory_types` entry points
3. user types: folders in `$CONFIG_DIR/inventory` (item modules only with INVENTORY_USER_CODE=true)
"""

import logging
import os
import threading
from collections.abc import Iterable

from inventorydb.itemtype import HandlerKind, InventoryItemType, ItemMethod, type_name
from inventorydb.overrides import load_overrides
from inventorydb.sources import ITEM_PACKAGE, ItemTypeSource, PackageSource, PluginSource, UserDirSource
from mc import config

__all__ = [
    "HandlerKind",
    "InventoryItemType",
    "InventoryRegistry",
    "ItemMethod",
    "get_inventory_registry",
    "reset_inventory_registry",
    "type_name",
    "validate_item_type",
]

logger = logging.getLogger(__name__)

# action types in meta.json, and the handler dict of the item module they call (None: handled by the UI)
ACTION_TYPE_HANDLERS: dict[str, HandlerKind | None] = {
    "form": "actions",
    "view": "views",
    "link": None,
    "separator": None,
}


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

    def __init__(self, sources: Iterable[ItemTypeSource], overrides_file: str | None = None) -> None:
        self._sources = list(sources)
        self._overrides_file = overrides_file
        self._types: dict[str, InventoryItemType] = {}
        self.warnings: list[str] = []
        self.load()

    def load(self) -> None:
        """(Re)load all item types from the sources and log validation warnings."""
        overrides, warnings = load_overrides(self._overrides_file) if self._overrides_file else ({}, [])
        disabled = {name for name, override in overrides.items() if not override.enabled}

        item_types: dict[str, InventoryItemType] = {}
        seen: set[str] = set()
        for source in self._sources:
            candidates, source_warnings = source.load()
            warnings.extend(source_warnings)
            for item_type in candidates:
                if item_type.name in item_types:
                    warnings.append(
                        f"{item_type.name}: skipped definition from {item_type.source}, "
                        f"already defined by {item_types[item_type.name].source}"
                    )
                    continue
                seen.add(item_type.name)
                if item_type.name in disabled:
                    logger.info("Inventory: %s from %s is disabled", item_type.name, item_type.source)
                    continue
                item_types[item_type.name] = item_type

        warnings.extend(
            f"{self._overrides_file}: [types.{name}] matches no item type" for name in sorted(set(overrides) - seen)
        )
        for name, item_type in item_types.items():
            # only accepted types run their module code
            item_type.load_module()
            if name in overrides:
                overrides[name].apply(item_type)
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
        """All item types: those with an order first (by order), then the others by name."""
        return sorted(self._types.values(), key=lambda t: (t.order is None, t.order or 0, t.name))

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
    return [
        PackageSource(ITEM_PACKAGE),
        PluginSource(),
        UserDirSource(os.path.join(config.CONFIG_DIR, "inventory"), allow_code=config.INVENTORY_USER_CODE),
    ]


def default_overrides_file() -> str:
    return os.path.join(config.CONFIG_DIR, "inventory.toml")


_registry: InventoryRegistry | None = None
_registry_lock = threading.Lock()


def get_inventory_registry() -> InventoryRegistry:
    """The shared registry, loaded from the default sources on first use."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = InventoryRegistry(default_sources(), default_overrides_file())
    return _registry


def reset_inventory_registry() -> None:
    """Drop the shared registry; the next get_inventory_registry() call loads it again."""
    global _registry
    with _registry_lock:
        _registry = None

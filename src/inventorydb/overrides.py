"""
Item type overrides from `inventory.toml`:

    [types.app-template]
    enabled = false             # don't load this item type

    [types.app-stack]
    title = "Stacks"            # replaces the schema title
    icon = "layers"             # replaces the schema $icon
    order = 1                   # position in the type list; types without order follow, sorted by name
"""

import os
import tomllib
from dataclasses import dataclass
from typing import Any

from inventorydb.itemtype import InventoryItemType, type_name

# allowed keys and their types
OVERRIDE_FIELDS: dict[str, type] = {"enabled": bool, "title": str, "icon": str, "order": int}


@dataclass(frozen=True)
class ItemTypeOverride:
    enabled: bool = True
    title: str | None = None
    icon: str | None = None
    order: int | None = None

    def apply(self, item_type: InventoryItemType) -> None:
        # copy the schema, so the source's dict stays unchanged
        if self.title is not None:
            item_type.schema = {**item_type.schema, "title": self.title}
        if self.icon is not None:
            item_type.schema = {**item_type.schema, "$icon": self.icon}
        if self.order is not None:
            item_type.order = self.order


def load_overrides(path: str) -> tuple[dict[str, ItemTypeOverride], list[str]]:
    """
    Read the overrides file. A missing file means no overrides.

    :return: (overrides by item type name, warnings)
    """
    if not os.path.exists(path):
        return {}, []
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        return {}, [f"Ignored {path}: {e}"]

    warnings = [f"{path}: unknown section [{key}]" for key in data if key != "types"]
    types = data.get("types", {})
    if not isinstance(types, dict):
        return {}, [*warnings, f"{path}: 'types' must be a table"]

    overrides: dict[str, ItemTypeOverride] = {}
    for raw_name, values in types.items():
        if not isinstance(values, dict):
            warnings.append(f"{path}: [types.{raw_name}] must be a table")
            continue
        fields: dict[str, Any] = {}
        for key, value in values.items():
            expected = OVERRIDE_FIELDS.get(key)
            if expected is None:
                warnings.append(f"{path}: [types.{raw_name}] unknown key '{key}'")
            elif not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
                warnings.append(f"{path}: [types.{raw_name}] '{key}' must be {expected.__name__}")
            else:
                fields[key] = value
        overrides[type_name(raw_name)] = ItemTypeOverride(**fields)
    return overrides, warnings

"""The inventory item type model, shared by the registry and its sources."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Literal

from inventorydb.metadata import InventoryShortInfo

logger = logging.getLogger(__name__)

# Item handlers take (item, params) and return a result dict; they may be sync or async
ItemMethod = Callable[[dict[str, Any], dict[str, Any]], Any]
HandlerKind = Literal["actions", "views"]
# imports (or executes) the item module of a type
ModuleLoader = Callable[[], ModuleType]


def type_name(item_type: str) -> str:
    """Canonical item type name, lowercase and hyphenated ('App_Stack' -> 'app-stack')."""
    return item_type.strip().lower().replace("_", "-")


@dataclass
class InventoryItemType:
    name: str
    schema: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)
    # where the item type was loaded from, for log messages
    source: str = ""
    # loads the item module; called by the registry once the type is accepted, so skipped types run no code
    module_loader: ModuleLoader | None = None
    module: ModuleType | None = None
    # set if the item module failed to load
    module_error: str | None = None
    # sort position in the type list (from inventory.toml); types without order come last, by name
    order: int | None = None

    def load_module(self) -> None:
        """Run the module loader, recording any error instead of raising it."""
        if self.module_loader is None:
            return
        try:
            self.module = self.module_loader()
        except Exception as e:
            logger.exception("Failed to load the item module of '%s' from %s", self.name, self.source)
            self.module_error = f"{type(e).__name__}: {e}"

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

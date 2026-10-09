import asyncio
import importlib
import inspect
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

ITEM_MODULE_PACKAGE = "mc.inventory.item"

# Item handlers take (item, params) and return a result dict; they may be sync or async
ItemMethod = Callable[[dict[str, Any], dict[str, Any]], Any]


def _get_item_handler(item_type: str, registry: str, name: str) -> ItemMethod:
    """
    Dynamically load a handler from the `actions` or `views` registry of an inventory item module.

    :param item_type: The type of the inventory item (e.g., "app_stack", "container_node").
    :param registry: The registry attribute of the module ("actions" or "views").
    :param name: The name of the action or view (e.g., "ping", "deploy").
    :return: The handler method.
    :raises NotImplementedError: If the item type has no module, or the module has no such handler.
    """
    item_type = item_type.lower().replace("-", "_")
    kind = registry.removesuffix("s")
    if not item_type.isidentifier():
        raise NotImplementedError(f"Invalid item type '{item_type}'.")

    module_name = f"{ITEM_MODULE_PACKAGE}.{item_type}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        # only treat a missing item module as "not implemented"; missing dependencies are real errors
        if e.name != module_name:
            raise
        raise NotImplementedError(f"Item type '{item_type}' has no {registry}.") from e

    handlers = getattr(module, registry, None) or {}
    method: ItemMethod | None = handlers.get(name)
    if not method:
        raise NotImplementedError(f"{kind.capitalize()} '{name}' for item type '{item_type}' is not implemented.")
    return method


async def _invoke(method: ItemMethod, item: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    """Await async handlers directly, run sync handlers in the thread pool."""
    result: dict[str, Any]
    if inspect.iscoroutinefunction(method):
        result = await method(item, params)
    else:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, method, item, params)
    return result


def get_inventory_item_action_handler(item_type: str, action_name: str) -> ItemMethod:
    return _get_item_handler(item_type, "actions", action_name)


def get_inventory_item_view_handler(item_type: str, view_name: str) -> ItemMethod:
    return _get_item_handler(item_type, "views", view_name)


async def handle_inventory_item_action(
    item_type: str, item: dict[str, Any], action_name: str, action_params: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Handle an action request for a specific inventory item.

    :param item_type: The type of the inventory item (e.g., "app_stack", "container_node").
    :param item: The inventory item.
    :param action_name: The name of the action to perform (e.g., "ping", "deploy").
    :param action_params: A dictionary of parameters required for the action.
    :return: A dictionary containing the result of the action.
    :raises NotImplementedError: If the action is not implemented for the item type.
    """
    method = get_inventory_item_action_handler(item_type, action_name)
    logger.debug("Running action '%s' on %s/%s", action_name, item_type, item.get("id"))
    return await _invoke(method, item, action_params or {})


async def handle_inventory_item_view(
    item_type: str, item: dict[str, Any], view_name: str, view_params: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Handle a view request for a specific inventory item.

    :param item_type: The type of the inventory item (e.g., "app_stack", "container_node").
    :param item: The inventory item.
    :param view_name: The name of the view to render (e.g., "stackfile").
    :param view_params: A dictionary of parameters required for the view.
    :return: A dictionary containing the result of the view.
    :raises NotImplementedError: If the view is not implemented for the item type.
    """
    method = get_inventory_item_view_handler(item_type, view_name)
    logger.debug("Rendering view '%s' on %s/%s", view_name, item_type, item.get("id"))
    return await _invoke(method, item, view_params or {})

import asyncio
import inspect
import logging
from typing import Any

from inventorydb.registry import ItemMethod, get_inventory_registry

logger = logging.getLogger(__name__)


async def invoke_item_handler(method: ItemMethod, item: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    """Await async handlers directly, run sync handlers in the thread pool."""
    result: dict[str, Any]
    if inspect.iscoroutinefunction(method):
        result = await method(item, params)
    else:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, method, item, params)
    return result


def get_inventory_item_action_handler(item_type: str, action_name: str) -> ItemMethod:
    """
    :raises NotImplementedError: If the item type or the action doesn't exist.
    :raises RuntimeError: If the item module failed to load.
    """
    return get_inventory_registry().get_handler(item_type, "actions", action_name)


def get_inventory_item_view_handler(item_type: str, view_name: str) -> ItemMethod:
    """
    :raises NotImplementedError: If the item type or the view doesn't exist.
    :raises RuntimeError: If the item module failed to load.
    """
    return get_inventory_registry().get_handler(item_type, "views", view_name)


async def handle_inventory_item_action(
    item_type: str, item: dict[str, Any], action_name: str, action_params: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Handle an action request for a specific inventory item.

    :param item_type: The type of the inventory item (e.g., "app-stack", "container_node").
    :param item: The inventory item.
    :param action_name: The name of the action to perform (e.g., "ping", "deploy").
    :param action_params: A dictionary of parameters required for the action.
    :return: A dictionary containing the result of the action.
    :raises NotImplementedError: If the action is not implemented for the item type.
    """
    method = get_inventory_item_action_handler(item_type, action_name)
    logger.debug("Running action '%s' on %s/%s", action_name, item_type, item.get("id"))
    return await invoke_item_handler(method, item, action_params or {})


async def handle_inventory_item_view(
    item_type: str, item: dict[str, Any], view_name: str, view_params: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Handle a view request for a specific inventory item.

    :param item_type: The type of the inventory item (e.g., "app-stack", "container_node").
    :param item: The inventory item.
    :param view_name: The name of the view to render (e.g., "stackfile").
    :param view_params: A dictionary of parameters required for the view.
    :return: A dictionary containing the result of the view.
    :raises NotImplementedError: If the view is not implemented for the item type.
    """
    method = get_inventory_item_view_handler(item_type, view_name)
    logger.debug("Rendering view '%s' on %s/%s", view_name, item_type, item.get("id"))
    return await invoke_item_handler(method, item, view_params or {})

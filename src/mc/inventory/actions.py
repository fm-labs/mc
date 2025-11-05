import asyncio

from mc.inventory.storage import get_inventory_storage_instance

def get_inventory_item_action_handler(item_type: str, action_name: str):
    """
    Dynamically load and return the action handler method for a given inventory item type and action name.

    :param item_type: The type of the inventory item (e.g., "host", "container_host").
    :param action_name: The name of the action to perform (e.g., "ping", "deploy_template").
    :return: The action handler method.
    :raises NotImplementedError: If the action is not implemented for the item type.
    """
    item_type = item_type.lower().replace("-", "_")
    module_name = f"mc.inventory.item.{item_type}"
    attr_name = "actions"

    try:
        module = __import__(module_name, fromlist=[attr_name])
        actions = getattr(module, attr_name)
        method = actions.get(action_name)
        if not method:
            raise NotImplementedError(f"Action '{action_name}' for item type '{item_type}' is not implemented.")
        return method
    except (ImportError, AttributeError) as e:
        raise NotImplementedError(f"Module for action '{action_name}' on item type '{item_type}' could not be loaded") from e


async def handle_inventory_item_action(item_type: str, item_key: str, action_name: str, action_params: dict) -> dict:
    """
    Handle an action request for a specific inventory item.

    :param item_type: The type of the inventory item (e.g., "host", "container_host").
    :param item_key: The unique key of the inventory item.
    :param action_name: The name of the action to perform (e.g., "ping", "deploy_template").
    :param action_params: A dictionary of parameters required for the action.
    :return: A dictionary containing the result of the action.
    :raises ValueError: If the item is not found.
    :raises NotImplementedError: If the action is not implemented for the item type.
    """
    storage = get_inventory_storage_instance()
    item_type = item_type.lower().replace("-", "_")
    item = storage.get_item(item_type, item_key)
    if not item:
        raise ValueError(f"Item '{item_key}' of type '{item_type}' not found.")

    method = get_inventory_item_action_handler(item_type, action_name)
    action_params = action_params or {}

    # if the method is async, await it directly
    print("Action method type:", type(method))
    if asyncio.iscoroutinefunction(method):
        print("Handling async action method")
        result = await method(item, action_params)
        print("Action result:", result)
        return result

    # if the method is sync, run in thread pool
    print("Handling sync action method in async context")
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, method, item, action_params)
    #result = {"status": "error", "error": "Synchronous action methods are not supported yet"}
    print("Action result:", result)
    return result


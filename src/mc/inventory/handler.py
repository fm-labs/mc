import asyncio
import inspect


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


async def handle_inventory_item_action(item_type: str, item: dict, action_name: str, action_params: dict) -> dict:
    """
    Handle an action request for a specific inventory item.

    :param item_type: The type of the inventory item (e.g., "host", "container_host").
    :param item: The unique key of the inventory item.
    :param action_name: The name of the action to perform (e.g., "ping", "deploy_template").
    :param action_params: A dictionary of parameters required for the action.
    :return: A dictionary containing the result of the action.
    :raises ValueError: If the item is not found.
    :raises NotImplementedError: If the action is not implemented for the item type.
    """
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


def get_inventory_item_view_handler(item_type: str, view_name: str):
    """
    Dynamically load and return the view handler method for a given inventory item type and view name.

    :param item_type: The type of the inventory item (e.g., "host", "container_host").
    :param view_name: The name of the view to perform (e.g., "ping", "deploy_template").
    :return: The view handler method.
    :raises NotImplementedError: If the view is not implemented for the item type.
    """
    item_type = item_type.lower().replace("-", "_")
    module_name = f"mc.inventory.item.{item_type}"
    attr_name = "views"

    try:
        module = __import__(module_name, fromlist=[attr_name])
        views = getattr(module, attr_name)
        method = views.get(view_name)
        if not method:
            raise NotImplementedError(f"Action '{view_name}' for item type '{item_type}' is not implemented.")
        return method
    except (ImportError, AttributeError) as e:
        raise NotImplementedError(f"Module for view '{view_name}' on item type '{item_type}' could not be loaded") from e


async def handle_inventory_item_view(item_type: str, item: dict, view_name: str, view_params: dict) -> dict:
    """
    Handle an view request for a specific inventory item.

    :param item_type: The type of the inventory item (e.g., "host", "container_host").
    :param item: The unique key of the inventory item.
    :param view_name: The name of the view to perform (e.g., "ping", "deploy_template").
    :param view_params: A dictionary of parameters required for the view.
    :return: A dictionary containing the result of the view.
    :raises ValueError: If the item is not found.
    :raises NotImplementedError: If the view is not implemented for the item type.
    """
    method = get_inventory_item_view_handler(item_type, view_name)
    view_params = view_params or {}
    # if the method is async, await it directly
    print("View method type:", type(method))
    if inspect.iscoroutinefunction(method):
        print("Handling async view method")
        result = await method(item, view_params)
        print("View result:", result)
        return result

    # if the method is sync, run in thread pool
    print("Handling sync view method in async context")
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, method, item, view_params)
    #result = {"status": "error", "error": "Synchronous view methods are not supported yet"}
    print("View result:", result)
    return result

from kloudia.inventory.storage import get_inventory_storage_instance


def handle_inventory_item_action(item_type: str, uuid: str, action_name: str, action_params: dict) -> dict:
    storage = get_inventory_storage_instance()
    item = storage.get_item(item_type, uuid)
    if not item:
        raise ValueError(f"Item '{uuid}' of type '{item_type}' not found.")

    module_name = f"kloudia.inventory.{item_type}"
    attr_name = "actions"

    try:
        module = __import__(module_name, fromlist=[attr_name])
        print(module)
        actions = getattr(module, attr_name)
        print(actions)
        method = actions.get(action_name)
        print(method)
        if not method:
            raise NotImplementedError(f"Action '{action_name}' for item type '{item_type}' is not implemented.")
    except (ImportError, AttributeError) as e:
        #return {"error": f"Action '{action_name}' for item type '{item_type}' is not implemented."}
        raise NotImplementedError(f"Action '{action_name}' for item type '{item_type}' is not implemented!") from e

    return method(item, action_params)


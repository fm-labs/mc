import os


def handle_container_registry_login(item: dict, action_params: dict) -> dict:
    registry_url= item.get("registry_url")
    username = item.get("username")
    #password = item_props.get("password")
    #is_private = item_props.get("is_private", True)
    return container_registry_login(registry_url, username)


actions = {
    "login": handle_container_registry_login,
}
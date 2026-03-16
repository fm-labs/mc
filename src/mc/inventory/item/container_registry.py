import os

from mc.docker.registry_helper import container_registry_login


def handle_container_registry_login(item: dict, action_params: dict) -> dict:
    registry_url= item.get("registry_url")
    username = item.get("username")
    #is_private = item_props.get("is_private", True)

    password = action_params.get("password")
    return container_registry_login(registry_url, username, password)


actions = {
    "login": handle_container_registry_login,
}
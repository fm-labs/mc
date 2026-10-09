from mc.docker.registry_helper import container_registry_login


def handle_container_registry_login(item: dict, action_params: dict) -> dict:
    registry_url = item.get("registry_url")
    username = item.get("username")

    password = action_params.get("password")
    # todo support action_params["store"]: store the password in config or .env
    return container_registry_login(registry_url, username, password)


actions = {
    "login": handle_container_registry_login,
}

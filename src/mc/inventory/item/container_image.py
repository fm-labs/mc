from mc.inventory.storage import get_inventory_storage_instance
from rx.helper.dockercli_helper import dockercli_image_pull


def handle_container_image_pull(item: dict, action_params: dict) -> dict:
    #item_name = item.get("name")
    item_props = item.get("properties", {})
    image_url = item_props.get("image_url")
    image_tag = item_props.get("tag", "latest")

    image_tag = action_params.get("tag", image_tag)
    image_url_tagged = f"{image_url}:{image_tag}"
    container_host = action_params.get("container_host")
    pull_policy = action_params.get("pull_policy", "if_not_present")

    print(f"Pulling container image '{image_url_tagged}' with policy '{pull_policy}' on host '{container_host or 'local'}'")

    env = {}
    if container_host:
        # find related container_host inventory item
        storage = get_inventory_storage_instance()
        ch_item = storage.get_item_by_name(inventory_type="container_host", name=container_host)
        if not ch_item:
            raise ValueError(f"Container host '{container_host}' not found in inventory.")
        ch_props = ch_item.get("properties", {})
        container_host_url = ch_props.get("url")
        if not container_host_url:
            raise ValueError(f"Container host '{container_host}' has no URL defined.")

        print(f"Using container host URL: {container_host_url}")
        env["DOCKER_HOST"] = container_host_url

    try:
        dockercli_image_pull(image_url_tagged, env=env)
    except Exception as e:
        raise RuntimeError(f"Error pulling image: {e}")

    return {
        "status": "pulled",
        "message": f"Container image '{image_url_tagged}' pulled successfully on host '{container_host or 'local'}'.",
        "image_url": image_url_tagged,
        "container_host": container_host,
    }


actions = {
    "pull": handle_container_image_pull,
}


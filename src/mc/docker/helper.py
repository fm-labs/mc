from typing import Literal


def docker_prune(client,
                 scope: Literal["system", "containers", "images", "volumes", "networks", "buildcache", "buildx"]):

    # BUILDS_FILTER = {"until": "2h"}
    # IMAGES_FILTERS = {"dangling": False}

    pruned = {}
    if scope == "system":
        pruned["containers"] = client.containers.prune()
        pruned["images"] = client.images.prune(filters={"dangling": False}) # all unused, like `image prune -a`
        pruned["buildcache"] = client.images.prune_builds()
        pruned["volumes"] = client.volumes.prune()
        pruned["networks"] = client.networks.prune()
    elif scope == "buildcache":
        pruned["buildcache"] = client.images.prune_builds()
    elif scope == "containers":
        pruned["containers"] = client.containers.prune()
    elif scope == "images":
        pruned["images"] = client.images.prune(filters={"dangling": False}) # all unused, like `image prune -a`
    elif scope == "volumes":
        pruned["volumes"] = client.volumes.prune()
    elif scope == "networks":
        pruned["networks"] = client.networks.prune()
    elif scope == "buildx":
        # todo shell out: docker buildx prune
        raise ValueError("Not supported yet")
    else:
        raise ValueError("Invalid scope specified.")
    return pruned
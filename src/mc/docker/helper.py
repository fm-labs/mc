import os
from typing import Literal

from mc.plugin.containers.manager import ContainerClient


def docker_prune(client: ContainerClient,
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


def _require_volume(client: ContainerClient, name: str) -> None:
    # Mounting a missing named volume makes docker create an empty one, so check first.
    from docker.errors import NotFound

    try:
        client.volumes.get(name)
    except NotFound:
        raise ValueError(f"Volume '{name}' does not exist.")


def _split_backup_path(path: str) -> tuple[str, str]:
    # A relative bind-mount source would be taken as a volume name, so require an absolute host path.
    if not os.path.isabs(path):
        raise ValueError(f"Backup file must be an absolute path on the docker host: '{path}'")
    directory, filename = os.path.split(os.path.normpath(path))
    if path.endswith("/") or filename in ("", ".", ".."):
        raise ValueError(f"Backup file must include a file name: '{path}'")
    return directory, filename


def docker_volume_clone(client: ContainerClient, source_volume: str, target_volume: str, **kwargs):
    """
    Clone a docker volume into a new volume.

    :param client: docker client
    :param source_volume: source volume (must exist)
    :param target_volume: target volume (must not exist yet)
    :param kwargs: docker container run args
    """
    from docker.errors import NotFound

    _require_volume(client, source_volume)
    try:
        client.volumes.get(target_volume)
        raise ValueError(f"Target volume '{target_volume}' already exists.")
    except NotFound:
        pass

    client.volumes.create(target_volume)
    return client.containers.run(
        "alpine", ["cp", "-a", "/from/.", "/to/"],
        volumes={source_volume: {"bind": "/from", "mode": "ro"},
                 target_volume: {"bind": "/to", "mode": "rw"}},
        remove=True,
        **kwargs
    )


def docker_volume_backup(client: ContainerClient, source_volume: str, target_file: str, **kwargs):
    """
    Backup a docker volume to a .tar.gz file on the docker host.

    :param client: docker client
    :param source_volume: source volume (must exist)
    :param target_file: absolute path of the backup file on the docker host
    :param kwargs: docker container run args
    """
    _require_volume(client, source_volume)
    directory, filename = _split_backup_path(target_file)
    return client.containers.run(
        "alpine", ["tar", "czf", f"/backup/{filename}", "--numeric-owner", "-C", "/data", "."],
        volumes={source_volume: {"bind": "/data", "mode": "ro"},
                 directory: {"bind": "/backup", "mode": "rw"}},
        remove=True,
        **kwargs
    )


def docker_volume_restore(client: ContainerClient, target_volume: str, source_file: str, **kwargs):
    """
    Restore a docker volume from a .tar.gz backup file on the docker host.

    :param client: docker client
    :param target_volume: volume to restore into (created if missing)
    :param source_file: absolute path of the backup file on the docker host
    :param kwargs: docker container run args
    """
    directory, filename = _split_backup_path(source_file)
    return client.containers.run(
        "alpine", ["tar", "xzf", f"/backup/{filename}", "--numeric-owner", "-C", "/data"],
        volumes={target_volume: {"bind": "/data", "mode": "rw"},
                 directory: {"bind": "/backup", "mode": "ro"}},
        remove=True,
        **kwargs
    )

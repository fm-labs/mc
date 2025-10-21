import os

import docker
import podman
from podman import PodmanClient

from mc.inventory.storage import get_inventory_storage_instance


# def enumerate_container_hosts_from_env() -> list[str]:
#     """
#     Enumerate Docker hosts from environment variables.
#
#     DOCKER_HOST: primary Docker host (default: unix:///var/run/docker.sock)
#     DOCKER_HOST_1, DOCKER_HOST_2, ... : additional Docker hosts
#     The index for DOCKER_HOST_n starts from 1 and increments until no more variables are found.
#     Returns a list of Docker host URLs.
#     """
#     hosts = [os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")]
#
#     i = 1
#     while True:
#         env_var = f"DOCKER_HOST_{i}"
#         host = os.getenv(env_var)
#         if not host:
#             break
#
#         hosts.append(host)
#         i += 1
#     return hosts



DOCKER_HOSTS = []

#CONTAINER_HOSTS = []  #{"engine": "docker", "url": "unix:///var/run/docker.sock"}

# Initialize Docker hosts from inventory
def init_container_hosts(refresh: bool = False):
    global DOCKER_HOSTS
    if (DOCKER_HOSTS) and not refresh:
        return

    DOCKER_HOSTS = []
    inventory = get_inventory_storage_instance()
    items = inventory.list_items("container_host")
    for item in items:
        url = item.get("properties", {}).get("url")
        engine = item.get("properties", {}).get("engine", "docker").lower()
        if engine == "docker" and url not in DOCKER_HOSTS:
            DOCKER_HOSTS.append(url)
        else:
            print(f"Unknown container engine '{engine}' for host '{url}'")
    #print("Configured container hosts:", DOCKER_HOSTS, PODMAN_HOSTS)


def _get_docker_client(idx: int = 0) -> docker.DockerClient:
    global DOCKER_HOSTS
    base_url = DOCKER_HOSTS[idx] if idx < len(DOCKER_HOSTS) else None
    if not base_url:
        raise ValueError(f"No Docker host configured for index {idx}")

    use_ssl_client = base_url.startswith("ssh://")
    return docker.DockerClient(base_url=base_url, use_ssh_client=use_ssl_client, timeout=15)

def get_docker_client(idx: int = 0) -> docker.DockerClient:
    return _get_docker_client(idx)


def get_podman_client(idx: int = 0) -> podman.PodmanClient:
    global DOCKER_HOSTS
    base_url = DOCKER_HOSTS[idx] if idx < len(DOCKER_HOSTS) else None
    if not base_url:
        raise ValueError(f"No Docker host configured for index {idx}")

    use_ssl_client = base_url.startswith("ssh://")
    return PodmanClient(base_url=base_url, use_ssh_client=use_ssl_client, timeout=15)


#init_container_hosts()


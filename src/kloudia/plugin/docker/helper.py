import os

import docker


def enumerate_docker_hosts_from_env() -> list[str]:
    """
    Enumerate Docker hosts from environment variables.

    DOCKER_HOST: primary Docker host (default: unix:///var/run/docker.sock)
    DOCKER_HOST_1, DOCKER_HOST_2, ... : additional Docker hosts
    The index for DOCKER_HOST_n starts from 1 and increments until no more variables are found.
    Returns a list of Docker host URLs.
    """
    hosts = [os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")]

    i = 1
    while True:
        env_var = f"DOCKER_HOST_{i}"
        host = os.getenv(env_var)
        if not host:
            break

        hosts.append(host)
        i += 1
    return hosts



DOCKER_HOSTS = enumerate_docker_hosts_from_env()

def get_docker_client(idx: int = 0) -> docker.DockerClient:
    base_url = DOCKER_HOSTS[idx] if idx < len(DOCKER_HOSTS) else None
    if not base_url:
        raise ValueError(f"No Docker host configured for index {idx}")

    print("DOCKER_HOST", idx, base_url)
    use_ssl_client = base_url.startswith("ssh://")
    return docker.DockerClient(base_url=base_url, use_ssh_client=use_ssl_client)

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Iterable
from typing import Any

from docker import DockerClient
from podman import PodmanClient

from mc import config
from mc.plugin.containers.node_client import NodeConfig, NodeContainerClient, load_node_configs

ContainerClient = PodmanClient | DockerClient | NodeContainerClient

logger = logging.getLogger(__name__)


class ContainerClientsManager:
    def __init__(self) -> None:
        self._clients: dict[str, ContainerClient] = {}
        self._urls: dict[str, str] = {}
        self._lock = threading.Lock()
        # all configured nodes, including the ones that aren't connected
        self.nodes: dict[str, NodeConfig] = {}

    def get(self, name: str) -> ContainerClient | None:
        return self._clients.get(name)

    def names(self) -> Iterable[str]:
        return tuple(self._clients.keys())

    def urls(self) -> dict[str, str]:
        """
        Return a dict of client names and their base URLs.
        """
        return self._urls

    def add(self, name: str, base_url: str, test_ping: bool = False) -> ContainerClient | None:
        """
        Create and register a client from a URL like "docker+unix:///var/run/docker.sock", "podman+ssh://..."
        or "node+http://host:3080" (no engine means docker). Nodes added this way have no API key, use add_node().
        """
        # split base_url into engine and url
        if "+" in base_url:
            engine, url = base_url.split("+", 1)
        else:
            engine, url = "docker", base_url  # default to docker if no engine specified

        try:
            if engine == "docker":
                use_ssh = url.startswith("ssh")
                c = DockerClient(base_url=url, timeout=15, use_ssh_client=use_ssh)
            elif engine == "podman":
                c = PodmanClient(base_url=url, timeout=10)
            elif engine == "node":
                c = NodeContainerClient(base_url=url)
            else:
                raise ValueError(f"Unknown container engine '{engine}' in URL '{base_url}'")
        except Exception as e:
            logger.error(f"Failed to create container client for '{name}' with URL '{base_url}': {e}")
            return None

        return self.register(name, c, base_url, test_ping=test_ping)

    def add_node(self, node: NodeConfig, test_ping: bool = False) -> ContainerClient | None:
        """Register a client for another mc instance."""
        return self.register(node.name, NodeContainerClient.from_config(node), f"node+{node.base_url}", test_ping)

    def register(self, name: str, client: ContainerClient, url: str, test_ping: bool = False) -> ContainerClient:
        """
        Register a client. If the ping test fails, the client is registered anyway (the host may come up later).
        """
        if test_ping:
            try:
                client.ping()
            except Exception as e:
                logger.warning(f"Failed to ping container client '{name}' at '{url}': {e}")

        with self._lock:
            if name in self._clients:
                client.close()
                raise ValueError(f"Client '{name}' already exists")
            self._clients[name] = client
            self._urls[name] = url

        logger.info(f"Added container client '{name}' with URL '{url}'")
        return client

    def ensure(self, name: str, base_url: str, test_ping: bool = True):
        existing = self.get(name)
        if existing:
            return existing
        return self.add(name, base_url, test_ping)

    def remove(self, name: str, close: bool = True) -> bool:
        with self._lock:
            c = self._clients.pop(name, None)
            if not c:
                return False
            if close:
                try:
                    c.close()
                except Exception:
                    pass
            self._urls.pop(name, None)
            return True

    def close_all(self) -> None:
        with self._lock:
            for c in list(self._clients.values()):
                try:
                    c.close()
                except Exception:
                    pass
            self._clients.clear()
            self._urls.clear()


# @lru_cache(maxsize=1)
# def init_container_connection_manager() -> ContainerClientsManager:
#    return ContainerClientsManager()


def bootstrap_container_connection_manager(mc_config: dict[str, Any] | None = None) -> ContainerClientsManager:
    """
    Create the manager with the local docker connection and the nodes from the mc config.
    Nodes are not pinged here, so unreachable nodes don't slow down the startup.
    """
    m = ContainerClientsManager()
    m.ensure("localdocker", os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock"), test_ping=False)

    for node in load_node_configs(config.CONFIG if mc_config is None else mc_config):
        m.nodes[node.name] = node
        if not node.autoconnect:
            logger.info(f"Node '{node.name}' is not connected (autoconnect is false)")
            continue
        try:
            m.add_node(node)
        except ValueError as e:
            logger.error(f"Can't add node '{node.name}': {e}")

    # inventory = get_inventory_storage_instance()
    # items = inventory.list_items("container_host")
    # for item in items:
    #     url = item.get("url")
    #     engine = item.get("engine", "docker").lower()
    #     autoconnect = item.get("autoconnect", False)
    #     print("CCM: Found container host in inventory:", engine, url)
    #     if not autoconnect:
    #         print("CCM: Skipping container host (autoconnect is false):", url)
    #         continue
    #
    #     engine_url = engine + "+" + url
    #     try:
    #         if engine == "docker" or engine == "podman":
    #             m.ensure(item.get("name", url), engine_url, test_ping=False)
    #             print("CCM: Configured container host:", engine_url)
    #         else:
    #             print(f"CCM: Unknown container engine '{engine}' for host '{url}'")
    #     except Exception as e:
    #         print(f"CCM: Failed to configure container host '{url}': {e}")
    # m.ensure("local", "unix:///run/podman/podman.sock", test_ping=False)
    return m


# best-effort cleanup if the process exits without FastAPI shutdown
# atexit.register(lambda: asyncio.run(init_container_connection_manager().close_all()))

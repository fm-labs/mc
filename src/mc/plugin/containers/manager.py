from __future__ import annotations

import logging
import threading
from collections.abc import Iterable
from typing import Any

from docker import DockerClient
from podman import PodmanClient
from pydantic import BaseModel

from mc import config
from mc.plugin.containers.node_client import NodeConfig, NodeContainerClient, parse_node_configs

ContainerClient = PodmanClient | DockerClient | NodeContainerClient

logger = logging.getLogger(__name__)


class ContainerClientsManager:
    def __init__(self) -> None:
        self._clients: dict[str, ContainerClient] = {}
        self._urls: dict[str, str] = {}
        self._lock = threading.Lock()
        # one lock per client name, so parallel requests don't create the same client twice
        self._create_locks: dict[str, threading.Lock] = {}
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

    def add(self, name: str, base_url: str, test_ping: bool = False) -> ContainerClient:
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
            raise

        return self.register(name, c, base_url, test_ping=test_ping)

    def add_node(self, node: NodeConfig, test_ping: bool = False) -> ContainerClient:
        """Register a client for another mc instance."""
        url = node.url if node.url.startswith("node+") else f"node+{node.url}"
        return self.register(node.name, NodeContainerClient.from_config(node), url, test_ping)

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

    def _create_lock(self, name: str) -> threading.Lock:
        with self._lock:
            return self._create_locks.setdefault(name, threading.Lock())

    def ensure(self, name: str, base_url: str, test_ping: bool = False) -> ContainerClient:
        """Return the client named `name`, or create it from `base_url`. Safe to call from parallel requests."""
        existing = self.get(name)
        if existing:
            return existing
        with self._create_lock(name):
            existing = self.get(name)
            if existing:
                return existing
            return self.add(name, base_url, test_ping)

    def ensure_node(self, node: NodeConfig, test_ping: bool = False) -> ContainerClient:
        """Like ensure(), for a node."""
        existing = self.get(node.name)
        if existing:
            return existing
        with self._create_lock(node.name):
            existing = self.get(node.name)
            if existing:
                return existing
            self.nodes[node.name] = node
            return self.add_node(node, test_ping)

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
    Create the manager. With mc_config, the "docker_hosts" from it are registered right away;
    without it, the manager starts empty and clients are created on first use (see deps.dep_container_connection).
    Hosts are not pinged here, so unreachable hosts don't slow down the startup.
    """
    m = ContainerClientsManager()
    if mc_config is not None and isinstance(mc_config, dict):
        bootstrap_ccm_from_config(m, mc_config)

    return m


def bootstrap_ccm_from_config(ccm: ContainerClientsManager, mc_config: dict[str, Any]) -> None:
    docker_hosts = mc_config.get("docker_hosts", {})
    for k, v in docker_hosts.items():
        if ccm.get(k) is not None:
            logger.warning(f"Container client '{k}' already exists")
            continue
        if not isinstance(v, dict) or not v.get("url"):
            logger.warning(f"Container client '{k}' has no URL")
            continue
        if v.get("url").startswith("node"):
            continue
        try:
            ccm.ensure(k, v.get("url"), test_ping=False)
        except Exception as e:
            logger.error(f"Can't add container client '{k}': {e}")

    for node in parse_node_configs(mc_config):
        try:
            ccm.ensure_node(node)
        except Exception as e:
            logger.error(f"Can't add node '{node.name}': {e}")


# best-effort cleanup if the process exits without FastAPI shutdown
# atexit.register(lambda: asyncio.run(init_container_connection_manager().close_all()))



class ContainerHostProperties(BaseModel):
    engine: str
    url: str
    autoconnect: bool


class ContainerHost(BaseModel):
    id: str
    name: str
    connected: bool
    properties: ContainerHostProperties


CONTAINER_HOSTS: list[ContainerHost] | None = None

def enumerate_container_hosts():
    global CONTAINER_HOSTS
    if CONTAINER_HOSTS is None:
        CONTAINER_HOSTS = parse_docker_hosts_config(config.CONFIG)
    return CONTAINER_HOSTS


def parse_docker_hosts_config(mc_config: dict) -> list[ContainerHost]:
    """
    List the hosts from the "docker_hosts" config section, plus the localhost fallback.
    A host is "connected" if its client was created already (clients are created on first use, see deps.py).
    """
    docker_hosts = mc_config.get("docker_hosts") or {}
    if not isinstance(docker_hosts, dict):
        docker_hosts = {}

    #def is_connected(name: str) -> bool:
    #    return manager is not None and manager.get(name) is not None

    hosts: list[ContainerHost] = []

    # localhost fallback
    if "localhost" not in docker_hosts:
        hosts.append(
            ContainerHost(
                id="localhost",
                name="localhost",
                connected=True, # deprecated
                properties=ContainerHostProperties(
                    engine="docker", url="unix:///var/run/docker.sock", autoconnect=False
                ),
            )
        )

    for name, entry in docker_hosts.items():
        if not isinstance(entry, dict) or not entry.get("url"):
            logger.warning(f"Container host '{name}' has no URL, skipping")
            continue
        url = entry["url"]
        engine = "docker"
        if "+" in url:
            engine, url = url.split("+", 1)

        hosts.append(
            ContainerHost(
                id=name,
                name=name,
                connected=True, # deprecated
                properties=ContainerHostProperties(
                    engine=engine, url=url, autoconnect=bool(entry.get("autoconnect", False))
                ),
            )
        )

    return hosts

